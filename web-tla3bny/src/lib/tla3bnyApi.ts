// tla3bny (LeagueHub subdomain) API client — talks to the Flask /api/tla3bny
// endpoints. Reads are public; writes carry the tla3bny bearer token, which is
// separate from the youthscores admin token.

const API_ORIGIN = (
  process.env.NEXT_PUBLIC_CONFIG_URL ?? 'https://tla3bny.youthscores.org/api/config'
).replace(/\/api\/config\/?$/, '');

export const T_BASE = `${API_ORIGIN}/api/tla3bny`;

/** Absolute URL for an uploaded asset stored as `uploads/<name>`. */
export function mediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (/^https?:\/\//.test(path)) return path;
  return `${API_ORIGIN}/${path.replace(/^\/+/, '')}`;
}

// ── types ───────────────────────────────────────────────────────────────────
export type TRole = 'super_admin' | 'academy';
export type TUserStatus = 'active' | 'pending' | 'approved' | 'rejected';
export type TPlayerStatus = 'pending' | 'approved' | 'rejected';
export type TMatchStatus = 'scheduled' | 'live' | 'finished';

export interface TUser {
  id: number;
  name: string | null;
  logo_path: string | null;
  role: TRole;
  status: TUserStatus;
  email?: string;
  phone?: string | null;
  address?: string | null;
  rejection_reason?: string | null;
  created_at?: string;
  player_count?: number;
}

export interface TCategory {
  id: number;
  label: string;
  required_files: number;
}

export interface TPlayerFile {
  id: number;
  file_path: string;
  original_name: string | null;
}

export interface TPlayer {
  id: number;
  academy_id: number;
  academy_name: string | null;
  age_category_id: number | null;
  age_category: string | null;
  name: string;
  position: string | null;
  sub_position: string | null;
  dob: string | null;
  jersey_number: number | null;
  photo_path: string | null;
  papers_path: string | null;
  status: TPlayerStatus;
  rejection_reason: string | null;
  files: TPlayerFile[];
  file_count: number;
  required_files: number;
}

export interface TMatchEvent {
  id: number;
  match_id: number;
  player_id: number | null;
  player_name: string | null;
  jersey_number: number | null;
  team_academy_id: number | null;
  event_type: 'goal' | 'assist' | 'yellow' | 'red' | 'substitution_in' | 'substitution_out';
  minute: number | null;
  related_event_id: number | null;
}

export interface TMatch {
  id: number;
  home_academy_id: number;
  away_academy_id: number;
  home_academy_name: string | null;
  away_academy_name: string | null;
  home_academy_logo: string | null;
  away_academy_logo: string | null;
  age_category_id: number;
  age_category: string | null;
  date: string | null;
  time: string | null;
  venue: string | null;
  duration_minutes: number;
  num_periods: number;
  max_substitutions: number;
  status: TMatchStatus;
  home_score: number | null;
  away_score: number | null;
  events?: TMatchEvent[];
}

export interface TStandingRow {
  academy_id: number;
  academy_name: string | null;
  logo_path: string | null;
  P: number; W: number; D: number; L: number;
  GF: number; GA: number; GD: number; Pts: number;
  form: ('W' | 'D' | 'L')[];
  rank: number;
}

export interface TPlayerBoardRow {
  player_id: number;
  player_name: string;
  academy_id: number;
  academy_name: string | null;
  photo_path: string | null;
  count: number;
}
export interface TCleanSheetRow {
  academy_id: number;
  academy_name: string | null;
  logo_path: string | null;
  count: number;
}
export interface TAnalysis {
  top_scorers: TPlayerBoardRow[];
  top_assisters: TPlayerBoardRow[];
  clean_sheets: TCleanSheetRow[];
  yellow_cards: TPlayerBoardRow[];
  red_cards: TPlayerBoardRow[];
}

