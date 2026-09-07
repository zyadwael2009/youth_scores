'use client';
import { useEffect, useState } from 'react';
import { useTT } from './kit';
import {
  followTeam, unfollowTeam, isFollowingTeam, notifState, type NotifState,
} from '@/lib/notifications';

// Star toggle on a team's page: follow it to get a push when the team's match
// results are posted — a parent can follow just their kid's team without following
// the whole competition. Mirrors the competition FollowButton. Hidden where web
// push isn't supported so it never dead-ends.
export default function FollowTeamButton({ teamId }: { teamId: string | number }) {
  const tt = useTT();
  const [supported, setSupported] = useState(false);
  const [following, setFollowing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [blocked, setBlocked] = useState(false);

  useEffect(() => {
    setSupported(notifState() !== 'unsupported');
    setFollowing(isFollowingTeam(teamId));
    setBlocked(notifState() === 'denied');
  }, [teamId]);

  if (!supported || !teamId) return null;

  const label = following
    ? tt('إلغاء متابعة نتائج الفريق', 'Unfollow team results')
    : blocked
      ? tt('الإشعارات محظورة في المتصفح', 'Notifications blocked in browser')
      : tt('تابع نتائج هذا الفريق', 'Follow this team’s results');

  const onClick = async () => {
    if (busy) return;
    setBusy(true);
    try {
      if (following) {
        await unfollowTeam(teamId);
        setFollowing(false);
      } else {
        const res: NotifState = await followTeam(teamId);
        if (res === 'granted') { setFollowing(true); setBlocked(false); }
        else if (res === 'denied') setBlocked(true);
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <button onClick={onClick} disabled={busy} title={label} aria-label={label} aria-pressed={following}
      className={`flex items-center gap-1 text-sm leading-none rounded-lg px-2.5 py-1 border transition-colors flex-shrink-0
        ${following ? 'border-yellow-400/60 bg-yellow-400/10 text-yellow-400'
                    : 'border-aqua/40 bg-cardBg text-aqua hover:bg-aqua/10'}`}>
      <span aria-hidden="true">{busy ? '…' : following ? '★' : '☆'}</span>
      <span className="text-[11px] font-bold">
        {following ? tt('متابَع', 'Following') : tt('متابعة', 'Follow')}
      </span>
    </button>
  );
}
