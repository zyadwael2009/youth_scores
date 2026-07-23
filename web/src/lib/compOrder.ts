// Canonical display order for the competition families. Names are folded (alef /
// ya / ta-marbuta variants and diacritics) before matching, so a spelling
// variant still lines up. Anything not listed sorts after these, alphabetically.
const CANONICAL = [
  'دوري الجمهورية القسم الاول',
  'دوري الجمهورية القسم الثاني أ',
  'دوري الجمهورية القسم الثاني ب',
  'القطاعات',
  'المناطق',
];

const fold = (s: string) =>
  (s || '')
    .toLowerCase()
    .replace(/[ً-ْـ]/g, '')
    .replace(/[أإآٱ]/g, 'ا')
    .replace(/ى/g, 'ي')
    .replace(/ة/g, 'ه')
    .replace(/\s+/g, ' ')
    .trim();

const ORDER = CANONICAL.map(fold);

export function compRank(name: string): number {
  const i = ORDER.indexOf(fold(name));
  return i === -1 ? ORDER.length : i;
}

/** Sort competition names by the canonical order, then alphabetically. */
export function compareCompName(a: string, b: string): number {
  return compRank(a) - compRank(b) || a.localeCompare(b, 'ar');
}
