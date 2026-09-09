'use client';
import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { tNews } from '@/lib/tla3bnyApi';
import { countUnseen, markSeen, newsSeenKey, newsIds } from '@/lib/seen';

// Light locale/theme provider for the standalone tla3bny app. It exposes the
// same `useApp()` shape the shared tla3bny components rely on (locale, isDark,
// toggleLocale, toggleTheme) WITHOUT the youthscores config/competition/ads
// machinery — this app talks only to /api/tla3bny.
interface AppContextValue {
  locale: 'ar' | 'en';
  isDark: boolean;
  toggleLocale: () => void;
  toggleTheme: () => void;
  /** How many news items are new since the user last opened the News page — the
   *  count on the bottom-nav News badge (all competitions + site-wide news). */
  newNewsCount: number;
  /** Called when the News page opens: everything in the feed becomes seen, so
   *  the badge clears until something new arrives. */
  markNewsSeen: () => void;
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
  const [newNewsCount, setNewNewsCount] = useState(0);
  // The loaded feed's ids, and a flag for "the user opened News before the feed
  // arrived" so the clear still applies once it does (no empty-baseline wipe).
  const newsIdsRef = useRef<string[]>([]);
  const pendingSeenRef = useRef(false);

  useEffect(() => {
    const l = localStorage.getItem('locale') as 'ar' | 'en' | null;
    const d = localStorage.getItem('isDark');
    if (l) setLocale(l);
    if (d !== null) setIsDark(d === 'true');
  }, []);

  // Fetch the news feed once per app load to badge how many are new since the
  // last News-page visit (newest 50, matching the list the page itself shows).
  useEffect(() => {
    tNews({}).then(items => {
      const ids = newsIds(items);
      newsIdsRef.current = ids;
      if (pendingSeenRef.current) { markSeen(newsSeenKey(), ids); setNewNewsCount(0); }
      else setNewNewsCount(countUnseen(newsSeenKey(), ids));
    }).catch(() => undefined);
  }, []);

  const markNewsSeen = useCallback(() => {
    // If the feed hasn't loaded yet, defer the clear to the fetch above rather
    // than writing an empty baseline (which would re-count everything as new).
    if (newsIdsRef.current.length) markSeen(newsSeenKey(), newsIdsRef.current);
    pendingSeenRef.current = true;
    setNewNewsCount(0);
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
    <Ctx.Provider value={{ locale, isDark, toggleLocale, toggleTheme, newNewsCount, markNewsSeen }}>
      {children}
    </Ctx.Provider>
  );
}
