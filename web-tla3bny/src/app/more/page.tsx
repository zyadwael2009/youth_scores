'use client';
import Link from 'next/link';
import { useTT } from '@/components/tla3bny/kit';

// The "More" hub reached from the bottom bar: the things that don't warrant
// their own tab — what you follow, and how to reach us.
export default function MorePage() {
  const tt = useTT();
  const chevron = tt('‹', '›');
  return (
    <div className="space-y-3 max-w-lg mx-auto">
      <MoreTile
        href="/more/favourites"
        emoji="⭐"
        title={tt('المتابَعات', 'Following')}
        sub={tt('البطولات والفرق واللاعبون الذين تتابعهم', 'Competitions, teams and players you follow')}
        chevron={chevron}
      />
      <MoreTile
        href="/contact"
        emoji="💬"
        title={tt('تواصل معنا', 'Contact Us')}
        sub={tt('للدعم الفني واقتراحات الأكاديميات لتطوير تلاعبني',
                'Technical support & academy suggestions to improve tla3bny')}
        chevron={chevron}
      />
      <MoreTile
        href="/about"
        emoji="🏆"
        title={tt('من نحن', 'About')}
        sub={tt('نبذة عن تلاعبني وما نقدّمه', 'About tla3bny and what we offer')}
        chevron={chevron}
      />
      <MoreTile
        href="/privacy-policy"
        emoji="🔒"
        title={tt('سياسة الخصوصية', 'Privacy Policy')}
        sub={tt('كيف نجمع بياناتك ونحميها', 'How we collect and protect your data')}
        chevron={chevron}
      />
      <MoreTile
        href="/terms"
        emoji="📜"
        title={tt('الشروط والأحكام', 'Terms & Conditions')}
        sub={tt('قواعد استخدام المنصة', 'The rules for using the platform')}
        chevron={chevron}
      />
    </div>
  );
}

function MoreTile({ href, emoji, title, sub, chevron }: {
  href: string; emoji: string; title: string; sub: string; chevron: string;
}) {
  return (
    <Link
      href={href}
      className="flex items-center gap-3 bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-xl px-4 py-3.5 transition-all hover:border-aqua/30 active:opacity-80"
    >
      <span className="w-11 h-11 rounded-xl grid place-items-center text-xl bg-aqua/10 border border-aqua/20 flex-shrink-0">
        {emoji}
      </span>
      <span className="flex-1 min-w-0">
        <span className="block text-text font-bold text-sm">{title}</span>
        <span className="block text-hint text-xs mt-0.5">{sub}</span>
      </span>
      <span className="text-hint text-lg">{chevron}</span>
    </Link>
  );
}
