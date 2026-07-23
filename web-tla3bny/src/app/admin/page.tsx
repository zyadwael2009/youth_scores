'use client';
import { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useTla3bnyAuth } from '@/context/Tla3bnyAuthContext';
import {
  tManageAcademies, tApproveAcademy, tRejectAcademy, tSuspendAcademy,
  tManagePlayers, tApprovePlayer, tRejectPlayer,
  tCategories, tCreateCategory, tUpdateCategory, tDeleteCategory,
  tMatches, tCreateMatch, tDeleteMatch, tEnterResult, tAcademies, tPlayers,
  mediaUrl,
  type TUser, type TPlayer, type TCategory, type TMatch,
} from '@/lib/tla3bnyApi';
import Spinner from '@/components/ui/Spinner';
import {
  Card, Field, inputCls, PrimaryButton, ErrorNote, EmptyState,
  LogoAvatar, StatusBadge, useTT,
} from '@/components/tla3bny/kit';

type Tab = 'academies' | 'players' | 'categories' | 'matches';

export default function AdminPage() {
  const tt = useTT();
  const router = useRouter();
  const { user, token, loading, isSuperAdmin } = useTla3bnyAuth();
  const [tab, setTab] = useState<Tab>('academies');

  useEffect(() => {
    if (loading) return;
    if (!user) { router.replace('/login'); return; }
    if (!isSuperAdmin) { router.replace('/dashboard'); return; }
  }, [loading, user, isSuperAdmin, router]);

  if (loading || !user || !isSuperAdmin || !token) return <Spinner />;

  const tabs: { k: Tab; label: string }[] = [
    { k: 'academies', label: tt('الأكاديميات', 'Academies') },
    { k: 'players', label: tt('اللاعبون', 'Players') },
    { k: 'categories', label: tt('الفئات', 'Categories') },
    { k: 'matches', label: tt('المباريات', 'Matches') },
  ];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-black text-text">{tt('لوحة إدارة الدوري', 'League admin')}</h1>
      <div className="flex items-center gap-1 overflow-x-auto no-scrollbar border-b border-bdr">
        {tabs.map(t => (
          <button key={t.k} onClick={() => setTab(t.k)}
            className={`px-4 py-2 text-sm font-bold whitespace-nowrap border-b-2 -mb-px transition-colors ${
              tab === t.k ? 'border-aqua text-aqua' : 'border-transparent text-hint hover:text-teal'
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'academies' && <AcademiesTab token={token} />}
      {tab === 'players' && <PlayersTab token={token} />}
      {tab === 'categories' && <CategoriesTab token={token} />}
      {tab === 'matches' && <MatchesTab token={token} />}
    </div>
  );
}

// ── Academies ────────────────────────────────────────────────────────────────
function AcademiesTab({ token }: { token: string }) {
  const tt = useTT();
  const [status, setStatus] = useState('pending');
  const [items, setItems] = useState<TUser[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    tManageAcademies(token, status || undefined).then(setItems).catch(() => setItems([])).finally(() => setLoading(false));
  }, [token, status]);
  useEffect(load, [load]);

  const filters = [
    { k: 'pending', label: tt('قيد المراجعة', 'Pending') },
    { k: 'approved', label: tt('معتمدة', 'Approved') },
    { k: 'rejected', label: tt('مرفوضة', 'Rejected') },
    { k: '', label: tt('الكل', 'All') },
  ];

  const act = async (fn: Promise<unknown>) => { await fn; load(); };

  return (
    <div className="space-y-3">
      <FilterChips options={filters} value={status} onChange={setStatus} />
      {loading ? <Spinner /> :
        items.length === 0 ? <EmptyState icon="🏫" text={tt('لا توجد أكاديميات', 'No academies')} /> :
        items.map(a => (
          <Card key={a.id} className="p-3">
            <div className="flex items-center gap-3">
              <LogoAvatar src={a.logo_path} name={a.name} size={44} />
              <div className="min-w-0 flex-1">
                <div className="font-bold text-text text-sm truncate">{a.name}</div>
                <div className="text-[11px] text-hint truncate">{a.email} · {a.phone || '—'}</div>
              </div>
              <StatusBadge status={a.status} />
            </div>
            <div className="flex items-center gap-2 mt-2 pt-2 border-t border-bdr/50">
              {a.status !== 'approved' && <ActBtn label={tt('اعتماد', 'Approve')} tone="win" onClick={() => act(tApproveAcademy(token, a.id))} />}
              {a.status !== 'rejected' && <ActBtn label={tt('رفض', 'Reject')} tone="loss" onClick={() => { const r = prompt(tt('سبب الرفض؟', 'Rejection reason?')) ?? undefined; act(tRejectAcademy(token, a.id, r)); }} />}
              {a.status === 'approved' && <ActBtn label={tt('تعليق', 'Suspend')} tone="gold" onClick={() => act(tSuspendAcademy(token, a.id))} />}
            </div>
          </Card>
        ))}
    </div>
  );
}

// ── Players verification ─────────────────────────────────────────────────────
function PlayersTab({ token }: { token: string }) {
  const tt = useTT();
  const [status, setStatus] = useState('pending');
  const [items, setItems] = useState<TPlayer[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    tManagePlayers(token, status || undefined).then(setItems).catch(() => setItems([])).finally(() => setLoading(false));
  }, [token, status]);
  useEffect(load, [load]);

  const filters = [
    { k: 'pending', label: tt('قيد المراجعة', 'Pending') },
    { k: 'approved', label: tt('معتمد', 'Approved') },
    { k: 'rejected', label: tt('مرفوض', 'Rejected') },
    { k: '', label: tt('الكل', 'All') },
  ];
  const act = async (fn: Promise<unknown>) => { await fn; load(); };

  return (
    <div className="space-y-3">
      <FilterChips options={filters} value={status} onChange={setStatus} />
      {loading ? <Spinner /> :
        items.length === 0 ? <EmptyState icon="👥" text={tt('لا يوجد لاعبون', 'No players')} /> :
        items.map(p => (
          <Card key={p.id} className="p-3">
            <div className="flex items-center gap-3">
              <LogoAvatar src={p.photo_path} name={p.name} size={44} />
              <div className="min-w-0 flex-1">
                <div className="font-bold text-text text-sm truncate">{p.name} {p.jersey_number != null && <span className="text-aqua text-xs">#{p.jersey_number}</span>}</div>
                <div className="text-[11px] text-hint truncate">{p.academy_name} · U{p.age_category ?? '—'} · {p.sub_position || '—'}</div>
              </div>
              <StatusBadge status={p.status} />
            </div>
            {p.files.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-2">
                {p.files.map(f => (
                  <a key={f.id} href={mediaUrl(f.file_path) ?? '#'} target="_blank" rel="noreferrer"
                    className="text-[11px] font-bold text-aqua bg-aqua/10 border border-aqua/30 rounded px-2 py-0.5 hover:bg-aqua/20">
                    📄 {f.original_name || tt('مستند', 'doc')}
                  </a>
                ))}
              </div>
            )}
            <div className="flex items-center gap-2 mt-2 pt-2 border-t border-bdr/50">
              <span className="text-[11px] text-hint">{tt('المستندات', 'Docs')}: {p.file_count}/{p.required_files}</span>
              <div className="flex-1" />
              {p.status !== 'approved' && <ActBtn label={tt('اعتماد', 'Approve')} tone="win" onClick={() => act(tApprovePlayer(token, p.id))} />}
              {p.status !== 'rejected' && <ActBtn label={tt('رفض', 'Reject')} tone="loss" onClick={() => { const r = prompt(tt('سبب الرفض؟', 'Rejection reason?')) ?? undefined; act(tRejectPlayer(token, p.id, r)); }} />}
            </div>
          </Card>
        ))}
    </div>
  );
}

// ── Categories ───────────────────────────────────────────────────────────────
function CategoriesTab({ token }: { token: string }) {
  const tt = useTT();
  const [items, setItems] = useState<TCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [label, setLabel] = useState('');
  const [reqFiles, setReqFiles] = useState(1);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    tCategories().then(setItems).catch(() => setItems([])).finally(() => setLoading(false));
  }, []);
  useEffect(load, [load]);

  const add = async (e: React.FormEvent) => {
    e.preventDefault(); setErr(null);
    try { await tCreateCategory(token, { label: label.trim(), required_files: reqFiles }); setLabel(''); setReqFiles(1); load(); }
    catch (e2) { setErr(e2 instanceof Error ? e2.message : String(e2)); }
  };

  return (
    <div className="space-y-3">
      <Card className="p-4">
        <form onSubmit={add} className="flex items-end gap-2 flex-wrap">
          <div className="flex-1 min-w-[120px]"><Field label={tt('الفئة (سنة الميلاد)', 'Label (birth year)')}><input value={label} onChange={e => setLabel(e.target.value)} placeholder="2012" className={inputCls} /></Field></div>
          <div className="w-28"><Field label={tt('عدد المستندات', 'Req. files')}><input type="number" min={0} value={reqFiles} onChange={e => setReqFiles(Number(e.target.value))} className={inputCls} /></Field></div>
          <PrimaryButton type="submit" disabled={!label.trim()}>{tt('إضافة', 'Add')}</PrimaryButton>
        </form>
        <ErrorNote>{err}</ErrorNote>
      </Card>
      {loading ? <Spinner /> :
        items.length === 0 ? <EmptyState icon="🗂️" text={tt('لا توجد فئات', 'No categories')} /> :
        items.map(c => (
          <Card key={c.id} className="p-3 flex items-center gap-3">
            <span className="font-black text-text">U{c.label}</span>
            <span className="text-[11px] text-hint flex-1">{tt('مستندات مطلوبة', 'Required docs')}: {c.required_files}</span>
            <button onClick={async () => { const l = prompt(tt('التسمية', 'Label'), c.label); if (l) { await tUpdateCategory(token, c.id, { label: l }); load(); } }} className="text-xs font-bold text-teal hover:text-aqua">{tt('تعديل', 'Edit')}</button>
            <button onClick={async () => { if (confirm(tt('حذف الفئة؟', 'Delete category?'))) { await tDeleteCategory(token, c.id); load(); } }} className="text-xs font-bold text-hint hover:text-loss">{tt('حذف', 'Delete')}</button>
          </Card>
        ))}
    </div>
  );
}

// ── Matches ──────────────────────────────────────────────────────────────────
function MatchesTab({ token }: { token: string }) {
  const tt = useTT();
  const [matches, setMatches] = useState<TMatch[]>([]);
  const [cats, setCats] = useState<TCategory[]>([]);
  const [academies, setAcademies] = useState<TUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [resultFor, setResultFor] = useState<TMatch | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    tMatches().then(setMatches).catch(() => setMatches([])).finally(() => setLoading(false));
  }, []);
  useEffect(() => {
    tCategories().then(setCats).catch(() => {});
    tAcademies().then(setAcademies).catch(() => {});
  }, []);
  useEffect(load, [load]);

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        {!showCreate && <PrimaryButton onClick={() => setShowCreate(true)} className="py-2 px-4 text-sm">+ {tt('مباراة', 'Match')}</PrimaryButton>}
      </div>
      {showCreate && (
        <CreateMatchForm token={token} cats={cats} academies={academies}
          onDone={() => { setShowCreate(false); load(); }} onCancel={() => setShowCreate(false)} />
      )}
      {loading ? <Spinner /> :
        matches.length === 0 ? <EmptyState icon="⚽" text={tt('لا توجد مباريات', 'No matches')} /> :
        matches.map(m => (
          <Card key={m.id} className="p-3">
            <div className="flex items-center justify-between text-[11px] text-hint mb-1.5">
              <span className="font-bold text-teal">U{m.age_category} · {m.date || tt('غير محدد', 'TBD')} {m.time || ''}</span>
              <StatusBadge status={m.status} />
            </div>
            <div className="flex items-center justify-between gap-2">
              <span className="font-bold text-text text-sm truncate flex-1 text-end">{m.home_academy_name}</span>
              <span className="font-black text-text tnum px-2">{m.status === 'finished' ? `${m.home_score ?? 0} - ${m.away_score ?? 0}` : tt('ضد', 'vs')}</span>
              <span className="font-bold text-text text-sm truncate flex-1">{m.away_academy_name}</span>
            </div>
            <div className="flex items-center gap-2 mt-2 pt-2 border-t border-bdr/50">
              <ActBtn label={tt('إدخال النتيجة', 'Enter result')} tone="win" onClick={() => setResultFor(m)} />
              <Link href={`/match/?id=${m.id}`} className="text-xs font-bold px-3 py-1.5 rounded-lg border border-aqua/40 text-aqua hover:bg-aqua/10 transition-colors">{tt('التشكيلات', 'Lineups')}</Link>
              <div className="flex-1" />
              <button onClick={async () => { if (confirm(tt('حذف المباراة؟', 'Delete match?'))) { await tDeleteMatch(token, m.id); load(); } }} className="text-xs font-bold text-hint hover:text-loss">{tt('حذف', 'Delete')}</button>
            </div>
          </Card>
        ))}

      {resultFor && (
        <ResultModal token={token} match={resultFor}
          onDone={() => { setResultFor(null); load(); }} onClose={() => setResultFor(null)} />
      )}
    </div>
  );
}

function CreateMatchForm({
  token, cats, academies, onDone, onCancel,
}: {
  token: string; cats: TCategory[]; academies: TUser[];
  onDone: () => void; onCancel: () => void;
}) {
  const tt = useTT();
  const [f, setF] = useState({
    home_academy_id: '', away_academy_id: '', age_category_id: cats[0]?.id ?? '',
    date: '', time: '', venue: '', duration_minutes: 60, num_periods: 2, max_substitutions: 5,
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const upd = (k: keyof typeof f, v: string | number) => setF({ ...f, [k]: v });

  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setErr(null);
    try {
      await tCreateMatch(token, {
        home_academy_id: Number(f.home_academy_id), away_academy_id: Number(f.away_academy_id),
        age_category_id: Number(f.age_category_id), date: f.date || null, time: f.time || null,
        venue: f.venue || null, duration_minutes: f.duration_minutes, num_periods: f.num_periods,
        max_substitutions: f.max_substitutions,
      });
      onDone();
    } catch (e2) { setErr(e2 instanceof Error ? e2.message : String(e2)); }
    finally { setBusy(false); }
  };

  return (
    <Card className="p-4">
      <form onSubmit={submit} className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <Field label={tt('الفريق المضيف', 'Home')}>
            <select value={f.home_academy_id} onChange={e => upd('home_academy_id', e.target.value)} className={inputCls}>
              <option value="">—</option>
              {academies.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </Field>
          <Field label={tt('الفريق الضيف', 'Away')}>
            <select value={f.away_academy_id} onChange={e => upd('away_academy_id', e.target.value)} className={inputCls}>
              <option value="">—</option>
              {academies.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </Field>
          <Field label={tt('الفئة', 'Category')}>
            <select value={f.age_category_id} onChange={e => upd('age_category_id', Number(e.target.value))} className={inputCls}>
              {cats.map(c => <option key={c.id} value={c.id}>U{c.label}</option>)}
            </select>
          </Field>
          <Field label={tt('الملعب', 'Venue')}><input value={f.venue} onChange={e => upd('venue', e.target.value)} className={inputCls} /></Field>
          <Field label={tt('التاريخ', 'Date')}><input type="date" value={f.date} onChange={e => upd('date', e.target.value)} className={inputCls} /></Field>
          <Field label={tt('الوقت', 'Time')}><input type="time" value={f.time} onChange={e => upd('time', e.target.value)} className={inputCls} /></Field>
          <Field label={tt('مدة المباراة (دقيقة)', 'Duration (min)')}><input type="number" value={f.duration_minutes} onChange={e => upd('duration_minutes', Number(e.target.value))} className={inputCls} /></Field>
          <Field label={tt('عدد الأشواط', 'Periods')}><input type="number" value={f.num_periods} onChange={e => upd('num_periods', Number(e.target.value))} className={inputCls} /></Field>
          <Field label={tt('أقصى تبديلات', 'Max subs')}><input type="number" value={f.max_substitutions} onChange={e => upd('max_substitutions', Number(e.target.value))} className={inputCls} /></Field>
        </div>
        <ErrorNote>{err}</ErrorNote>
        <div className="flex items-center gap-2">
          <PrimaryButton type="submit" disabled={busy || !f.home_academy_id || !f.away_academy_id}>{busy ? tt('جارٍ…', 'Saving…') : tt('إنشاء', 'Create')}</PrimaryButton>
          <button type="button" onClick={onCancel} className="text-sm text-hint hover:text-text px-3 py-2">{tt('إلغاء', 'Cancel')}</button>
        </div>
      </form>
    </Card>
  );
}

// ── Result entry ─────────────────────────────────────────────────────────────
interface DraftEvent {
  temp_id: string;
  event_type: 'goal' | 'assist' | 'yellow' | 'red';
  team_academy_id: number;
  player_id: number | '';
  minute: number | '';
  related_temp_id?: string;
}

function ResultModal({
  token, match, onDone, onClose,
}: {
  token: string; match: TMatch; onDone: () => void; onClose: () => void;
}) {
  const tt = useTT();
  const [homeScore, setHomeScore] = useState(match.home_score ?? 0);
  const [awayScore, setAwayScore] = useState(match.away_score ?? 0);
  const [events, setEvents] = useState<DraftEvent[]>([]);
  const [rosters, setRosters] = useState<Record<number, TPlayer[]>>({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      tPlayers({ academy_id: match.home_academy_id }),
      tPlayers({ academy_id: match.away_academy_id }),
    ]).then(([h, a]) => setRosters({ [match.home_academy_id]: h, [match.away_academy_id]: a })).catch(() => {});
  }, [match]);

  const addEvent = (type: DraftEvent['event_type']) =>
    setEvents(es => [...es, { temp_id: `e${Date.now()}${es.length}`, event_type: type, team_academy_id: match.home_academy_id, player_id: '', minute: '' }]);
  const updEvent = (i: number, patch: Partial<DraftEvent>) =>
    setEvents(es => es.map((e, idx) => idx === i ? { ...e, ...patch } : e));
  const removeEvent = (i: number) => setEvents(es => es.filter((_, idx) => idx !== i));

  const goals = events.filter(e => e.event_type === 'goal');

  const submit = async () => {
    setBusy(true); setErr(null);
    try {
      await tEnterResult(token, match.id, {
        home_score: homeScore, away_score: awayScore,
        events: events.map(e => ({
          event_type: e.event_type,
          team_academy_id: e.team_academy_id,
          player_id: e.player_id || null,
          minute: e.minute === '' ? null : e.minute,
          temp_id: e.temp_id,
          related_temp_id: e.related_temp_id,
        })),
      });
      onDone();
    } catch (e2) { setErr(e2 instanceof Error ? e2.message : String(e2)); }
    finally { setBusy(false); }
  };

  const teamOptions = [
    { id: match.home_academy_id, name: match.home_academy_name },
    { id: match.away_academy_id, name: match.away_academy_name },
  ];
  const evLabel = { goal: tt('هدف', 'Goal'), assist: tt('صناعة', 'Assist'), yellow: tt('صفراء', 'Yellow'), red: tt('حمراء', 'Red') };

  return (
    <div className="fixed inset-0 z-[110] bg-black/60 grid place-items-center p-3 overflow-y-auto" onClick={onClose}>
      <Card className="w-full max-w-lg p-4 my-8" >
        <div onClick={e => e.stopPropagation()}>
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-black text-text">{tt('إدخال النتيجة', 'Enter result')}</h3>
            <button onClick={onClose} className="text-hint hover:text-loss text-xl leading-none">×</button>
          </div>

          <div className="flex items-center justify-center gap-3 mb-4">
            <span className="text-sm font-bold text-text truncate max-w-[35%] text-end">{match.home_academy_name}</span>
            <input type="number" value={homeScore} onChange={e => setHomeScore(Number(e.target.value))} className={`${inputCls} w-16 text-center`} />
            <span className="text-hint">-</span>
            <input type="number" value={awayScore} onChange={e => setAwayScore(Number(e.target.value))} className={`${inputCls} w-16 text-center`} />
            <span className="text-sm font-bold text-text truncate max-w-[35%]">{match.away_academy_name}</span>
          </div>

          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs text-hint">{tt('أضف حدثًا:', 'Add:')}</span>
            {(['goal', 'assist', 'yellow', 'red'] as const).map(t => (
              <button key={t} onClick={() => addEvent(t)} className="text-xs font-bold px-2.5 py-1 rounded-lg bg-cardBg2 border border-bdr text-teal hover:border-aqua">
                + {evLabel[t]}
              </button>
            ))}
          </div>

          <div className="space-y-2 max-h-[40vh] overflow-y-auto">
            {events.map((e, i) => {
              const roster = rosters[e.team_academy_id] ?? [];
              return (
                <div key={e.temp_id} className="grid grid-cols-[auto_1fr_1fr_auto_auto] items-center gap-1.5 bg-cardBg2/60 rounded-lg p-2">
                  <span className="text-[11px] font-bold text-aqua w-12">{evLabel[e.event_type]}</span>
                  <select value={e.team_academy_id} onChange={ev => updEvent(i, { team_academy_id: Number(ev.target.value), player_id: '' })} className={`${inputCls} py-1.5 text-xs`}>
                    {teamOptions.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                  </select>
                  <select value={e.player_id} onChange={ev => updEvent(i, { player_id: ev.target.value ? Number(ev.target.value) : '' })} className={`${inputCls} py-1.5 text-xs`}>
                    <option value="">{tt('لاعب', 'Player')}</option>
                    {roster.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                  <input type="number" placeholder="′" value={e.minute} onChange={ev => updEvent(i, { minute: ev.target.value === '' ? '' : Number(ev.target.value) })} className={`${inputCls} py-1.5 w-12 text-xs text-center`} />
                  <button onClick={() => removeEvent(i)} className="text-hint hover:text-loss px-1">×</button>
                  {e.event_type === 'assist' && (
                    <select value={e.related_temp_id ?? ''} onChange={ev => updEvent(i, { related_temp_id: ev.target.value || undefined })} className={`${inputCls} py-1.5 text-xs col-span-5`}>
                      <option value="">{tt('اربط بهدف…', 'Link to goal…')}</option>
                      {goals.map((g, gi) => {
                        const gp = (rosters[g.team_academy_id] ?? []).find(p => p.id === g.player_id);
                        return <option key={g.temp_id} value={g.temp_id}>{tt('هدف', 'Goal')} {gi + 1}{gp ? ` · ${gp.name}` : ''}</option>;
                      })}
                    </select>
                  )}
                </div>
              );
            })}
          </div>

          <ErrorNote>{err}</ErrorNote>
          <div className="flex items-center gap-2 mt-3">
            <PrimaryButton onClick={submit} disabled={busy}>{busy ? tt('جارٍ الحفظ…', 'Saving…') : tt('حفظ النتيجة', 'Save result')}</PrimaryButton>
            <button onClick={onClose} className="text-sm text-hint hover:text-text px-3 py-2">{tt('إلغاء', 'Cancel')}</button>
            <span className="text-[11px] text-hint">{tt('سيتم وضع الحالة "انتهت".', 'Match will be marked finished.')}</span>
          </div>
        </div>
      </Card>
    </div>
  );
}

// ── shared bits ──────────────────────────────────────────────────────────────
function FilterChips({ options, value, onChange }: { options: { k: string; label: string }[]; value: string; onChange: (v: string) => void }) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
      {options.map(o => (
        <button key={o.k} onClick={() => onChange(o.k)}
          className={`text-xs font-bold px-3 py-1.5 rounded-lg whitespace-nowrap transition-colors ${
            value === o.k ? 'bg-aqua/15 text-aqua border border-aqua/40' : 'text-hint hover:text-teal border border-transparent'
          }`}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

function ActBtn({ label, tone, onClick }: { label: string; tone: 'win' | 'loss' | 'gold'; onClick: () => void }) {
  const cls = { win: 'text-win border-win/40 hover:bg-win/10', loss: 'text-loss border-loss/40 hover:bg-loss/10', gold: 'text-gold border-gold/40 hover:bg-gold/10' }[tone];
  return <button onClick={onClick} className={`text-xs font-bold px-3 py-1.5 rounded-lg border ${cls} transition-colors`}>{label}</button>;
}
