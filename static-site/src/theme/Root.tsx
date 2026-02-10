import type {PropsWithChildren} from 'react';
import {useEffect, useRef} from 'react';
import {useLocation} from '@docusaurus/router';

declare global {
  interface Window {
    __trackPageView?: (path: string, title: string) => void;
  }
}

export default function Root({children}: PropsWithChildren): JSX.Element {
  const location = useLocation();
  const lastPathRef = useRef<string | null>(null);

  useEffect(() => {
    const path = location.pathname;
    if (lastPathRef.current === path) {
      return;
    }

    lastPathRef.current = path;
    window.__trackPageView?.(path, document.title);
  }, [location.pathname]);

  return <>{children}</>;
}
