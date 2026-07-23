'use client';
import { useEffect, useState } from 'react';
import { tCategories, tAnalysis, type TCategory, type TAnalysis } from '@/lib/tla3bnyApi';
import Spinner from '@/components/ui/Spinner';
import CategoryTabs from '@/components/tla3bny/CategoryTabs';
import { EmptyState, LogoAvatar, useTT } from '@/components/tla3bny/kit';

type Board = 'top_scorers' | 'top_assisters' | 'clean_sheets' | 'yellow_cards' | 'red_cards';

export default function StatsPage() {
  const tt = useTT();
  const [cats, setCats] = useState<TCategory[]>([]);
  const [cat, setCat] = useState<number | null>(null);
  const [data, setData] = useState<TAnalysis | null>(null);
  const [board, setBoard] = useState<Board>('top_scorers');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    tCategories().then(cs => { setCats(cs); if (cs.length) setCat(cs[0].id); }).catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (cat == null) return;
    setLoading(true);
    tAnalysis(cat).then(setData).catch(() => setData(null)).finally(() => setLoading(false));
  }, [cat]);

  const boards: { k: Board; label: string; unit: string }[] = [
    { k: 'top_scorers', label: tt('الهدافون', 'Scorers'), unit: tt('هدف', 'goals') },
    { k: 'top_assisters', label: tt('صناع الأهداف', 'Assists'), unit: tt('صناعة', 'assists') },
    { k: 'clean_sheets', label: tt('شباك نظيفة', 'Clean sheets'), unit: tt('مباراة', 'CS') },
    { k: 'yellow_cards', label: tt('صفراء', 'Yellow'), unit: tt('بطاقة', 'YC') },
    { k: 'red_cards', label: tt('حمراء', 'Red'), unit: tt('بطاقة', 'RC') },
  ];
  const active = boards.find(b => b.k === board)!;
  const rows = data?.[board] ?? [];
  const isTeamBoard = board === 'clean_sheets';

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-black text-text">{tt('الإحصائيات', 'Stats')}</h1>
      <CategoryTabs categories={cats} selected={cat} onSelect={setCat} />

      <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
        {boards.map(b => (
          <button key={b.k} onClick={() => setBoard(b.k)}
            className={`text-xs font-bold px-3 py-1.5 rounded-lg whitespace-nowrap transition-colors ${
              board === b.k ? 'bg-aqua/15 text-aqua border border-aqua/40' : 'text-hint hover:text-teal border border-transparent'
            }`}>
            {b.label}
          </button>
        ))}
      </div>

      {loading ? <Spinner /> :
        rows.length === 0 ? <EmptyState icon="🏆" text={tt('لا توجد بيانات بعد', 'No data yet')} /> :
        <div className="space-y-2">
          {rows.map((r, i) => {
            const name = isTeamBoard ? (r as { academy_name: string }).academy_name : (r as { player_name: string }).player_name;
            const sub = (r as { academy_name?: string }).academy_name;
            const photo = isTeamBoard ? (r as { logo_path?: string }).logo_path : (r as { photo_path?: string }).photo_path;
            return (
              <div key={i} className="flex items-center gap-3 bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-xl px-3 py-2.5">
                <span className={`w-6 text-center font-black tnum ${i < 3 ? 'text-gold' : 'text-hint'}`}>{i + 1}</span>
                <LogoAvatar src={photo} name={name} size={34} />
                <div className="min-w-0 flex-1">
                  <div className="font-bold text-text text-sm truncate">{name}</div>
                  {!isTeamBoard && sub && <div className="text-[11px] text-hint truncate">{sub}</div>}
                </div>
                <div className="text-end shrink-0">
                  <span className="font-black text-lg text-aqua tnum">{r.count}</span>
                  <span className="text-[11px] text-hint block">{active.unit}</span>
                </div>
              </div>
            );
          })}
        </div>}
    </div>
  );
}
