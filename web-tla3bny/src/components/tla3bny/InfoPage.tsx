'use client';
import Link from 'next/link';
import { useApp } from '@/context/AppContext';

export type InfoSection = { emoji: string; title: string; body?: string; items?: string[] };

/** Shared layout for the static info pages (About / Privacy / Terms): a hero,
 *  a list of emoji-titled sections, and a footer that cross-links the others.
 *  Content is passed per-locale so each page just supplies its copy. */
export default function InfoPage({
  hero, sections,
}: {
  hero: { emoji: string; title: string; sub: string };
  sections: { ar: InfoSection[]; en: InfoSection[] };
}) {
  const { locale } = useApp();
  const isAr = locale === 'ar';
  const content = isAr ? sections.ar : sections.en;
  return (
    <div className="space-y-4 max-w-lg mx-auto pb-8">
      <div className="text-center py-4">
        <div className="text-5xl mb-3">{hero.emoji}</div>
        <h1 className="text-aqua font-black text-2xl">{hero.title}</h1>
        <p className="text-teal text-sm mt-1">{hero.sub}</p>
      </div>

      {content.map((sec, i) => (
        <div key={i} className="bg-cardBg border border-bdr rounded-2xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-2xl">{sec.emoji}</span>
            <h2 className="text-aqua font-bold text-base">{sec.title}</h2>
          </div>
          {sec.body && <p className="text-teal text-sm leading-[1.9]">{sec.body}</p>}
          {sec.items && (
            <ul className="space-y-2">
              {sec.items.map((it, j) => (
                <li key={j} className="flex items-start gap-2 text-teal text-sm">
                  <span className="text-aqua mt-0.5 flex-shrink-0">✓</span>{it}
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}

      <div className="flex flex-wrap justify-center gap-x-4 gap-y-1 text-xs text-hint pt-2">
        <Link href="/about" className="hover:text-aqua">{isAr ? 'من نحن' : 'About'}</Link>
        <span>·</span>
        <Link href="/privacy-policy" className="hover:text-aqua">{isAr ? 'سياسة الخصوصية' : 'Privacy'}</Link>
        <span>·</span>
        <Link href="/terms" className="hover:text-aqua">{isAr ? 'الشروط والأحكام' : 'Terms'}</Link>
        <span>·</span>
        <Link href="/contact" className="hover:text-aqua">{isAr ? 'تواصل معنا' : 'Contact'}</Link>
      </div>
    </div>
  );
}
