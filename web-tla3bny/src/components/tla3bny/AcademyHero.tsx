'use client';
import { mediaUrl, type TAcademy } from '@/lib/tla3bnyApi';

// The academy identity card — mirrors CompetitionHero: a top row with the
// contained logo (never cropped), the name and the branch names, and a
// full-width "about" blurb beneath so it reads on a phone.
export default function AcademyHero({ academy }: { academy: TAcademy }) {
  const logo = mediaUrl(academy.logo_path);
  const branches = (academy.branches ?? []).map(b => b.name).filter(Boolean);
  return (
    <div className="bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-2xl p-4 shadow-[0_20px_40px_-24px_rgba(0,0,0,0.7)]">
      <div className="flex items-center gap-3">
        {logo ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={logo} alt={academy.name}
            className="w-20 h-20 sm:w-24 sm:h-24 object-contain rounded-xl flex-shrink-0 bg-darkBg border border-bdr/60 p-1" />
        ) : (
          <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-xl bg-aqua/10 grid place-items-center text-4xl flex-shrink-0">🏫</div>
        )}
        <div className="flex-1 min-w-0 flex flex-col gap-1.5">
          <h1 className="text-text font-black text-xl leading-tight">{academy.name}</h1>
          {branches.length > 0 && (
            <p className="text-hint text-xs flex items-start gap-1">
              <span aria-hidden="true">📍</span>
              <span className="line-clamp-2">{branches.join(' · ')}</span>
            </p>
          )}
        </div>
      </div>
      {academy.description && (
        <p className="text-sm text-teal leading-relaxed line-clamp-3 mt-3">{academy.description}</p>
      )}
    </div>
  );
}
