// Formation → ordered position-slot labels (GK first, then defence → attack),
// ported from the ug/ Flutter app. Rows are laid out goalkeeper (bottom) to
// forwards (top). The trailing "(7s)" formats are smaller-sided youth setups.
export const FORMATIONS: Record<string, string[]> = {
  '4-3-3': ['GK', 'LB', 'CB1', 'CB2', 'RB', 'CM1', 'CM2', 'CM3', 'LW', 'ST', 'RW'],
  '4-4-2': ['GK', 'LB', 'CB1', 'CB2', 'RB', 'LM', 'CM1', 'CM2', 'RM', 'ST1', 'ST2'],
  '3-4-3': ['GK', 'CB1', 'CB2', 'CB3', 'LM', 'CM1', 'CM2', 'RM', 'LW', 'ST', 'RW'],
  '4-2-3-1': ['GK', 'LB', 'CB1', 'CB2', 'RB', 'CDM1', 'CDM2', 'CAM', 'LW', 'RW', 'ST'],
  '3-5-2': ['GK', 'CB1', 'CB2', 'CB3', 'LM', 'CM1', 'CM2', 'CM3', 'RM', 'ST1', 'ST2'],
  '2-3-1 (7s)': ['GK', 'CB1', 'CB2', 'LM', 'CM', 'RM', 'ST'],
  '3-2-1 (7s)': ['GK', 'CB1', 'CB2', 'CB3', 'CM1', 'CM2', 'ST'],
};

export const FORMATION_NAMES = Object.keys(FORMATIONS);

/** Selectable player positions, bilingual. The stored `code` matches the base
 *  slot labels used by the pitch/lineup ({@link slotBase}), e.g. "CB"/"ST",
 *  so a player's position keeps feeding the formation-aware sort there.
 *  Offering a fixed list (instead of a free-text field) avoids typos that
 *  would break that matching. */
export const PLAYER_POSITIONS: { code: string; ar: string; en: string }[] = [
  { code: 'GK',  ar: 'حارس مرمى',       en: 'Goalkeeper' },
  { code: 'RB',  ar: 'ظهير أيمن',        en: 'Right Back' },
  { code: 'LB',  ar: 'ظهير أيسر',        en: 'Left Back' },
  { code: 'CB',  ar: 'قلب دفاع',         en: 'Centre Back' },
  { code: 'CDM', ar: 'وسط مدافع',        en: 'Defensive Midfielder' },
  { code: 'CM',  ar: 'وسط',              en: 'Central Midfielder' },
  { code: 'CAM', ar: 'صانع ألعاب',       en: 'Attacking Midfielder' },
  { code: 'RM',  ar: 'وسط أيمن',         en: 'Right Midfielder' },
  { code: 'LM',  ar: 'وسط أيسر',         en: 'Left Midfielder' },
  { code: 'RW',  ar: 'جناح أيمن',        en: 'Right Winger' },
  { code: 'LW',  ar: 'جناح أيسر',        en: 'Left Winger' },
  { code: 'ST',  ar: 'مهاجم',            en: 'Striker' },
];

/** Parse leading formation numbers, e.g. "4-2-3-1 (7s)" → [4,2,3,1]. */
export function parseFormationRows(formation: string | null | undefined): number[] {
  if (!formation) return [];
  const head = formation.split(' ')[0]; // strip "(7s)"
  return head.split('-').map(p => parseInt(p.trim(), 10)).filter(n => !isNaN(n));
}

/** Group an ordered slot list into pitch rows: [GK], then a row per number. */
export function formationRowLabels(formation: string | null | undefined): string[][] {
  const order = (formation && FORMATIONS[formation]) || [];
  const rows = parseFormationRows(formation);
  if (order.length === 0 || rows.length === 0) return [];
  const out: string[][] = [[order[0]]]; // GK
  let idx = 1;
  for (const n of rows) {
    out.push(order.slice(idx, Math.min(idx + n, order.length)));
    idx += n;
  }
  return out;
}

/** The bare position (CB1 → CB), used to suggest player-position filters. */
export function slotBase(label: string): string {
  return label.replace(/[0-9]/g, '');
}
