'use client';
import { Suspense } from 'react';
import NewsList from '@/components/tla3bny/NewsList';
import Spinner from '@/components/ui/Spinner';
import { useTT } from '@/components/tla3bny/kit';

export default function NewsPage() {
  const tt = useTT();
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-black text-text">{tt('الأخبار', 'News')}</h1>
      <Suspense fallback={<Spinner />}>
        <NewsList search />
      </Suspense>
    </div>
  );
}
