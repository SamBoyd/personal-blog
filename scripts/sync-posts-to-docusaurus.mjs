import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, '..');
const postsRoot = path.join(repoRoot, 'content', 'posts');
const outputBlogDir = path.join(repoRoot, 'static-site', 'blog');
const outputStaticPostsDir = path.join(repoRoot, 'static-site', 'static', 'posts');

function isValidDate(dateString) {
  return /^\d{4}-\d{2}-\d{2}$/.test(dateString);
}

function toYamlValue(value) {
  if (Array.isArray(value)) {
    return `[${value.map((item) => `"${String(item).replace(/"/g, '\\"')}"`).join(', ')}]`;
  }

  if (typeof value === 'string') {
    return `"${value.replace(/"/g, '\\"')}"`;
  }

  return String(value);
}

async function ensureDir(dir) {
  await fs.mkdir(dir, {recursive: true});
}

async function cleanDirectory(dir) {
  await fs.rm(dir, {recursive: true, force: true});
  await ensureDir(dir);
}

async function copyDirectory(sourceDir, targetDir) {
  const entries = await fs.readdir(sourceDir, {withFileTypes: true});
  await ensureDir(targetDir);

  for (const entry of entries) {
    const sourcePath = path.join(sourceDir, entry.name);
    const targetPath = path.join(targetDir, entry.name);

    if (entry.isDirectory()) {
      await copyDirectory(sourcePath, targetPath);
      continue;
    }

    await fs.copyFile(sourcePath, targetPath);
  }
}

function buildFrontmatter(meta) {
  const frontmatter = {
    title: meta.title,
    slug: meta.slug,
    date: meta.date,
    tags: meta.tags,
  };

  const lines = ['---'];
  for (const [key, value] of Object.entries(frontmatter)) {
    lines.push(`${key}: ${toYamlValue(value)}`);
  }
  lines.push('---', '');

  return lines.join('\n');
}

function rewriteAssetPaths(markdown, slug) {
  return markdown.replace(/\.\/assets\/(\S+)/g, (_match, fileName) => `/posts/${slug}/${fileName}`);
}

async function readPublishedPosts() {
  let postDirs = [];
  try {
    const entries = await fs.readdir(postsRoot, {withFileTypes: true});
    postDirs = entries.filter((entry) => entry.isDirectory()).map((entry) => entry.name);
  } catch (error) {
    if (error && error.code === 'ENOENT') {
      return [];
    }
    throw error;
  }

  const posts = [];

  for (const postDirName of postDirs) {
    const canonicalDir = path.join(postsRoot, postDirName);
    const metaPath = path.join(canonicalDir, 'meta.json');
    const readmePath = path.join(canonicalDir, 'README.md');
    const assetsDir = path.join(canonicalDir, 'assets');

    const metaRaw = await fs.readFile(metaPath, 'utf8');
    const meta = JSON.parse(metaRaw);

    if (meta.status !== 'published') {
      continue;
    }

    if (!meta.title || !meta.slug || !meta.date || !Array.isArray(meta.tags)) {
      throw new Error(`Invalid meta.json in ${canonicalDir}: expected title, slug, date, tags`);
    }

    if (!isValidDate(meta.date)) {
      throw new Error(`Invalid date format in ${metaPath}. Expected YYYY-MM-DD.`);
    }

    const readme = await fs.readFile(readmePath, 'utf8');

    posts.push({
      assetsDir,
      meta,
      readme,
    });
  }

  return posts;
}

async function sync() {
  await cleanDirectory(outputBlogDir);
  await ensureDir(outputStaticPostsDir);

  const posts = await readPublishedPosts();

  for (const post of posts) {
    const {meta, readme, assetsDir} = post;
    const filename = `${meta.date}-${meta.slug}.md`;
    const frontmatter = buildFrontmatter(meta);
    const rewritten = rewriteAssetPaths(readme, meta.slug);

    const blogOutputPath = path.join(outputBlogDir, filename);
    await fs.writeFile(blogOutputPath, `${frontmatter}${rewritten}\n`, 'utf8');

    const staticTargetDir = path.join(outputStaticPostsDir, meta.slug);
    await cleanDirectory(staticTargetDir);
    await copyDirectory(assetsDir, staticTargetDir);
  }

  console.log(`Synced ${posts.length} published post(s) to static-site/blog and static-site/static/posts.`);
}

sync().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
