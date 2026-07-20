'use client';
import { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useApp } from '@/context/AppContext';
import { fetchCoach } from '@/lib/api';
import { localize } from '@/lib/utils';
import type { CoachFull } from '@/lib/types';

export default function CoachPage() {
  return (
    <Suspense fallback={<div className="min-h-[70vh] grid place-items-center"><div className="w-7 h-7 border-2 border-bdr border-t-aqua rounded-full animate-spin" /></div>}>
      <CoachProfile />
    </Suspense>
  );
}

function CoachProfile() {
  const params = useSearchParams();
  const id = params.get('id') ?? '';
  const { locale } = useApp();
  const router = useRouter();
  const [c, setC] = useState<CoachFull | null>(null);
  const [loading, setLoading] = useState(true);
  const isAr = locale === 'ar';

  useEffect(() => {
    if (!id) { setLoading(false); return; }
    setLoading(true);
    fetchCoach(id).then(setC).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="min-h-[70vh] grid place-items-center"><div className="w-7 h-7 border-2 border-bdr border-t-aqua rounded-full animate-spin" /></div>;
  if (!c) return <div className="p-8 text-center text-hint">{isAr ? 'غير موجود' : 'Not found'}</div>;

  const name = localize(c.name, locale);
  const monogram = name.split(/\s+/).map(w => w[0]).slice(0, 2).join('');
  const coachYears = c.career.filter(x => x.type === 'coach').length;
  const mgrYears = c.career.filter(x => x.type === 'manager').length;

  return (
    <div className="min-h-screen bg-darkBg pb-24">
      <div className="sticky top-0 z-30 bg-cardBg/90 backdrop-blur border-b border-bdr flex items-center gap-3 px-4 py-3">
        <button onClick={() => router.back()} className="text-aqua text-xl font-bold">‹</button>
        <span className="flex-1 text-aqua font-bold text-sm truncate">{name}</span>
      </div>

      {/* Hero */}
      <div className="relative overflow-hidden bg-gradient-to-b from-cardBg to-cardBg2 border-b border-bdr p-5">
        <div className="absolute -left-10 -top-10 w-44 h-44 rounded-full bg-[radial-gradient(circle,rgb(var(--accent-rgb)/0.16),transparent_65%)]" />
        <div className="relative flex items-center gap-4">
          {c.photo
            ? <img src={c.photo} alt={name} className="w-20 h-20 rounded-2xl object-cover" />
            : <div className="w-20 h-20 rounded-2xl grid place-items-center text-2xl font-black text-on-accent bg-gradient-to-br from-aqua to-aqua/70 shadow-[0_10px_26px_-8px_rgb(var(--accent-rgb))]">{monogram}</div>}
          <div>
            <h1 className="text-xl font-extrabold">{name}</h1>
            <div className="flex flex-wrap gap-1.5 mt-2">
              {c.birth_year && <span className="text-[11px] text-teal bg-cardBg2 border border-bdr rounded-full px-2.5 py-0.5 tnum">{isAr ? 'مواليد' : 'Born'} {c.birth_year}</span>}
              {localize(c.nationality, locale) && <span className="text-[11px] text-teal bg-cardBg2 border border-bdr rounded-full px-2.5 py-0.5">{localize(c.nationality, locale)}</span>}
            </div>
          </div>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-3 p-4">
        {[
          { v: coachYears, l: isAr ? 'مهام تدريبية' : 'Coaching roles', c: 'text-aqua' },
          { v: mgrYears, l: isAr ? 'مهام إدارية' : 'Management roles', c: 'text-gold' },
        ].map(k => (
          <div key={k.l} className="bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-2xl p-4 text-center">
            <p className={`font-extrabold text-2xl tnum ${k.c}`}>{k.v}</p>
            <p className="text-hint text-[11px] mt-0.5">{k.l}</p>
          </div>
        ))}
      </div>

      {/* Career */}
      <div className="px-4">
        <h2 className="text-text font-bold text-sm mb-3">{isAr ? 'المسيرة' : 'Career'}</h2>
        {c.career.length === 0 ? (
          <p className="text-hint text-sm text-center py-4">{isAr ? 'لا توجد بيانات مسيرة' : 'No career data'}</p>
        ) : (
          <div className="relative pr-4">
            <div className="absolute top-3 bottom-3 right-[13px] w-0.5 bg-gradient-to-b from-aqua to-bdr" />
            {c.career.map((r, i) => (
              <div key={i} className="grid grid-cols-[28px_1fr] gap-3 pb-3">
                <div className="relative z-10">
                  {r.logo ? <img src={r.logo} alt="" className="w-7 h-7 object-contain rounded" /> : <div className="w-7 h-7 rounded bg-bdr grid place-items-center text-xs">🛡️</div>}
                </div>
                <div className={`border rounded-xl p-3 ${r.current ? 'border-gold/35 bg-gold/[0.04]' : 'border-bdr bg-cardBg'}`}>
                  <div className="flex items-center gap-2">
                    <p className="text-text text-sm font-bold truncate flex-1">{r.club}</p>
                    <span className={`text-[9px] font-bold rounded px-1.5 py-0.5 flex-shrink-0 ${r.type === 'manager' ? 'text-gold bg-gold/10 border border-gold/30' : 'text-aqua bg-aqua/10 border border-aqua/30'}`}>
                      {r.type === 'manager' ? (isAr ? 'إدارة' : 'Mgmt') : (isAr ? 'تدريب' : 'Coach')}
                    </span>
                  </div>
                  <p className="text-teal text-[11px] mt-0.5">{localize(r.role, locale)}</p>
                  <p className="text-hint text-[10px] mt-0.5">
                    {[localize(r.age, locale), localize(r.season, locale)].filter(Boolean).join(' · ')}
                    {r.current ? ` · ${isAr ? 'حالي' : 'now'}` : ''}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
