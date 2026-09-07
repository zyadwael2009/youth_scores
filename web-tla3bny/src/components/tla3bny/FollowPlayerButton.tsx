'use client';
import { useEffect, useState } from 'react';
import { useTT } from './kit';
import {
  followPlayer, unfollowPlayer, isFollowingPlayer, notifState, type NotifState,
} from '@/lib/notifications';

// Star toggle on a player's page: follow to get a push when the player scores — a
// parent following their child. Mirrors the team/competition follow buttons.
export default function FollowPlayerButton({ playerId }: { playerId: string | number }) {
  const tt = useTT();
  const [supported, setSupported] = useState(false);
  const [following, setFollowing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [blocked, setBlocked] = useState(false);

  useEffect(() => {
    setSupported(notifState() !== 'unsupported');
    setFollowing(isFollowingPlayer(playerId));
    setBlocked(notifState() === 'denied');
  }, [playerId]);

  if (!supported || !playerId) return null;

  const label = following
    ? tt('إلغاء متابعة أهداف اللاعب', 'Unfollow player goals')
    : blocked
      ? tt('الإشعارات محظورة في المتصفح', 'Notifications blocked in browser')
      : tt('تابع أهداف هذا اللاعب', 'Follow this player’s goals');

  const onClick = async () => {
    if (busy) return;
    setBusy(true);
    try {
      if (following) {
        await unfollowPlayer(playerId);
        setFollowing(false);
      } else {
        const res: NotifState = await followPlayer(playerId);
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
