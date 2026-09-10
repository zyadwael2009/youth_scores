'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { tCompetition, tTeam, tPlayer } from '@/lib/tla3bnyApi';
import {
  followedCompetitions, unfollowCompetition,
  followedTeams, unfollowTeam,
  followedPlayers, unfollowPlayer,
} from '@/lib/notifications';
import Spinner from '@/components/ui/Spinner';
import { LogoAvatar, useName, useTT } from '@/components/tla3bny/kit';

// Followed competitions / teams / players are stored client-side as bare ids
// (see lib/notifications). Their names + logos are resolved by fetching each by
// id, and the ★ unfollows — the one place to see and manage everything followed.

function useFollowed<T>(loadIds: () => string[], fetchOne: (id: number) => Promise<T>) {
  const [ids, setIds] = useState<string[]>([]);
  const [items, setItems] = useState<Record<string, T | null>>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => { setIds(loadIds()); }, [loadIds]);

  useEffect(() => {
    if (!ids.length) { setItems({}); return; }
    let alive = true;
    setLoading(true);
    Promise.all(ids.map(id =>
      fetchOne(Number(id)).then(v => [id, v] as const).catch(() => [id, null] as const)))
      .then(pairs => { if (alive) setItems(Object.fromEntries(pairs)); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [ids, fetchOne]);

  const remove = (id: string, unfollow: (x: string) => Promise<void>) => {
    setIds(xs => xs.filter(x => x !== id));  // optimistic — stays removed on error
    unfollow(id).catch(() => {});
  };

  return { ids, items, loading, remove };
}

export default function FavouritesPage() {
  const tt = useTT();
  const name = useName();

  const comps = useFollowed(followedCompetitions, tCompetition);
  const teams = useFollowed(followedTeams, tTeam);
  const players = useFollowed(followedPlayers, tPlayer);

  const empty = !comps.ids.length && !teams.ids.length && !players.ids.length;
  const chevron = tt('‹', '›');
  const unfollowLabel = tt('إلغاء المتابعة', 'Unfollow');

  if (empty) {
    return (
      <div className="text-center py-16 px-6 max-w-lg mx-auto">
        <div className="text-5xl mb-3">⭐</div>
        <p className="text-text font-bold text-base mb-2">
          {tt('لا توجد عناصر متابَعة بعد', 'Nothing followed yet')}
        </p>
        <p className="text-hint text-sm leading-relaxed">
          {tt(
            'تابِع بطولة أو فريقاً أو لاعباً بالضغط على النجمة ⭐ لتظهر هنا وتصلك إشعارات النتائج.',
            'Follow a competition, team or player with the ⭐ to see it here and get results notifications.',
          )}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-5 max-w-lg mx-auto">
      <Section icon="🏆" label={tt('البطولات', 'Competitions')} count={comps.ids.length}
        loading={comps.loading} hasItems={Object.keys(comps.items).length > 0}
        emptyText={tt('لا بطولات متابَعة', 'No followed competitions')}>
        {comps.ids.map(id => {
          const c = comps.items[id];
          return (
            <FavRow key={id} href={`/competition?id=${id}`}
              image={c?.logo_path}
              label={c ? name(c.name, c.name_en) : `${tt('بطولة', 'Competition')} #${id}`}
              chevron={chevron} unfollowLabel={unfollowLabel}
              onRemove={() => comps.remove(id, unfollowCompetition)} />
          );
        })}
      </Section>

      <Section icon="🛡️" label={tt('الفرق', 'Teams')} count={teams.ids.length}
        loading={teams.loading} hasItems={Object.keys(teams.items).length > 0}
        emptyText={tt('لا فرق متابَعة', 'No followed teams')}>
        {teams.ids.map(id => {
          const t = teams.items[id];
          return (
            <FavRow key={id} href={`/team?id=${id}`}
              image={t?.academy_logo}
              label={t ? name(t.display_name, t.display_name_en) : `${tt('فريق', 'Team')} #${id}`}
              chevron={chevron} unfollowLabel={unfollowLabel}
              onRemove={() => teams.remove(id, unfollowTeam)} />
          );
        })}
      </Section>

      <Section icon="👤" label={tt('اللاعبون', 'Players')} count={players.ids.length}
        loading={players.loading} hasItems={Object.keys(players.items).length > 0}
        emptyText={tt('لا لاعبين متابَعين', 'No followed players')}>
        {players.ids.map(id => {
          const p = players.items[id];
          return (
            <FavRow key={id} href={`/player?id=${id}`}
              image={p?.photo_path}
              label={p ? name(p.name, p.name_en) : `${tt('لاعب', 'Player')} #${id}`}
              chevron={chevron} unfollowLabel={unfollowLabel}
              onRemove={() => players.remove(id, unfollowPlayer)} />
          );
        })}
      </Section>
    </div>
  );
}

function Section({ icon, label, count, loading, hasItems, emptyText, children }: {
  icon: string; label: string; count: number; loading: boolean; hasItems: boolean;
  emptyText: string; children: React.ReactNode;
}) {
  return (
    <div>
      <div className="flex items-center gap-2 px-1 mb-2">
        <span>{icon}</span>
        <span className="text-text font-bold text-sm">{label}</span>
        <span className="text-hint text-xs">({count})</span>
      </div>
      {count === 0
        ? <p className="text-hint text-xs px-1">{emptyText}</p>
        : <div className="space-y-2">
            {loading && !hasItems && <Spinner />}
            {children}
          </div>}
    </div>
  );
}

function FavRow({ href, image, label, chevron, unfollowLabel, onRemove }: {
  href: string; image?: string | null; label: string; chevron: string;
  unfollowLabel: string; onRemove: () => void;
}) {
  return (
    <div className="flex items-center gap-3 bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-xl px-3 py-2.5 transition-all hover:border-aqua/30">
      <Link href={href} className="flex items-center gap-3 flex-1 min-w-0">
        <LogoAvatar src={image} name={label} size={32} />
        <span className="flex-1 min-w-0 text-text text-sm font-bold truncate">{label}</span>
      </Link>
      <button onClick={onRemove} title={unfollowLabel} aria-label={unfollowLabel}
        className="text-gold text-lg leading-none px-1 flex-shrink-0 hover:opacity-70">★</button>
      <Link href={href} className="text-hint text-lg flex-shrink-0">{chevron}</Link>
    </div>
  );
}
