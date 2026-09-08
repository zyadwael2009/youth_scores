// Turn positioned OCR words into fixture rows. The table columns are fixed, so
// rather than trust the OCR's line grouping we rebuild the grid from geometry:
// cluster words into rows by Y, locate columns from the header row, then read
// each cell out of its column band. Home = the team cell nearer the date column
// (higher X in this RTL table); away = the cell nearer the venue column.

import type { OcrWord } from './ocrEngine';

export interface RawFixture {
  round: string;
  date: string; // YYYY-MM-DD, or '' if unreadable
  time: string; // HH:MM, or ''
  home: string;
  away: string;
  venue: string;
  /** Lowest confidence among the row's key cells (0..1). */
  conf: number;
  y: number;
}

export interface ReconstructResult {
  fixtures: RawFixture[];
  warnings: string[];
  orientation: 'logical' | 'visual';
  columns: Record<string, number>;
}

// ── text helpers ──────────────────────────────────────────────────────────────

const reverse = (s: string) => [...s].reverse().join('');

const AR_DIGITS = '٠١٢٣٤٥٦٧٨٩';
const FA_DIGITS = '۰۱۲۳۴۵۶۷۸۹';
function normalizeDigits(s: string): string {
  return s.replace(/[٠-٩۰-۹]/g, (d) => {
    const a = AR_DIGITS.indexOf(d);
    return String(a >= 0 ? a : FA_DIGITS.indexOf(d));
  });
}

// Fold for header-keyword matching only (not for team matching).
function foldAr(s: string): string {
  return s
    .replace(/[ً-ْـ]/g, '')
    .replace(/[أإآٱ]/g, 'ا')
    .replace(/ى/g, 'ي')
    .replace(/ة/g, 'ه')
    .replace(/\s+/g, '');
}

// Column header → keyword(s) (folded, logical order). A column may be printed
// differently between templates — e.g. the time column is «التوقيت» on one
// fixtures template and «الساعة» on another, the round column «الأسبوع» vs
// «الجولة» — so each column carries every spelling we've seen.
const HEADERS: Record<string, string[]> = {
  time: ['توقيت', 'ساعه'], // التوقيت / الساعة
  venue: ['ملعب'],
  teams: ['فريق'],
  teams2: ['تبار'], // المتباريان — same column as الفريقان
  date: ['تاريخ'],
  day: ['يوم'],
  match: ['مباراه'],
  round: ['اسبوع', 'جوله'], // الأسبوع / الجولة
};

// Day-of-week words to exclude from the name tokens (folded spellings).
const DAY_NAMES = new Set(
  ['الاحد', 'الاثنين', 'الثلاثاء', 'الاربعاء', 'الخميس', 'الجمعه', 'السبت'].map(foldAr));

// Arabic ordinal words → round number, for round columns printed as text
// («الجولة الأولى» → 1) rather than a digit. Folded spellings (foldAr collapses
// ة→ه and ى→ي), both feminine and masculine forms. Used to read the round cell
// and to keep these words out of the team/venue name tokens.
const AR_ORDINALS: Record<string, string> = {
  الاولي: '1', الاول: '1',
  الثانيه: '2', الثاني: '2',
  الثالثه: '3', الثالث: '3',
  الرابعه: '4', الرابع: '4',
  الخامسه: '5', الخامس: '5',
  السادسه: '6', السادس: '6',
  السابعه: '7', السابع: '7',
  الثامنه: '8', الثامن: '8',
  التاسعه: '9', التاسع: '9',
  العاشره: '10', العاشر: '10',
};
const ROUND_WORDS = new Set(Object.keys(AR_ORDINALS));

// ── row clustering ────────────────────────────────────────────────────────────

