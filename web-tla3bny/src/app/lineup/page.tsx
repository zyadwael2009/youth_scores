'use client';
import { Suspense, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useTla3bnyAuth } from '@/context/Tla3bnyAuthContext';
import LineupBuilder from '@/components/tla3bny/LineupBuilder';
import Spinner from '@/components/ui/Spinner';
import { EmptyState, useTT } from '@/components/tla3bny/kit';

function LineupContent() {
  const tt = useTT();
  const params = useSearchParams();
  const router = useRouter();
  const { user, token, loading, isSuperAdmin } = useTla3bnyAuth();

  const matchId = Number(params.get('match'));
  const queryAcademy = Number(params.get('academy'));
  // An academy may only build its own side; the super admin edits whichever side
  // the entry link named.
  const academyId = isSuperAdmin ? queryAcademy : (user?.id ?? 0);

  useEffect(() => {
    if (loading) return;
    if (!user) router.replace('/login');
  }, [loading, user, router]);

  if (loading || !user || !token) return <Spinner />;
  if (!matchId || !academyId) return <EmptyState icon="⚠️" text={tt('رابط غير صالح', 'Invalid link')} />;

  return (
    <div className="space-y-4">
      <Link href={`/match/?id=${matchId}`} className="text-sm text-hint hover:text-aqua">← {tt('الرجوع للمباراة', 'Back to match')}</Link>
      <LineupBuilder token={token} matchId={matchId} academyId={academyId} />
    </div>
  );
}

export default function LineupPage() {
  return (
    <Suspense fallback={<Spinner />}>
      <LineupContent />
    </Suspense>
  );
}
