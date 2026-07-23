'use client';
import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { tMatch, tMatchLineups, type TMatch, type TLineup } from '@/lib/tla3bnyApi';
import { formatMatchDate } from '@/lib/utils';
import { useApp } from '@/context/AppContext';
import { useTla3bnyAuth } from '@/context/Tla3bnyAuthContext';
import Spinner from '@/components/ui/Spinner';
import PitchView, { type SlotView } from '@/components/tla3bny/PitchView';
import { LogoAvatar, StatusBadge, EmptyState, useTT } from '@/components/tla3bny/kit';

const EVENT_ICON: Record<string, string> = {
  goal: '⚽', assist: '🅰️', yellow: '🟨', red: '🟥',
  substitution_in: '🔺', substitution_out: '🔻',
};

function Timeline({ m }: { m: TMatch }) {
  const tt = useTT();
  const events = (m.events ?? []).filter(e => e.event_type !== 'assist');
  const assists = (m.events ?? []).filter(e => e.event_type === 'assist');
  if (events.length === 0) return <EmptyState icon="⏱️" text={tt('لا توجد أحداث', 'No events recorded')} />;

  return (
    <div className="space-y-1.5">
      {events.map(e => {
        const home = e.team_academy_id === m.home_academy_id;
        const assist = e.event_type === 'goal'
          ? assists.find(a => a.related_event_id === e.id)
          : undefined;
        const label = (
          <div className={home ? 'text-right' : 'text-left'}>
            <span className="font-bold text-text text-sm">{e.player_name ?? '—'}</span>
            {assist && <span className="text-hint text-xs"> · {tt('صناعة', 'assist')} {assist.player_name}</span>}
          </div>
        );
        return (
          <div key={e.id} className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 bg-cardBg2/50 rounded-lg px-3 py-2">
            <div>{home && label}</div>
            <div className="flex items-center gap-1.5 text-xs text-hint whitespace-nowrap">
              {e.minute != null && <span className="tnum font-bold">{e.minute}&apos;</span>}
              <span>{EVENT_ICON[e.event_type] ?? '•'}</span>
            </div>
            <div>{!home && label}</div>
          </div>
        );
      })}
    </div>
  );
}

/** One team's saved lineup: the pitch, its substitutes, and (for the authorized
 *  editor) a link into the builder. `lu` is null when nothing is saved yet. */
