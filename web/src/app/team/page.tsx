'use client';
import { Suspense, useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useApp } from '@/context/AppContext';
import AppBar from '@/components/ui/AppBar';
import Spinner from '@/components/ui/Spinner';
import { fetchTeam } from '@/lib/api';
import { localize, teamNameLines } from '@/lib/utils';
import type { TeamPublic } from '@/lib/types';

export default function TeamPage() {
  return (
    <Suspense fallback={<Spinner label="..." />}>
      <TeamProfile />
    </Suspense>
  );
}

function TeamProfile() {
  const params = useSearchParams();
  const id = params.get('id') ?? '';
  const { locale } = useApp();
  const router = useRouter();
  const [t, setT] = useState<TeamPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const isAr = locale === 'ar';

  useEffect(() => {
    if (!id) { setLoading(false); return; }
    setLoading(true);
    fetchTeam(id).then(setT).finally(() => setLoading(false));
  }, [id]);

  // The club is the identity; a second name (academy/sponsor) sits beneath it,
  // exactly as the standings and match cards show it.
  const lines = t ? teamNameLines({ name: t.name, clubName: t.club.name }, locale) : null;
  const title = lines ? lines.primary : (isAr ? 'الفريق' : 'Team');

  return (
    <>
      <AppBar title={title} back />
      {loading ? <Spinner label={isAr ? 'جاري التحميل...' : 'Loading...'} />
        : !t ? <div className="p-8 text-center text-hint">{isAr ? 'الفريق غير موجود' : 'Team not found'}</div>
        : (
        <div className="pb-24">
          {/* Hero */}
          <div className="relative overflow-hidden bg-gradient-to-b from-cardBg to-cardBg2 border-b border-bdr p-5 flex items-center gap-4">
            <div className="absolute -right-10 -top-10 w-44 h-44 rounded-full bg-[radial-gradient(circle,rgb(var(--accent-rgb)/0.14),transparent_65%)]" />
            {t.logo
              ? <img src={t.logo} alt="" className="relative w-16 h-16 rounded-2xl object-contain bg-darkBg" />
              : <div className="relative w-16 h-16 rounded-2xl bg-darkBg grid place-items-center text-2xl">🛡️</div>}
            <div className="relative min-w-0">
              <h1 onClick={() => router.push(`/club?id=${t.club.id}`)}
                className="text-lg font-extrabold truncate cursor-pointer hover:text-aqua transition-colors">
                {lines!.primary} <span className="text-aqua text-xs align-middle">›</span>
              </h1>
              {lines!.alias && (
                <p className="text-hint text-sm truncate">{lines!.alias}</p>
              )}
              <p className="text-hint text-xs truncate mt-0.5">
                {[localize(t.age, locale), t.seasons.map(s => localize(s, locale)).join('، ')]
                  .filter(Boolean).join(' · ')}
              </p>
            </div>
          </div>

          {/* Technical staff */}
          <div className="px-4 pt-5">
            <h2 className="text-text font-bold text-sm mb-3">{isAr ? 'الجهاز الفني' : 'Technical Staff'}</h2>
            {t.staff.length === 0 ? (
              <p className="text-hint text-sm text-center py-4">{isAr ? 'لا توجد بيانات' : 'No data'}</p>
            ) : (
              <div className="space-y-2">
                {t.staff.map(s => (
                  <button key={`${s.id}-${s.role?.ar ?? ''}`} onClick={() => router.push(`/coach?id=${s.id}`)}
                    className="w-full flex items-center gap-3 bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-2xl p-3 text-start hover:border-aqua/40 transition-colors">
                    {s.photo
                      ? <img src={s.photo} alt="" className="w-10 h-10 rounded-full object-cover bg-darkBg flex-shrink-0" />
                      : <div className="w-10 h-10 rounded-full bg-darkBg grid place-items-center flex-shrink-0">👤</div>}
                    <div className="flex-1 min-w-0">
                      <p className="text-text font-bold text-sm truncate">{localize(s.name, locale)}</p>
                      <p className="text-teal text-[11px] truncate">{localize(s.role, locale) || '—'}</p>
                    </div>
                    <span className="text-aqua text-xs flex-shrink-0">›</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Roster */}
          <div className="px-4 pt-5">
            <h2 className="text-text font-bold text-sm mb-3">
              {isAr ? 'اللاعبون' : 'Players'}
              {t.roster.length > 0 && <span className="text-hint text-xs font-normal"> ({t.roster.length})</span>}
            </h2>
            {t.roster.length === 0 ? (
              <p className="text-hint text-sm text-center py-4">{isAr ? 'لا توجد قائمة' : 'No squad'}</p>
            ) : (
              <div className="space-y-2">
                {t.roster.map(p => (
                  <button key={p.id} onClick={() => router.push(`/player?id=${p.id}`)}
                    className="w-full flex items-center gap-3 bg-cardBg border border-bdr rounded-xl px-3 py-2.5 text-start hover:border-aqua/40 transition-colors">
                    <div className="w-8 h-8 rounded-lg bg-darkBg grid place-items-center flex-shrink-0 text-aqua font-bold text-sm tnum">{p.shirt ?? '—'}</div>
                    <div className="flex-1 min-w-0">
                      <p className="text-text text-sm font-bold truncate">{localize(p.name, locale)}</p>
                      <p className="text-hint text-[11px] truncate">
                        {[localize(p.position, locale), p.birth_year || ''].filter(Boolean).join(' · ')}
                      </p>
                    </div>
                    <span className="text-aqua text-xs flex-shrink-0">›</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
