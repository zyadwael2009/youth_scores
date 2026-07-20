'use client';
import Link from 'next/link';
import { useApp } from '@/context/AppContext';

export default function ControlsBar() {
  const { locale, isDark, toggleLocale, toggleTheme } = useApp();
  const isAr = locale === 'ar';

  // Matches the width the banner and bottom nav are held to, so the controls
  // line up with the rest of the column on a wide screen.
  return (
    <div className="w-full max-w-lg mx-auto flex items-center gap-2 px-3 py-2" dir="ltr">
      <button
        onClick={toggleLocale}
        className="text-[10px] text-aqua font-bold border border-aqua/40 rounded-lg px-2 py-1 leading-none bg-cardBg hover:bg-aqua/10 transition-colors"
      >
        {locale === 'ar' ? 'EN' : 'ع'}
      </button>
      <button
        onClick={toggleTheme}
        className="text-sm leading-none bg-cardBg border border-bdr rounded-lg px-2 py-1 hover:bg-aqua/10 transition-colors"
        aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      >
        {isDark ? '☀️' : '🌙'}
      </button>

      {/* Pushed to the far end so it never crowds the language and theme
          toggles. The admin shell covers this bar, so it is only ever seen on
          the public site. */}
      <Link
        href="/admin/login"
        className="ms-auto flex items-center gap-1.5 text-[11px] font-bold text-aqua border border-aqua/40 rounded-lg px-3 py-1 leading-none bg-cardBg hover:bg-aqua/10 transition-colors"
      >
        <span aria-hidden="true">🔑</span>
        {isAr ? 'دخول' : 'Log in'}
      </Link>
    </div>
  );
}
