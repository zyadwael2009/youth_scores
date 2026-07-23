'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { tCategories, tMatches, type TCategory, type TMatch } from '@/lib/tla3bnyApi';
import Spinner from '@/components/ui/Spinner';
import CategoryTabs from '@/components/tla3bny/CategoryTabs';
import MatchRow from '@/components/tla3bny/MatchRow';
import { EmptyState, useTT } from '@/components/tla3bny/kit';

type Filter = 'all' | 'scheduled' | 'finished';

export default function Tla3bnyHome() {
  const tt = useTT();
  const [cats, setCats] = useState<TCategory[]>([]);
  const [cat, setCat] = useState<number | null>(null);
  const [filter, setFilter] = useState<Filter>('all');
  const [matches, setMatches] = useState<TMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    tCategories().then(setCats).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true); setErr(null);
    tMatches({
      age_category_id: cat ?? undefined,
      status: filter === 'all' ? undefined : filter,
    })
      .then(setMatches)
      .catch(e => setErr(String(e)))
      .finally(() => setLoading(false));
  }, [cat, filter]);

  const filters: { k: Filter; label: string }[] = [
    { k: 'all', label: tt('الكل', 'All') },
    { k: 'scheduled', label: tt('قادمة', 'Upcoming') },
    { k: 'finished', label: tt('انتهت', 'Finished') },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <h1 className="text-2xl font-black text-text">{tt('دوري تلاعبني', 'Tla3bny League')}</h1>
        <Link href="/register"
          className="text-xs font-bold text-aqua hover:underline shrink-0">
          {tt('سجّل أكاديميتك', 'Register academy')} →
        </Link>
      </div>

      <CategoryTabs categories={cats} selected={cat} onSelect={setCat} allowAll allLabel={tt('كل الفئات', 'All ages')} />

      <div className="flex items-center gap-2">
        {filters.map(f => (
          <button key={f.k} onClick={() => setFilter(f.k)}
            className={`text-xs font-bold px-3 py-1.5 rounded-lg transition-colors ${
              filter === f.k ? 'bg-cardBg2 text-aqua border border-aqua/40' : 'text-hint hover:text-teal'
            }`}>
            {f.label}
          </button>
        ))}
      </div>

      {loading ? <Spinner /> :
        err ? <EmptyState icon="⚠️" text={err} /> :
        matches.length === 0 ? <EmptyState text={tt('لا توجد مباريات', 'No matches yet')} /> :
        <div className="space-y-2.5">{matches.map(m => <MatchRow key={m.id} m={m} />)}</div>}
    </div>
  );
}