export interface TLineupSlot {
  id: number;
  lineup_id: number;
  position_slot: string | null;
  player_id: number | null;
  player_name: string | null;
  jersey_number: number | null;
  photo_path: string | null;
  is_substitute: boolean;
}
export interface TLineup {
  id: number;
  match_id: number;
  academy_id: number;
  academy_name: string | null;
  formation: string | null;
  slots: TLineupSlot[];
}

// ── fetch helpers ───────────────────────────────────────────────────────────
function authHeaders(token?: string | null, json = false): HeadersInit {
  const h: Record<string, string> = {};
  if (json) h['Content-Type'] = 'application/json';
  if (token) h['Authorization'] = `Bearer ${token}`;
  return h;
}

async function parse<T>(res: Response): Promise<T> {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error((data as { error?: string }).error || `خطأ (${res.status})`);
  return data as T;
}

const get = <T,>(path: string, token?: string | null) =>
  fetch(`${T_BASE}${path}`, { headers: authHeaders(token), cache: 'no-store' }).then(r => parse<T>(r));
const send = <T,>(method: string, path: string, body?: unknown, token?: string | null) =>
  fetch(`${T_BASE}${path}`, {
    method,
    headers: authHeaders(token, true),
    body: body != null ? JSON.stringify(body) : undefined,
  }).then(r => parse<T>(r));

// ── auth ────────────────────────────────────────────────────────────────────
export const tLogin = (email: string, password: string) =>
  send<{ token: string; user: TUser }>('POST', '/auth/login', { email, password });

export function tRegister(fd: {
  name: string; email: string; password: string; phone?: string; address?: string; logo?: File | null;
}) {
  const body = new FormData();
  body.append('name', fd.name);
  body.append('email', fd.email);
  body.append('password', fd.password);
  if (fd.phone) body.append('phone', fd.phone);
  if (fd.address) body.append('address', fd.address);
  if (fd.logo) body.append('logo', fd.logo);
  return fetch(`${T_BASE}/auth/register`, { method: 'POST', body }).then(
    r => parse<{ message: string; token: string; user: TUser }>(r),
  );
}

export const tMe = (token: string) =>
  get<{ user: TUser }>('/auth/me', token).then(d => d.user).catch(() => null);

// ── categories ──────────────────────────────────────────────────────────────
export const tCategories = () => get<TCategory[]>('/categories');
export const tCreateCategory = (token: string, b: { label: string; required_files?: number }) =>
  send<TCategory>('POST', '/categories', b, token);
export const tUpdateCategory = (token: string, id: number, b: Record<string, unknown>) =>
  send<TCategory>('PUT', `/categories/${id}`, b, token);
export const tDeleteCategory = (token: string, id: number) =>
  send<{ message: string }>('DELETE', `/categories/${id}`, undefined, token);

// ── academies ───────────────────────────────────────────────────────────────
export const tAcademies = () => get<TUser[]>('/academies');
export const tManageAcademies = (token: string, status?: string) =>
  get<TUser[]>(`/academies/manage${status ? `?status=${status}` : ''}`, token);
export const tApproveAcademy = (token: string, id: number) =>
  send<TUser>('POST', `/academies/${id}/approve`, undefined, token);
export const tRejectAcademy = (token: string, id: number, reason?: string) =>
  send<TUser>('POST', `/academies/${id}/reject`, { reason }, token);
export const tSuspendAcademy = (token: string, id: number) =>
  send<TUser>('POST', `/academies/${id}/suspend`, undefined, token);

export function tUpdateProfile(token: string, fd: {
  name?: string; phone?: string; address?: string; logo?: File | null;
}) {
  const body = new FormData();
  if (fd.name != null) body.append('name', fd.name);
  if (fd.phone != null) body.append('phone', fd.phone);
  if (fd.address != null) body.append('address', fd.address);
  if (fd.logo) body.append('logo', fd.logo);
  return fetch(`${T_BASE}/academies/me`, {
    method: 'PUT', headers: authHeaders(token), body,
  }).then(r => parse<TUser>(r));
}