function clusterRows(words: OcrWord[]): OcrWord[][] {
  const sorted = [...words].sort((a, b) => a.cy - b.cy);
  const heights = sorted.map((w) => w.h).filter((h) => h > 0).sort((a, b) => a - b);
  const medH = heights.length ? heights[Math.floor(heights.length / 2)] : 16;
  const rows: OcrWord[][] = [];
  let cur: OcrWord[] = [];
  let curSum = 0; // running Σcy of the open cluster, to anchor on its mean
  for (const w of sorted) {
    // Compare to the cluster's MEAN cy, not the previous word. Chaining off the
    // last word lets a vertically-centred spanning cell (the round / date / day
    // block covers every row of a week) bridge two adjacent data rows into one
    // cluster — silently dropping one match per round. The mean stays pinned to
    // the current row, so a stray word between rows can't hop two rows together.
    if (cur.length && w.cy - curSum / cur.length > medH * 0.7) {
      rows.push(cur);
      cur = [];
      curSum = 0;
    }
    cur.push(w);
    curSum += w.cy;
  }
  if (cur.length) rows.push(cur);
  return rows;
}

// ── column detection from the header row ──────────────────────────────────────

interface Columns {
  centres: Record<string, number>;
  orientation: 'logical' | 'visual';
}

function detectColumns(headerRow: OcrWord[]): Columns {
  const centres: Record<string, number> = {};
  let visualVotes = 0, logicalVotes = 0;

  for (const w of headerRow) {
    const logical = foldAr(w.text);
    const visual = foldAr(reverse(w.text));
    for (const [col, kws] of Object.entries(HEADERS)) {
      if (kws.some(kw => logical.includes(kw))) { centres[col] = w.cx; logicalVotes++; }
      else if (kws.some(kw => visual.includes(kw))) { centres[col] = w.cx; visualVotes++; }
    }
  }
  // Merge the two "teams" header tokens into one centre.
  if (centres.teams2 != null) {
    centres.teams = centres.teams != null ? (centres.teams + centres.teams2) / 2 : centres.teams2;
    delete centres.teams2;
  }
  return { centres, orientation: visualVotes > logicalVotes ? 'visual' : 'logical' };
}

// Fallback column centres as fractions of image width (right-to-left table),
// used only if the header row can't be read.
function fallbackColumns(width: number): Record<string, number> {
  return {
    time: width * 0.15,
    venue: width * 0.29,
    teams: width * 0.52,
    date: width * 0.71,
    day: width * 0.8,
    round: width * 0.92,
  };
}

// ── cell parsers ──────────────────────────────────────────────────────────────

function parseDate(tokens: OcrWord[]): { value: string; conf: number } {
  for (const t of tokens) {
    const s = normalizeDigits(t.text);
    const m = s.match(/(\d{4})\D+(\d{1,2})\D+(\d{1,2})/);
    if (m) {
      const [, y, mo, d] = m;
      return { value: `${y}-${mo.padStart(2, '0')}-${d.padStart(2, '0')}`, conf: t.conf };
    }
  }
  return { value: '', conf: 0 };
}

function parseTime(tokens: OcrWord[]): { value: string; conf: number } {
  for (const t of tokens) {
    const s = normalizeDigits(t.text);
    const m = s.match(/(\d{1,2})\s*[.:,،]\s*(\d{2})/);
    if (m) {
      const h = m[1].padStart(2, '0');
      return { value: `${h}:${m[2]}`, conf: t.conf };
    }
  }
  return { value: '', conf: 0 };
}

// Read the round cell: a digit if the column prints numbers, else an Arabic
// ordinal word («الأولى» → "1"). Falls back to the raw text so an unrecognised
// value still surfaces for the admin. Tries both orientations for the ordinal.
function parseRound(tokens: OcrWord[]): string {
  for (const t of tokens) {
    const m = normalizeDigits(t.text).match(/\d+/);
    if (m) return m[0];
  }
  for (const t of tokens) {
    for (const cand of [foldAr(t.text), foldAr(reverse(t.text))]) {
      if (AR_ORDINALS[cand]) return AR_ORDINALS[cand];
    }
  }
  return tokens.map(t => t.text).join(' ').trim();
}

