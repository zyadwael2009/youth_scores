// Tracks which news the user has already seen, per feed, so a nav item or tab
// can badge how many arrived since their last visit. The first run seeds the
// baseline with everything currently present, so a badge only counts items
// added *after* the user first opened the app — never the whole back-catalogue.
//
// There is one baseline per feed: the global feed (home / the News tab) and one
// per competition. They are independent — opening the global News page clears
// the global badge; opening a competition's News tab clears only that one.

function read(key: string): Set<string> | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(key);
    return raw == null ? null : new Set(JSON.parse(raw) as string[]);
  } catch { return null; }
}

function write(key: string, ids: Iterable<string>): void {
  try { localStorage.setItem(key, JSON.stringify([...ids])); } catch { /* quota / private mode */ }
}

/** How many of `ids` haven't been seen under `key`. On the very first call for a
 *  key (no stored baseline) it records them all as seen and returns 0. */
export function countUnseen(key: string, ids: string[]): number {
  const seen = read(key);
  if (seen == null) { write(key, ids); return 0; }
  return ids.filter(id => !seen.has(id)).length;
}

/** Like {@link countUnseen}, but an id also counts as seen if any of the
 *  read-only `alsoSeenKeys` baselines already has it — so opening the global
 *  News feed (which writes its own baseline) clears a competition's badge too.
 *  Only `key` is seeded on first run; the extra keys are never written here. */
export function countUnseenExcept(key: string, alsoSeenKeys: string[], ids: string[]): number {
  const primary = read(key);
  if (primary == null) { write(key, ids); return 0; }  // first run for this feed
  const extra = alsoSeenKeys.map(read).filter((s): s is Set<string> => s != null);
  return ids.filter(id => !primary.has(id) && !extra.some(s => s.has(id))).length;
}

/** Mark exactly `ids` as seen — called when the user opens the feed. Storing the
 *  current snapshot keeps the baseline bounded to the feed size. */
export function markSeen(key: string, ids: string[]): void {
  write(key, ids);
}

const NEWS_SEEN_PREFIX = 'tla3bnySeenNews';

/** localStorage key for a news feed: the global feed, or one competition's. */
export function newsSeenKey(compId?: number | null): string {
  return compId == null ? NEWS_SEEN_PREFIX : `${NEWS_SEEN_PREFIX}:${compId}`;
}

/** Stable per-item ids for the seen-set (news rows always carry a DB id). */
export function newsIds(items: { id: number }[]): string[] {
  return items.map(n => `n${n.id}`);
}

// ── per-article "NEW" tag ────────────────────────────────────────────────────
// Individual articles the user has actually opened. Drives the per-card "NEW"
// tag: once an article is opened its tag clears. This is independent of the
// per-feed seen baseline above (which clears a whole feed's badge on open), and
// it replaces the old "published in the last 3 days" heuristic with real
// per-user read state — matching the youthscores web app.
const READ_NEWS_KEY = 'tla3bnyReadNews';

export function getReadNews(): Set<string> {
  if (typeof window === 'undefined') return new Set();
  try {
    const raw = localStorage.getItem(READ_NEWS_KEY);
    return new Set(raw ? (JSON.parse(raw) as string[]) : []);
  } catch { return new Set(); }
}

export function markNewsRead(id: number | string): void {
  try {
    const ids = getReadNews();
    if (ids.has(String(id))) return;
    ids.add(String(id));
    localStorage.setItem(READ_NEWS_KEY, JSON.stringify([...ids]));
  } catch { /* quota / private mode */ }
}

/** First run (no stored read-set): treat the whole current feed as already read,
 *  so "NEW" only tags articles that arrive *after* this point rather than
 *  lighting up the entire back-catalogue. No-op once a set exists. */
export function seedReadNewsIfFirstRun(ids: (number | string)[]): void {
  if (typeof window === 'undefined') return;
  try {
    if (localStorage.getItem(READ_NEWS_KEY) != null) return;
    localStorage.setItem(READ_NEWS_KEY, JSON.stringify(ids.map(String)));
  } catch { /* quota / private mode */ }
}
