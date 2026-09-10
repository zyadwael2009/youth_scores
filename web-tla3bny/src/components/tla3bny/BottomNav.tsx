'use client';
import { useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useApp } from '@/context/AppContext';

const tabs = [
  { href: '/',             icon: '🏠', arLabel: 'الرئيسية',   enLabel: 'Home' },
  { href: '/competitions', icon: '🏆', arLabel: 'البطولات',   enLabel: 'Competitions' },
  { href: '/academies',    icon: '🏫', arLabel: 'الأكاديميات', enLabel: 'Academies' },
  { href: '/news',         icon: '📰', arLabel: 'الأخبار',    enLabel: 'News' },
  { href: '/more',         icon: '☰', arLabel: 'المزيد',     enLabel: 'More' },
];

export default function BottomNav() {
  const pathname = usePathname();
  const { locale, newNewsCount, markNewsSeen } = useApp();

  // Landing on the News page clears its badge until new items arrive. Done here
  // (rather than in the page) so the News route stays a plain static file.
  // trailingSlash is on, so usePathname yields "/news/"; strip it before match.
  const route = pathname.replace(/\/+$/, '') || '/';
  useEffect(() => { if (route === '/news') markNewsSeen(); }, [route, markNewsSeen]);

  return (
    <nav className="fixed bottom-0 inset-x-0 bg-cardBg border-t border-bdr safe-bottom z-50">
      <div className="flex items-stretch max-w-3xl mx-auto">
        {tabs.map(tab => {
          const active = tab.href === '/' ? pathname === '/' : pathname.startsWith(tab.href);
          const label = locale === 'ar' ? tab.arLabel : tab.enLabel;
          const badge = tab.href === '/news' ? newNewsCount : 0;
          return (
            <Link key={tab.href} href={tab.href}
              className={`flex-1 flex flex-col items-center justify-center py-2 gap-0.5 transition-colors relative ${active ? 'text-aqua' : 'text-hint'}`}>
              <span className="relative text-lg">
                {tab.icon}
                {badge > 0 && (
                  <span className="absolute -top-1 -end-2 min-w-[15px] h-[15px] px-1 grid place-items-center rounded-full bg-red-500 text-white text-[9px] font-bold leading-none tnum">
                    {badge > 99 ? '99+' : badge}
                  </span>
                )}
              </span>
              <span className={`text-[9px] leading-tight text-center ${active ? 'font-bold' : ''}`}>{label}</span>
              {active && <div className="absolute bottom-0 h-0.5 w-6 bg-aqua rounded-t" />}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