// ── main ──────────────────────────────────────────────────────────────────────

export function reconstructFixtures(words: OcrWord[], imageWidth: number): ReconstructResult {
  const warnings: string[] = [];
  const clean = words.filter((w) => w.text.trim().length > 0);
  if (clean.length === 0) return { fixtures: [], warnings: ['No text detected'], orientation: 'logical', columns: {} };

  const rows = clusterRows(clean);
  // The header isn't always the first cluster — some layouts print a faint group
  // title (e.g. «المجموعة الثانية») on its own line above it — and some templates
  // stack a federation logo + branch name + «إدارة المسابقات» above that. Pick,
  // among the first several rows, the one whose cells hit the most column
  // keywords, and read the data rows below it so the banner lines are skipped.
  let headerIdx = 0, bestHits = -1, detected: Record<string, number> = {};
  let orientation: 'logical' | 'visual' = 'logical';
  for (let i = 0; i < Math.min(8, rows.length); i++) {
    const c = detectColumns(rows[i]);
    const hits = Object.keys(c.centres).length;
    if (hits > bestHits) { bestHits = hits; headerIdx = i; detected = c.centres; orientation = c.orientation; }
  }

  let centres = detected;
  if (centres.date == null || centres.teams == null) {
    warnings.push('Header row unclear — using fallback column positions');
    centres = fallbackColumns(imageWidth);
  }
  const orient = (s: string) => (orientation === 'visual' ? reverse(s) : s);
  const venueCentre = centres.venue ?? imageWidth * 0.29;
  const teamsCentre = centres.teams ?? imageWidth * 0.52;
  // A name belongs to the venue column if its cluster sits on the venue side of
  // the venue↔teams midpoint. This is a boundary between the two DETECTED centres,
  // so it holds whichever side of the table the teams column is printed on.
  const venueBoundary = (venueCentre + teamsCentre) / 2;
  // The minimum gap that separates the two teams (the ×/result space). Wider than
  // any between-words gap inside one team name, so it tells a real pairing from a
  // lone bye team whose name happens to span several OCR tokens.
  const teamGap = imageWidth * 0.08;

  // Assign an x-position to the nearest detected column. Different templates order
  // the columns differently (teams-in-the-middle vs teams-far-right), so instead
  // of hard-coding "names live between the time and date columns" we keep only the
  // tokens whose nearest column is the teams or the venue. Everything else —
  // day-of-week names, the round column's ordinal words («الأولى»), and time cells
  // like «١٠ص» that carry an Arabic letter — is pulled to its own column and dropped.
  const classCols = (['teams', 'venue', 'date', 'day', 'time', 'round', 'match'] as const)
    .filter(k => centres[k] != null)
    .map(k => [k, centres[k] as number] as const);
  const nearestCol = (cx: number): string => {
    let best = '', bestD = Infinity;
    for (const [k, c] of classCols) { const d = Math.abs(cx - c); if (d < bestD) { bestD = d; best = k; } }
    return best;
  };

  const fixtures: RawFixture[] = [];
  let skippedIncomplete = 0;

  for (const row of rows.slice(headerIdx + 1)) {
    // Date/time/round by CONTENT, not raw position — so team words that sit close
    // to a neighbouring column aren't stolen by it (the bug that dropped home-team
    // words). The round cell is read from the tokens nearest the round column.
    const date = parseDate(row);
    const time = parseTime(row);
    const round = parseRound(row.filter(w => nearestCol(w.cx) === 'round'));

    // The team + venue names are the tokens bearing an Arabic LETTER (ء-ي, so pure
    // date/time digit cells like «٤:٠٠» or «٢٠٢٦/٩/٧» are skipped) whose nearest
    // column is the teams or the venue. Day-of-week words and round ordinals are
    // excluded by content too, so a missing header for those columns can't leak them.
    const nameToks = row.filter(w => {
      const t = w.text.trim();
      if (!(/[ء-ي]/.test(t) || /^bye?$/i.test(t))) return false; // Arabic name, or a Latin "by"/"bye" bye-marker
      const f = foldAr(w.text);
      if (DAY_NAMES.has(f) || ROUND_WORDS.has(f)) return false;
      const col = nearestCol(w.cx);
      return col === 'teams' || col === 'venue' || col === '';
    });

    // Cluster the names on real gaps, then place clusters by position: the
    // venue-side cluster is the venue, and of the two team clusters the right one
    // (read first in RTL) is away and the left one is home. Robust when the venue
    // or a team is missing.
    const { home: homeW, away: awayW, venue: venueW } = splitRow(nameToks, venueBoundary, teamGap);

    const joinRtl = (ws: OcrWord[]) =>
      ws.slice().sort((a, b) => b.cx - a.cx).map((w) => orient(w.text)).join(' ').trim();
    const homeStr = joinRtl(homeW);
    const awayStr = joinRtl(awayW);
    const venueStr = joinRtl(venueW);

    if (!homeStr && !awayStr) continue; // stray header/footer line
    // A real fixture needs BOTH sides. A row with only one team is a bye (the
    // resting team in an odd-sized group, printed alone with a "B" marker that the
    // scanner usually can't read) or an unrecoverable half-read — either way it
    // can't become a match, so drop it and note the count rather than emit a
    // broken half-row for every bye.
    if (!homeStr || !awayStr) { skippedIncomplete++; continue; }

    const confs = [date.conf, time.conf, ...homeW.map(w => w.conf), ...awayW.map(w => w.conf)].filter(c => c > 0);
    const conf = confs.length ? Math.min(...confs) : 0;

    fixtures.push({ round, date: date.value, time: time.value, home: homeStr, away: awayStr, venue: venueStr, conf, y: row[0].cy });
  }

  if (skippedIncomplete > 0) {
    warnings.push(`تم تخطّي ${skippedIncomplete} صفًّا بفريق واحد فقط (غالبًا مباراة راحة «باي»).`);
  }
  return { fixtures, warnings, orientation, columns: centres };
}

