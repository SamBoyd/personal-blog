import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';

export default function Home(): ReactNode {
  return (
    <Layout title="Personal Blog" description="Repo-first content workflow with Docusaurus.">
      <main className="container margin-vert--xl">
        <h1>Personal Blog</h1>
        <p>A minimal static blog powered by Docusaurus and synced from canonical markdown content.</p>
        <p>
          <Link className="button button--primary" to="/blog">
            Read the blog
          </Link>
        </p>
      </main>
    </Layout>
  );
}
