# Project Overview

This repository contains a static blog site and a growing collection of posts exploring **product tooling and workflows for solo engineers and very small teams**, particularly those building with **AI-driven development practices**.

The primary purpose of this project is **exploration**.

Rather than promoting a single, fully-formed product or framework, this blog is designed to generate and publish **many small, concrete tools, workflows, automations, and mental models** that touch different parts of the product development process. Each post is intentionally narrow in scope: a single mechanism, input, feedback loop, or lightweight system that a solo engineer could realistically try.

These tools are not primarily about *decision-making frameworks*. They are about:

- collecting and structuring product inputs
- surfacing signal from noise
- maintaining context over time
- supporting learning velocity
- reducing cognitive overhead for solo builders

A key goal of the blog is to **observe interest and resonance**:

- Which problem areas do readers care about most?
- Which tools feel immediately useful vs. theoretical?
- Where do solo engineers struggle as their ability to ship code accelerates?
- What kinds of “product management” support actually fit solo workflows?

In that sense, this blog is as much **market exploration and sense-making** as it is content delivery. Posts are expected to vary in depth, polish, and ambition. Some ideas will intentionally be speculative or incomplete. That is a feature, not a bug.

The audience is assumed to be:

- technically fluent
- biased toward shipping
- skeptical of heavyweight process
- comfortable experimenting with imperfect tools
- increasingly reliant on LLMs, agents, and automation

This repository should therefore favor:

- concrete examples over abstractions
- minimal surface area over platforms
- artifacts that are readable by both humans and AI agents
- fast iteration over premature coherence

Technical documentation, build details, and site mechanics are secondary. The core artifact is the **ideas expressed through posts**, and the learning that emerges from publishing many of them and watching what sticks.

# Repository Structure

- `content/posts/<YYYY-MM-DD-slug>/README.md`: canonical post source.
- `content/posts/<YYYY-MM-DD-slug>/meta.json`: post metadata (`title`, `slug`, `date`, `tags`, `status`).
- `content/posts/<YYYY-MM-DD-slug>/assets/`: per-post media.
- `scripts/sync-posts-to-docusaurus.mjs`: syncs canonical posts into Docusaurus.
- `static-site/`: Cloudflare Pages-ready Docusaurus app.
- `static-site/blog/`: generated blog markdown (do not hand-edit).
- `static-site/static/posts/<slug>/`: generated copied assets (do not hand-edit).

# Build And Test Commands

Run all commands from repo root unless noted.

- `npm run sync`: generate `static-site/blog/*` and `static-site/static/posts/*` from `content/posts/*`.
- `npm run dev`: sync content, then run Docusaurus dev server on port `4173`.
- `npm run build`: sync content, then build production static files.
- `npm run serve`: serve prebuilt Docusaurus output.
- `npm --prefix ./static-site run deploy`: deploy `static-site/build` to Cloudflare Pages via Wrangler.
- `npm --prefix ./static-site run preview`: build and preview Cloudflare Pages locally.

# Code Style Guidelines

- Use TypeScript for Docusaurus custom app code (`static-site/src/**`) when practical.
- Keep implementation minimal and deterministic; avoid unnecessary abstractions.
- Preserve the repo-first workflow: source-of-truth content belongs in `content/posts`, not `static-site/blog`.
- Keep frontmatter fields consistent with `meta.json`.
- Use clear, stable slugs; assets should be referenced in canonical markdown as `./assets/<file>`.
- Do not manually edit generated files in `static-site/blog` or `static-site/static/posts`.

# Testing Instructions

- There is no dedicated unit test suite currently.
- Required validation for content or site changes:
  - Run `npm run sync`.
  - Run `npm run build`.
  - Confirm generated post markdown exists in `static-site/blog/`.
  - Confirm generated assets exist in `static-site/static/posts/<slug>/`.
- When modifying routing, config, or analytics behavior, also run `npm run dev` and verify primary pages load (`/` and `/blog`).

# Security Considerations

- Mixpanel is optional and controlled by `MIXPANEL_TOKEN`.
- Never hardcode or commit analytics tokens or other secrets.
- Ensure behavior remains non-breaking when `MIXPANEL_TOKEN` is unset.
- Treat `content/posts/*` as trusted repository content; do not introduce runtime remote content fetching.
- Before deploying, verify no secrets are present in tracked files.

# Summary additions

After completing a major code change, include a suggested git commit message at the end of your response.

Use Conventional Commits v1.0.0 structure:

`<type>[optional scope][!]: <description>`

`[optional body]`

`[optional footer(s)]`

Follow these rules:

- Use a valid type. Prefer: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `build`, `perf`, `revert`.
- Add an optional scope when helpful (for example `sync`, `blog`, `mixpanel`, `content`, `docusaurus`).
- Keep the description short, specific, and actionable.
- Add a body when context is useful; separate it from the header with one blank line.
- IMPORTANT: Explain intent and impact in the body (why this change was needed, what behavior changed). 
- Use footers for metadata like issue refs (`Refs: #123`) or review trailers (`Reviewed-by: name`).
- Mark breaking changes with `!` in the header and/or a `BREAKING CHANGE: <description>` footer.
- Keep formatting machine-parseable and consistent so release tooling can use commit history.

Format the suggestion as:

**Suggested commit message:**
```text
<type>(<scope>): <short description>

<optional body explaining intent and impact>

<optional footer(s)>
```
