import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const mixpanelToken = process.env.MIXPANEL_TOKEN;

const config: Config = {
  title: 'Personal Blog',
  tagline: 'A minimal Docusaurus blog with repo-first content.',
  favicon: 'img/favicon.ico',
  future: {
    v4: true,
  },
  url: 'http://localhost',
  baseUrl: '/',
  onBrokenLinks: 'throw',
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },
  presets: [
    [
      'classic',
      {
        docs: false,
        blog: {
          path: 'blog',
          routeBasePath: 'blog',
          showReadingTime: true,
          onInlineTags: 'warn',
          onInlineAuthors: 'ignore',
          onUntruncatedBlogPosts: 'ignore',
        },
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],
  headTags: mixpanelToken
    ? [
        {
          tagName: 'script',
          attributes: {
            src: 'https://cdn.mxpnl.com/libs/mixpanel-2-latest.min.js',
            async: 'true',
          },
        },
        {
          tagName: 'script',
          innerHTML: `
            (function () {
              var token = ${JSON.stringify(mixpanelToken)};
              if (!token) return;
              function getTracker() {
                return window.mixpanel && typeof window.mixpanel.track === 'function'
                  ? window.mixpanel
                  : null;
              }
              function trackPageView(pathname, title) {
                var tracker = getTracker();
                if (!tracker) return;
                tracker.track('Page Viewed', { path: pathname, title: title || document.title });
              }
              window.__trackPageView = trackPageView;
              function init() {
                if (!window.mixpanel || typeof window.mixpanel.init !== 'function') return;
                window.mixpanel.init(token, { track_pageview: false });
                trackPageView(window.location.pathname, document.title);
              }
              if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', init, { once: true });
              } else {
                init();
              }
            })();
          `,
        },
      ]
    : [],
  themeConfig: {
    image: 'img/docusaurus-social-card.jpg',
    navbar: {
      title: 'Personal Blog',
      items: [{to: '/blog', label: 'Blog', position: 'left'}],
    },
    footer: {
      style: 'light',
      links: [],
      copyright: `Copyright © ${new Date().getFullYear()} Personal Blog`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
