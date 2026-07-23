'use client';
import { useEffect, useState } from 'react';
import { tAcademies, type TUser } from '@/lib/tla3bnyApi';
import Spinner from '@/components/ui/Spinner';
import { EmptyState, LogoAvatar, useTT } from '@/components/tla3bny/kit';

export default function AcademiesPage() {
  const tt = useTT();
  const [items, setItems] = useState<TUser[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    tAcademies().then(setItems).catch(() => setItems([])).finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-black text-text">{tt('الأكاديميات', 'Academies')}</h1>
      {loading ? <Spinner /> :
        items.length === 0 ? <EmptyState icon="🏫" text={tt('لا توجد أكاديميات معتمدة بعد', 'No approved academies yet')} /> :
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {items.map(a => (
            <div key={a.id} className="flex flex-col items-center gap-2 bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-2xl p-4 text-center">
              <LogoAvatar src={a.logo_path} name={a.name} size={56} />
              <span className="font-bold text-text text-sm line-clamp-2">{a.name}</span>
            </div>
          ))}
        </div>}
    </div>
  );
}
