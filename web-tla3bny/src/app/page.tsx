'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { tNews, tHomeAds, type TNews, type TAd } from '@/lib/tla3bnyApi';
import MatchesFeed from '@/components/tla3bny/MatchesFeed';
import NewsCard from '@/components/tla3bny/NewsCard';
import { useTT } from '@/components/tla3bny/kit';

export default function HomePage() {
  const tt = useTT();
  const [news, setNews] = useState<TNews[]>([]);
  const [ads, setAds] = useState<TAd[]>([]);
  useEffect(() => { tNews({ limit: 4 }).then(setNews).catch(() => setNews([])); }, []);
  useEffect(() => { tHomeAds().then(setAds).catch(() => setAds([])); }, []);

  return (
    <div className="space-y-6">
      {news.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-black text-text">{tt('آخر الأخبار', 'Latest News')}</h2>
            <Link href="/news" className="text-xs font-bold text-aqua hover:underline">{tt('الكل', 'All')}</Link>
          </div>
          <div className="space-y-3">
            {news.map(n => {
              // Open the item on its competition's News tab (deep-linked), so the
              // article — and its shareable URL — lives on the competition page.
              // Site-wide items (no competition) open on the standalone News page.
              const href = n.competition_id
                ? `/competition/?id=${n.competition_id}&tab=news&news=${n.id}`
                : `/news/?news=${n.id}`;
              return (
                <Link key={n.id} href={href} className="block active:opacity-80">
                  <NewsCard item={n} />
                </Link>
              );
            })}
          </div>
        </section>
      )}

      <section>
        <h2 className="text-lg font-black text-text mb-2">{tt('المباريات', 'Matches')}</h2>
        <MatchesFeed ads={ads} />
      </section>
    </div>
  );
}
