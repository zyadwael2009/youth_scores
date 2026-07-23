'use client';
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

// Light locale/theme provider for the standalone tla3bny app. It exposes the
// same `useApp()` shape the shared tla3bny components rely on (locale, isDark,
// toggleLocale, toggleTheme) WITHOUT the youthscores config/competition/ads
// machinery — this app talks only to /api/tla3bny.
interface AppContextValue {
  locale: 'ar' | 'en';
  isDark: boolean;
  toggleLocale: () => void;
  toggleTheme: () => void;
}

const Ctx = createContext<AppContextValue | null>(null);

export function useApp() {
  const c = useContext(Ctx);
  if (!c) throw new Error('useApp outside AppProvider');
  return c;
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocale] = useState<'ar' | 'en'>('ar');
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    const l = localStorage.getItem('locale') as 'ar' | 'en' | null;
    const d = localStorage.getItem('isDark');
    if (l) setLocale(l);
    if (d !== null) setIsDark(d === 'true');
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute('dir', locale === 'ar' ? 'rtl' : 'ltr');
    document.documentElement.setAttribute('lang', locale);
    document.documentElement.classList.toggle('dark', isDark);
  }, [locale, isDark]);

  const toggleLocale = useCallback(() => {
    setLocale(l => { const n = l === 'ar' ? 'en' : 'ar'; localStorage.setItem('locale', n); return n; });
  }, []);

  const toggleTheme = useCallback(() => {
    setIsDark(d => { localStorage.setItem('isDark', String(!d)); return !d; });
  }, []);

  return (
    <Ctx.Provider value={{ locale, isDark, toggleLocale, toggleTheme }}>
      {children}
    </Ctx.Provider>
  );
}
