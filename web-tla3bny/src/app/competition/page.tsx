'use client';
import { Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { tCompetition, tNews, type TCompetition, type TCompAge, type TNews } from '@/lib/tla3bnyApi';
import { countUnseenExcept, markSeen, newsSeenKey, newsIds } from '@/lib/seen';
import { sortAges } from '@/lib/utils';
import Spinner from '@/components/ui/Spinner';
import CompetitionInfo from '@/components/tla3bny/CompetitionInfo';
import CompetitionHero from '@/components/tla3bny/CompetitionHero';
import FollowButton from '@/components/tla3bny/FollowButton';
import NewsList from '@/components/tla3bny/NewsList';
import { EmptyState, useTT } from '@/components/tla3bny/kit';

type Tab = 'about' | 'subs' | 'news';

// The public competition page. Its hero sits on top, then three tabs:
//   • about — who runs it, معلومات, contact (CompetitionInfo)
//   • subs  — المنافسات (the sub-competitions), each opening its own view
//   • news  — this competition's news (moved here from the sub-competition view)
function CompetitionContent() {
  const tt = useTT();
  const params = useSearchParams();
  const router = useRouter();
  const id = Number(params.get('id'));
  const [comp, setComp] = useState<TCompetition | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>(() => {
    const t = params.get('tab');
    return t === 'subs' || t === 'news' ? t : 'about';
  });
  const [newsItems, setNewsItems] = useState<TNews[] | null>(null);
  const [newsBadge, setNewsBadge] = useState(0);

  useEffect(() => {
    if (!id) { setLoading(false); return; }
    setLoading(true);
    tCompetition(id).then(setComp).catch(() => setComp(null)).finally(() => setLoading(false));
  }, [id]);

  // Badge the News tab with this competition's items new since it was last
  // opened. Items already seen on the global News page count as seen too, so
  // opening that page clears this badge as well.
  useEffect(() => {
    if (!id) return;
    setNewsItems(null);
    tNews({ competition_id: id }).then(items => {
      setNewsItems(items);
      setNewsBadge(countUnseenExcept(newsSeenKey(id), [newsSeenKey()], newsIds(items)));
    }).catch(() => undefined);
  }, [id]);

  // Opening the News tab (including a direct ?tab=news deep link) clears it.
  useEffect(() => {
    if (tab === 'news' && newsItems) {
      markSeen(newsSeenKey(id), newsIds(newsItems));
      setNewsBadge(0);
    }
  }, [tab, newsItems, id]);

  // Keep the open tab in the address bar so a view can be shared/reopened.
  const selectTab = useCallback((t: Tab) => {
    setTab(t);
    const p = new URLSearchParams({ id: String(id) });
    if (t !== 'about') p.set('tab', t);
    router.replace(`/competition?${p.toString()}`, { scroll: false });
  }, [id, router]);

  if (loading) return <Spinner />;
  if (!comp) return <EmptyState icon="🏆" text={tt('البطولة غير موجودة', 'Competition not found')} />;

  const ages = sortAges(comp.ages ?? []);
  const tabs: Tab[] = ['about', 'subs', 'news'];
  const label: Record<Tab, [string, string]> = {
    about: ['عن البطولة', 'About'],
    subs: ['المنافسات', 'Competitions'],
    news: ['الأخبار', 'News'],
  };

  return (
    <div className="space-y-5">
      <Link href="/competitions" className="inline-block text-aqua text-xs font-bold">→ {tt('البطولات', 'Competitions')}</Link>

      {/* Blurb (description) is intentionally hidden in the hero — it shows in the
          About tab instead, so it doesn't crowd the hero on small screens. */}
      <CompetitionHero comp={comp} description={null} action={<FollowButton competitionId={String(comp.id)} />} />

      <div className="flex items-center gap-1 border-b border-bdr overflow-x-auto no-scrollbar">
        {tabs.map(t => (
          <button key={t} onClick={() => selectTab(t)}
            className={`px-3 py-2 text-sm font-bold border-b-2 -mb-px whitespace-nowrap transition-colors ${
              tab === t ? 'border-aqua text-aqua' : 'border-transparent text-teal hover:text-text'}`}>
            {tt(label[t][0], label[t][1])}
            {t === 'news' && newsBadge > 0 && (
              <span className="ms-1.5 inline-grid min-w-[16px] h-[16px] px-1 place-items-center rounded-full bg-red-500 text-white text-[9px] font-extrabold leading-none tnum align-middle">
                {newsBadge > 99 ? '99+' : newsBadge}
              </span>
            )}
          </button>
        ))}
      </div>

      {tab === 'about' && <CompetitionInfo comp={comp} />}

      {tab === 'subs' && <SubsTab comp={comp} ages={ages} />}

      {tab === 'news' && <NewsList compId={comp.id} />}
    </div>
  );
}

// المنافسات: the sub-competitions. Organisers often run the same competition
// across several ages ("League 1" for 2011, 2012, …), so sub-competitions that
// share a name are aggregated under it — tap the name to reveal its ages. A name
// used only once (or an unnamed one) stays a single direct entry.
function SubsTab({ comp, ages }: { comp: TCompetition; ages: TCompAge[] }) {
  const tt = useTT();
  const groups = useMemo(() => {
    const out: { name: string | null; items: TCompAge[] }[] = [];
    const idx = new Map<string, number>();
    for (const a of ages) {
      const key = (a.name || '').trim();
      if (!key) { out.push({ name: null, items: [a] }); continue; }
      const at = idx.get(key);
      if (at != null) out[at].items.push(a);
      else { idx.set(key, out.length); out.push({ name: key, items: [a] }); }
    }
    return out;
  }, [ages]);

  const [open, setOpen] = useState<Set<string>>(new Set());
  const toggle = (name: string) => setOpen(s => {
    const n = new Set(s);
    if (n.has(name)) n.delete(name); else n.add(name);
    return n;
  });

  const cardCls = 'bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-2xl';

  return (
    <section className="space-y-2.5">
      <div className="flex items-baseline justify-between">
        <h2 className="text-text font-black text-base">{tt('المنافسات', 'Competitions')}</h2>
        <span className="text-hint text-xs tnum">{groups.length}</span>
      </div>
      {groups.length === 0 ? (
        <EmptyState icon="📋" text={tt('لا منافسات بعد', 'No competitions yet')} />
      ) : (
        <div className="space-y-2.5">
          {groups.map(g => {
            // Several ages under one name → an expandable header.
            if (g.name && g.items.length > 1) {
              const isOpen = open.has(g.name);
              return (
                <div key={g.name} className={`${cardCls} overflow-hidden`}>
                  <button onClick={() => toggle(g.name!)}
                    className="w-full flex items-center gap-3 p-4 text-start active:opacity-80 transition-colors">
                    <span className="w-11 h-11 rounded-xl bg-aqua/10 grid place-items-center text-lg flex-shrink-0">🏆</span>
                    <span className="flex-1 min-w-0">
                      <span className="block text-text font-bold text-sm truncate">{g.name}</span>
                      <span className="block text-hint text-[11px] mt-0.5">{g.items.length} {tt('فئات', 'ages')}</span>
                    </span>
                    <span className="text-aqua text-base flex-shrink-0">{isOpen ? '▲' : '▼'}</span>
                  </button>
                  {isOpen && (
                    <div className="border-t border-bdr divide-y divide-bdr">
                      {g.items.map(a => (
                        <Link key={a.id} href={`/competitions?comp=${comp.id}&cage=${a.id}`}
                          className="flex items-center gap-3 px-4 py-3 hover:bg-aqua/5 active:opacity-80 transition-colors">
                          <span className="flex-1 min-w-0 text-text text-sm truncate">{a.age_category || tt('فئة', 'Age')}</span>
                          <span className="text-aqua text-base flex-shrink-0">‹</span>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              );
            }
            // A single entry (named once, or unnamed) → a direct link.
            const a = g.items[0];
            return (
              <Link key={a.id} href={`/competitions?comp=${comp.id}&cage=${a.id}`}
                className={`${cardCls} flex items-center gap-3 p-4 hover:border-aqua/50 active:opacity-80 transition-colors`}>
                <span className="w-11 h-11 rounded-xl bg-aqua/10 grid place-items-center text-lg flex-shrink-0">🏆</span>
                <span className="flex-1 min-w-0">
                  <span className="block text-text font-bold text-sm truncate">{a.name || a.age_category}</span>
                  {a.name && a.age_category && (
                    <span className="block text-hint text-[11px] mt-0.5">{a.age_category}</span>
                  )}
                </span>
                <span className="text-aqua text-lg flex-shrink-0">‹</span>
              </Link>
            );
          })}
        </div>
      )}
    </section>
  );
}

export default function CompetitionPage() {
  return <Suspense fallback={<Spinner />}><CompetitionContent /></Suspense>;
}