// ── players ─────────────────────────────────────────────────────────────────
export const tPlayers = (params: { academy_id?: number; age_category_id?: number; status?: string } = {}) => {
  const q = new URLSearchParams();
  if (params.academy_id) q.set('academy_id', String(params.academy_id));
  if (params.age_category_id) q.set('age_category_id', String(params.age_category_id));
  if (params.status) q.set('status', params.status);
  const qs = q.toString();
  return get<TPlayer[]>(`/players${qs ? `?${qs}` : ''}`);
};
export const tMyPlayers = (token: string) => get<TPlayer[]>('/players/mine', token);
export const tManagePlayers = (token: string, status?: string) =>
  get<TPlayer[]>(`/players/manage${status ? `?status=${status}` : ''}`, token);
export const tPlayer = (id: number) => get<TPlayer>(`/players/${id}`);

export function tSavePlayer(
  token: string,
  fd: Record<string, string | number | null | undefined>,
  photo?: File | null,
  documents?: File[],
  id?: number,
) {
  const body = new FormData();
  Object.entries(fd).forEach(([k, v]) => { if (v != null && v !== '') body.append(k, String(v)); });
  if (photo) body.append('photo', photo);
  (documents ?? []).forEach(f => body.append('documents', f));
  return fetch(`${T_BASE}/players${id ? `/${id}` : ''}`, {
    method: id ? 'PUT' : 'POST', headers: authHeaders(token), body,
  }).then(r => parse<TPlayer>(r));
}
export const tDeletePlayer = (token: string, id: number) =>
  send<{ message: string }>('DELETE', `/players/${id}`, undefined, token);
export const tApprovePlayer = (token: string, id: number) =>
  send<TPlayer>('POST', `/players/${id}/approve`, undefined, token);
export const tRejectPlayer = (token: string, id: number, reason?: string) =>
  send<TPlayer>('POST', `/players/${id}/reject`, { reason }, token);

// ── matches ─────────────────────────────────────────────────────────────────
export const tMatches = (params: { age_category_id?: number; status?: string; academy_id?: number } = {}) => {
  const q = new URLSearchParams();
  if (params.age_category_id) q.set('age_category_id', String(params.age_category_id));
  if (params.status) q.set('status', params.status);
  if (params.academy_id) q.set('academy_id', String(params.academy_id));
  const qs = q.toString();
  return get<TMatch[]>(`/matches${qs ? `?${qs}` : ''}`);
};
export const tMatch = (id: number) => get<TMatch>(`/matches/${id}`);
export const tCreateMatch = (token: string, b: Record<string, unknown>) =>
  send<TMatch>('POST', '/matches', b, token);
export const tUpdateMatch = (token: string, id: number, b: Record<string, unknown>) =>
  send<TMatch>('PUT', `/matches/${id}`, b, token);
export const tDeleteMatch = (token: string, id: number) =>
  send<{ message: string }>('DELETE', `/matches/${id}`, undefined, token);
export const tEnterResult = (token: string, id: number, b: Record<string, unknown>) =>
  send<TMatch>('POST', `/matches/${id}/result`, b, token);

// ── lineups ─────────────────────────────────────────────────────────────────
export const tMatchLineups = (matchId: number) => get<TLineup[]>(`/lineups/match/${matchId}`);
export const tSaveLineup = (token: string, matchId: number, academyId: number, b: Record<string, unknown>) =>
  send<TLineup>('PUT', `/lineups/match/${matchId}/academy/${academyId}`, b, token);

// ── standings / analysis ────────────────────────────────────────────────────
export const tStandings = (categoryId: number) =>
  get<TStandingRow[]>(`/standings?age_category_id=${categoryId}`);
export const tAnalysis = (categoryId: number) =>
  get<TAnalysis>(`/analysis?age_category_id=${categoryId}`);
