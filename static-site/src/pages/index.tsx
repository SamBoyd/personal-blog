import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import styles from './index.module.css';

export default function Home(): ReactNode {
  return (
    <Layout title="Home" description="Practical tools and workflows for solo engineers building with AI.">
      <main className={styles.hero}>
        <div className="container">
          <h1 className={styles.headline}>
            Building solo doesn't mean building without a system.
          </h1>
          <p className={styles.subtitle}>
            I write about lightweight product tools, feedback loops, and workflows
            for engineers who ship fast and figure out the rest as they go.
          </p>
          <div className={styles.actions}>
            <Link className="button button--primary button--lg" to="/blog">
              Read the blog
            </Link>
          </div>
        </div>
      </main>
    </Layout>
  );
}
