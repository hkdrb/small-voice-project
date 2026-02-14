'use client';

import { useEffect } from 'react';

/**
 * BFcache (Back-Forward Cache) 対策のためのコンポーネント。
 * ブラウザの「戻る」「進む」でキャッシュからページが復元された際、
 * 強制的にリロードして認証状態（Middleware）を再評価させます。
 */
export default function NavigationGuard() {
  useEffect(() => {
    const handlePageShow = (event: PageTransitionEvent) => {
      if (event.persisted) {
        // キャッシュから復元された場合、リロードして最新の状態を確認する
        window.location.reload();
      }
    };

    window.addEventListener('pageshow', handlePageShow);

    return () => {
      window.removeEventListener('pageshow', handlePageShow);
    };
  }, []);

  return null;
}
