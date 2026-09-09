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
