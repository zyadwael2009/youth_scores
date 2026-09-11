'use client';
import { type ReactNode } from 'react';
import { mediaUrl, type TCompetition } from '@/lib/tla3bnyApi';
import { useTT, useName } from './kit';

// The competition identity card: a top row with the logo, name, edition/age
// chips and location, and — when there is one — a full-width blurb beneath it.
// The blurb sits on its own row (not squeezed beside the logo) so it reads on a
// phone; the logo is contained (never cropped). Shared by the competition page
// and the sub-competition view so they look the same.
//   • title       — override the heading (the sub-comp view titles it by the
//                   sub-competition instead of the parent competition)
//   • description — override the blurb (pass null to hide it)
//   • ageLabel    — names the open sub-competition (shown as a chip)
//   • action      — an optional control at the top-end (e.g. the info toggle)
export default function CompetitionHero({ comp, title, description, ageLabel, action }: {
  comp: TCompetition;
  title?: string;
  description?: string | null;
  ageLabel?: string | null;
  action?: ReactNode;
}) {
  const tt = useTT();
  const nm = useName();
  const logo = mediaUrl(comp.logo_path);
  // Use the English name when the UI is in English (falls back to Arabic).
  const heading = title ?? nm(comp.name, comp.name_en);
  const blurb = description === undefined ? comp.description : description;
  return (
    <div className="bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-2xl p-4 shadow-[0_20px_40px_-24px_rgba(0,0,0,0.7)]">
      {/* Top row: logo + name / chips / location */}
      <div className="flex items-center gap-3">
        {logo ? (
          // object-contain (not cover) so the whole crest shows, shrunk to fit.
          // eslint-disable-next-line @next/next/no-img-element
          <img src={logo} alt={heading}
            className="w-20 h-20 sm:w-24 sm:h-24 object-contain rounded-xl flex-shrink-0 bg-darkBg border border-bdr/60 p-1" />
        ) : (
          <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-xl bg-aqua/10 grid place-items-center text-4xl flex-shrink-0">🏆</div>
        )}
        <div className="flex-1 min-w-0 flex flex-col gap-1.5">
          <div className="flex items-start gap-2">
            <h1 className="flex-1 min-w-0 text-text font-black text-xl leading-tight">{heading}</h1>
            {action}
          </div>
          {/* The organizer's edition/season number (الموسم), right under the name. */}
          {comp.season_number != null && (
            <span className="self-start text-xs font-bold text-gold">
              {tt(`الموسم ${comp.season_number}`, `Season ${comp.season_number}`)}
            </span>
          )}
          {ageLabel && (
            <span className="self-start text-[11px] font-bold text-aqua bg-aqua/10 border border-aqua/30 rounded-full px-2.5 py-0.5">
              {ageLabel}
            </span>
          )}
          {comp.location && (
            <p className="text-hint text-xs flex items-center gap-1"><span aria-hidden="true">📍</span>{comp.location}</p>
          )}
        </div>
      </div>

      {/* Full-width blurb beneath, so it has room to read on a phone. */}
      {blurb && <p className="text-sm text-teal leading-relaxed line-clamp-3 mt-3">{blurb}</p>}
    </div>
  );
}
