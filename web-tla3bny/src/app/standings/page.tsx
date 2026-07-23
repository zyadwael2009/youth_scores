'use client';
import { useEffect, useState } from 'react';
import { tCategories, tStandings, type TCategory, type TStandingRow } from '@/lib/tla3bnyApi';
import Spinner from '@/components/ui/Spinner';
import CategoryTabs from '@/components/tla3bny/CategoryTabs';
import { EmptyState, LogoAvatar, useTT } from '@/components/tla3bny/kit';

function FormDots({ form }: { form: ('W' | 'D' | 'L')[] }) {
  const color = { W: 'bg-win', D: 'bg-hint', L: 'bg-loss' };
  return (
    <div className="flex gap-0.5 justify-center">
      {form.map((f, i) => <span key={i} className={`w-1.5 h-1.5 rounded-full ${color[f]}`} />)}
    </div>
  );
}

export default function StandingsPage() {
  const tt = useTT();
  const [cats, setCats] = useState<TCategory[]>([]);
  const [cat, setCat] = useState<number | null>(null);
  const [rows, setRows] = useState<TStandingRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    tCategories().then(cs => { setCats(cs); if (cs.length) setCat(cs[0].id); }).catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (cat == null) return;
    setLoading(true);
    tStandings(cat).then(setRows).catch(() => setRows([])).finally(() => setLoading(false));
  }, [cat]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-black text-text">{tt('الترتيب', 'Standings')}</h1>
      <CategoryTabs categories={cats} selected={cat} onSelect={setCat} />

      {loading ? <Spinner /> :
        rows.length === 0 ? <EmptyState icon="📊" text={tt('لا يوجد ترتيب بعد', 'No standings yet')} /> :
        <div className="bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-hint text-[11px] border-b border-bdr">
                  <th className="text-start font-bold px-3 py-2.5">#</th>
                  <th className="text-start font-bold px-2 py-2.5">{tt('الفريق', 'Team')}</th>
                  <th className="font-bold px-1.5 py-2.5 tnum">{tt('لعب', 'P')}</th>
                  <th className="font-bold px-1.5 py-2.5 tnum">{tt('ف', 'W')}</th>
                  <th className="font-bold px-1.5 py-2.5 tnum">{tt('ت', 'D')}</th>
                  <th className="font-bold px-1.5 py-2.5 tnum">{tt('خ', 'L')}</th>
                  <th className="font-bold px-1.5 py-2.5 tnum hidden sm:table-cell">{tt('+/-', 'GD')}</th>
                  <th className="font-bold px-2 py-2.5">{tt('آخر ٥', 'Form')}</th>
                  <th className="font-black px-3 py-2.5 tnum text-aqua">{tt('نقاط', 'Pts')}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(r => (
                  <tr key={r.academy_id} className="border-b border-bdr/50 last:border-0">
                    <td className="px-3 py-2.5 text-hint font-bold tnum">{r.rank}</td>
                    <td className="px-2 py-2.5">
                      <div className="flex items-center gap-2 min-w-0">
                        <LogoAvatar src={r.logo_path} name={r.academy_name} size={26} />
                        <span className="font-bold text-text truncate">{r.academy_name}</span>
                      </div>
                    </td>
                    <td className="text-center px-1.5 tnum text-teal">{r.P}</td>
                    <td className="text-center px-1.5 tnum text-teal">{r.W}</td>
                    <td className="text-center px-1.5 tnum text-teal">{r.D}</td>
                    <td className="text-center px-1.5 tnum text-teal">{r.L}</td>
                    <td className="text-center px-1.5 tnum text-teal hidden sm:table-cell">{r.GD > 0 ? `+${r.GD}` : r.GD}</td>
                    <td className="px-2"><FormDots form={r.form} /></td>
                    <td className="text-center px-3 font-black tnum text-text">{r.Pts}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>}
    </div>
  );
}