// Split a row's name tokens into home / away / venue. The venue sits on its own
// side of the venue↔teams boundary; the two teams share the pairings column.
// Rather than cluster on a fixed gap (which over-splits a long 4-word team name
// like «الاتحاد الرياضى بركة السبع» into two "teams" and mis-pairs it), we take
// ALL team-side tokens and cut them at their single LARGEST gap: that gap is the
// ×/result space between the two sides, while the smaller gaps are the spaces
// between the words of one name. The right group (read first in RTL) is the home
// side, the left group the away side.
function splitRow(
  toks: OcrWord[], venueBoundary: number, teamGap: number,
): { home: OcrWord[]; away: OcrWord[]; venue: OcrWord[] } {
  const venue = toks.filter(w => w.cx < venueBoundary);
  const teamToks = toks.filter(w => w.cx >= venueBoundary).sort((a, b) => b.cx - a.cx); // right → left
  if (teamToks.length <= 1) return { home: teamToks, away: [], venue }; // a lone team = bye/half-read
  let splitAt = 1, maxGap = -1;
  for (let i = 1; i < teamToks.length; i++) {
    const gap = teamToks[i - 1].cx - teamToks[i].cx;
    if (gap > maxGap) { maxGap = gap; splitAt = i; }
  }
  // If even the biggest gap is small, every token is a word of ONE name — a lone
  // resting team on a bye row whose name spans several tokens, not two teams. The
  // ×/result space between two real sides is much wider than a between-words gap.
  if (maxGap < teamGap) return { home: teamToks, away: [], venue };
  const home = teamToks.slice(0, splitAt);
  const away = teamToks.slice(splitAt);
  return { home, away, venue };
}
