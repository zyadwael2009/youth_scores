'use client';
import { useRouter } from 'next/navigation';

interface Props {
  title: string;
  back?: boolean;
  actions?: React.ReactNode;
}

export default function AppBar({ title, back, actions }: Props) {
  const router = useRouter();
  return (
    <header className="sticky top-0 z-40 bg-cardBg border-b border-bdr flex items-center px-4 py-3 gap-3 safe-top">
      {back && (
        <button onClick={() => router.back()} className="text-aqua text-xl">‹</button>
      )}
      <h1 className="flex-1 text-aqua font-bold text-base truncate">{title}</h1>
      {actions}
    </header>
  );
}