function SideLineup({
  matchId, academyId, academyName, lu, canEdit,
}: {
  matchId: number; academyId: number; academyName: string | null;
  lu: TLineup | null; canEdit: boolean;
}) {
  const tt = useTT();
  const editHref = `/lineup/?match=${matchId}&academy=${academyId}`;

  const filled: Record<string, SlotView> = {};
  const subs = (lu?.slots ?? []).filter(s => s.is_substitute);
  for (const s of lu?.slots ?? []) {
    if (!s.is_substitute && s.position_slot) {
      filled[s.position_slot] = {
        playerId: s.player_id, playerName: s.player_name,
        jerseyNumber: s.jersey_number, photoPath: s.photo_path,
      };
    }
  }

  return (
    <div className="bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-2xl p-4 space-y-3">
      <div className="flex items-center justify-between gap-2">
        <span className="font-bold text-text text-sm truncate">{academyName}</span>
        <div className="flex items-center gap-2 shrink-0">
          {lu?.formation && <span className="text-[11px] font-bold text-aqua bg-aqua/10 px-2 py-0.5 rounded">{lu.formation}</span>}
          {canEdit && (
            <Link href={editHref} className="text-[11px] font-bold text-aqua hover:underline">
              {lu ? tt('تعديل', 'Edit') : tt('إضافة', 'Add')}
            </Link>
          )}
        </div>
      </div>

      {lu ? (
        <>
          <PitchView formation={lu.formation} filled={filled} />
          {subs.length > 0 && (
            <div>
              <div className="text-[11px] text-hint font-bold mb-1">{tt('البدلاء', 'Substitutes')}</div>
              <div className="flex flex-wrap gap-1.5">
                {subs.map(s => (
                  <span key={s.id} className="text-xs text-text bg-cardBg2 border border-bdr rounded-full px-2 py-0.5">
                    {s.jersey_number != null && <span className="text-aqua font-bold me-1">#{s.jersey_number}</span>}
                    {s.player_name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <p className="text-xs text-hint">{tt('لم تُسجَّل التشكيلة بعد.', 'No lineup set yet.')}</p>
      )}
    </div>
  );
}

function MatchContent() {
  const tt = useTT();
  const { locale } = useApp();
  const { user, isSuperAdmin, isApprovedAcademy } = useTla3bnyAuth();
  const params = useSearchParams();
  const id = Number(params.get('id'));
  const [m, setM] = useState<TMatch | null>(null);
  const [lineups, setLineups] = useState<TLineup[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) { setLoading(false); return; }
    setLoading(true);
    Promise.all([tMatch(id), tMatchLineups(id).catch(() => [])])
      .then(([mm, lu]) => { setM(mm); setLineups(lu); })
      .catch(() => setM(null))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <Spinner />;
  if (!m) return <EmptyState icon="🔍" text={tt('المباراة غير موجودة', 'Match not found')} />;

  const finished = m.status === 'finished';
  const statusLabel = { scheduled: tt('مجدولة', 'Scheduled'), live: tt('مباشر', 'Live'), finished: tt('انتهت', 'Finished') }[m.status];

  return (
    <div className="space-y-5">
      <Link href="/" className="text-sm text-hint hover:text-aqua">← {tt('الرجوع', 'Back')}</Link>

      <div className="bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-2xl p-5">
        <div className="flex items-center justify-center gap-2 mb-4 text-xs text-hint">
          {m.age_category && <span className="font-bold text-teal">U{m.age_category}</span>}
          <StatusBadge status={m.status} label={statusLabel} />
        </div>
        <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">
          <div className="flex flex-col items-center gap-2 text-center">
            <LogoAvatar src={m.home_academy_logo} name={m.home_academy_name} size={56} />
            <span className="font-bold text-text text-sm">{m.home_academy_name}</span>
          </div>
          <div className="text-center px-2">
            {finished || (m.home_score != null) ? (
              <div className="font-black text-3xl text-text tnum whitespace-nowrap">
                {m.home_score ?? 0} <span className="text-hint">-</span> {m.away_score ?? 0}
              </div>
            ) : (
              <div className="text-hint font-bold">{tt('ضد', 'vs')}</div>
            )}
            <div className="text-[11px] text-hint mt-1">
              {formatMatchDate(m.date ?? '', locale)}{m.time ? ` · ${m.time}` : ''}
            </div>
          </div>
          <div className="flex flex-col items-center gap-2 text-center">
            <LogoAvatar src={m.away_academy_logo} name={m.away_academy_name} size={56} />
            <span className="font-bold text-text text-sm">{m.away_academy_name}</span>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 mt-4 pt-4 border-t border-bdr text-[11px] text-hint">
          {m.venue && <span>📍 {m.venue}</span>}
          <span>⏱️ {m.num_periods}×{Math.round(m.duration_minutes / m.num_periods)} {tt('دقيقة', 'min')}</span>
          <span>🔁 {tt('تبديلات', 'subs')}: {m.max_substitutions}</span>
        </div>
      </div>

      <section>
        <h2 className="font-extrabold text-text mb-2">{tt('الأحداث', 'Events')}</h2>
        <Timeline m={m} />
      </section>

      {(() => {
        const homeLu = lineups.find(l => l.academy_id === m.home_academy_id) ?? null;
        const awayLu = lineups.find(l => l.academy_id === m.away_academy_id) ?? null;
        const canEditHome = isSuperAdmin || (isApprovedAcademy && user?.id === m.home_academy_id);
        const canEditAway = isSuperAdmin || (isApprovedAcademy && user?.id === m.away_academy_id);
        // Show the section when there is something to show or someone who can edit.
        if (!homeLu && !awayLu && !canEditHome && !canEditAway) return null;
        return (
          <section>
            <h2 className="font-extrabold text-text mb-2">{tt('التشكيلات', 'Lineups')}</h2>
            <div className="grid sm:grid-cols-2 gap-4">
              <SideLineup matchId={m.id} academyId={m.home_academy_id} academyName={m.home_academy_name} lu={homeLu} canEdit={canEditHome} />
              <SideLineup matchId={m.id} academyId={m.away_academy_id} academyName={m.away_academy_name} lu={awayLu} canEdit={canEditAway} />
            </div>
          </section>
        );
      })()}
    </div>
  );
}

export default function MatchPage() {
  return (
    <Suspense fallback={<Spinner />}>
      <MatchContent />
    </Suspense>
  );
}
