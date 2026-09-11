'use client';
import { type ReactNode } from 'react';
import { mediaUrl, type TTeam } from '@/lib/tla3bnyApi';
import { useName } from './kit';

// The team identity card — mirrors CompetitionHero / AcademyHero: a top row
// with the contained photo (never cropped), the team name + age category, and
// a full-width description beneath. `action` renders a control (e.g. the follow
// button) in the top corner.
export default function TeamHero({ team, action }: { team: TTeam; action?: ReactNode }) {
  const nm = useName();
  const photo = mediaUrl(team.photo_path);
  return (
    <div className="bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-2xl p-4 shadow-[0_20px_40px_-24px_rgba(0,0,0,0.7)]">
      <div className="flex items-center gap-3">
        {photo ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={photo} alt={team.display_name}
            className="w-20 h-20 sm:w-24 sm:h-24 object-contain rounded-xl flex-shrink-0 bg-darkBg border border-bdr/60 p-1" />
        ) : (
          <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-xl bg-aqua/10 grid place-items-center text-4xl flex-shrink-0">⚽</div>
        )}
        <div className="flex-1 min-w-0 flex flex-col gap-1.5">
          <div className="flex items-start gap-2">
            <h1 className="flex-1 min-w-0 text-text font-black text-xl leading-tight">{nm(team.display_name, team.display_name_en)}</h1>
            {action}
          </div>
          {team.age_category && (
            <span className="self-start text-[11px] font-bold text-aqua bg-aqua/10 border border-aqua/30 rounded-full px-2.5 py-0.5">
              {team.age_category}
            </span>
          )}
        </div>
      </div>
      {team.description && (
        <p className="text-sm text-teal leading-relaxed line-clamp-3 mt-3">{team.description}</p>
      )}
    </div>
  );
}
