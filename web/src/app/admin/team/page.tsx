'use client';
import { Suspense, useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import AdminShell from '@/components/admin/AdminShell';
import { useAdminAuth } from '@/context/AdminAuthContext';
import {
  apiTeam, apiUploadImage,
  apiTeamCoaches, apiAddTeamCoach, apiUpdateTeamCoach, apiDeleteTeamCoach, apiReorderTeamCoaches,
  apiTeamRoster, apiAddTeamPlayer, apiUpdateTeamPlayer, apiDeleteTeamPlayer, apiReorderTeamRoster,
  type MTeamFull, type MTeamCoach, type MRegistration,
} from '@/lib/adminApi';

const inputCls = "w-full bg-darkBg border border-bdr rounded-lg px-3 py-2 text-text text-sm outline-none focus:border-aqua";
const btn = "bg-aqua text-on-accent font-extrabold py-2.5 rounded-xl disabled:opacity-50";
const card = "bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-2xl p-4";

const STATUS = [
  { v: 'active', l: 'نشط' },
  { v: 'transferred', l: 'منتقل' },
  { v: 'loaned', l: 'إعارة' },
] as const;
const statusLabel = (v: string) => STATUS.find(s => s.v === v)?.l ?? v;

// Common technical-staff roles offered as suggestions; the field stays free
// text, and picking a known role fills in its English counterpart.
const COACH_ROLES = [
  { ar: 'المدير الفني',      en: 'Head Coach' },
  { ar: 'مدرب',              en: 'Coach' },
  { ar: 'مساعد مدرب',        en: 'Assistant Coach' },
  { ar: 'مدرب حراس مرمي',    en: 'Goalkeeping Coach' },
  { ar: 'محلل اداء',         en: 'Performance Analyst' },
  { ar: 'المعد النفسي',      en: 'Sports Psychologist' },
  { ar: 'اداري',             en: 'Team Administrator' },
  { ar: 'طبيب',              en: 'Doctor' },
  { ar: 'اخصائي اصابات',     en: 'Injury Specialist' },
  { ar: 'علاج طبيعي',        en: 'Physiotherapist' },
  { ar: 'مدلك',              en: 'Masseur' },
  { ar: 'مدرب الاحمال',      en: 'Fitness Coach' },
  { ar: 'اخصائي',            en: 'Specialist' },
  { ar: 'عامل مهمات',        en: 'Kit Man' },
];

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div><label className="block text-teal text-[11px] font-bold mb-1">{label}</label>{children}</div>;
}
function Err({ e }: { e: string | null }) { return e ? <p className="text-loss text-xs">{e}</p> : null; }

function Arrows({ onUp, onDown, first, last }: { onUp: () => void; onDown: () => void; first: boolean; last: boolean }) {
  return (
    <div className="flex flex-col flex-shrink-0 -my-1">
      <button onClick={onUp} disabled={first} className="text-aqua disabled:text-bdr text-xs leading-none px-1 py-0.5" aria-label="up">▲</button>
      <button onClick={onDown} disabled={last} className="text-aqua disabled:text-bdr text-xs leading-none px-1 py-0.5" aria-label="down">▼</button>
    </div>
  );
}

// Photo input: paste a URL or upload a file (server resizes and returns a URL).
function PhotoInput({ token, value, onChange }: { token: string; value: string; onChange: (v: string) => void }) {
  const [busy, setBusy] = useState(false);
  return (
    <div className="flex items-center gap-2">
      {value && <img src={value} alt="" className="w-10 h-10 rounded-full object-cover bg-darkBg border border-bdr flex-shrink-0" />}
      <input value={value} onChange={e => onChange(e.target.value)} dir="ltr" placeholder="رابط الصورة أو ارفع" className={inputCls} />
      <label className="flex-shrink-0 bg-cardBg border border-aqua/40 text-aqua text-xs font-bold px-3 py-2 rounded-lg cursor-pointer whitespace-nowrap">
        {busy ? '…' : '📤 رفع'}
        <input type="file" accept="image/*" hidden disabled={busy}
          onChange={async e => { const file = e.target.files?.[0]; if (!file) return; setBusy(true); try { onChange(await apiUploadImage(token, file)); } finally { setBusy(false); e.target.value = ''; } }} />
      </label>
    </div>
  );
}

// ── Coaches ───────────────────────────────────────────────────────────────────
function CoachForm({ token, tid, coach, onDone, onCancel }: {
  token: string; tid: number; coach: MTeamCoach | null; onDone: () => void; onCancel: () => void;
}) {
  const [f, setF] = useState({
    name_ar: coach?.name_ar ?? '', name_en: coach?.name_en ?? '',
    role_ar: coach?.role_ar ?? '', role_en: coach?.role_en ?? '',
    photo: coach?.photo ?? '',
    start_date: coach?.start_date ?? '', end_date: coach?.end_date ?? '',
  });
  const [err, setErr] = useState<string | null>(null); const [busy, setBusy] = useState(false);
  const set = (k: string, v: string) => setF({ ...f, [k]: v });
  // Choosing (or typing) a known role fills the English side automatically.
  const setRole = (v: string) => {
    const hit = COACH_ROLES.find(r => r.ar === v.trim());
    setF(prev => ({ ...prev, role_ar: v, ...(hit ? { role_en: hit.en } : {}) }));
  };
  const save = async () => {
    setErr(null); setBusy(true);
    try {
      if (coach) await apiUpdateTeamCoach(token, coach.id, f);
      else await apiAddTeamCoach(token, tid, f);
      onDone();
    } catch (e) { setErr(e instanceof Error ? e.message : 'خطأ'); } finally { setBusy(false); }
  };
  return (
    <div className={card + ' space-y-3 border-aqua/40'}>
      <p className="text-aqua font-bold text-sm">{coach ? '✏️ تعديل المدرّب' : '➕ مدرّب جديد'}</p>
      <div className="grid grid-cols-2 gap-3">
        <Field label="الاسم (عربي) *"><input value={f.name_ar} onChange={e => set('name_ar', e.target.value)} className={inputCls} /></Field>
        <Field label="الاسم (إنجليزي)"><input value={f.name_en} onChange={e => set('name_en', e.target.value)} dir="ltr" className={inputCls} /></Field>
        <Field label="الدور (عربي)">
          <input list="coach-roles" value={f.role_ar} onChange={e => setRole(e.target.value)} placeholder="اختر من القائمة أو اكتب" className={inputCls} />
          <datalist id="coach-roles">
            {COACH_ROLES.map(r => <option key={r.ar} value={r.ar} />)}
          </datalist>
        </Field>
        <Field label="الدور (إنجليزي)"><input value={f.role_en} onChange={e => set('role_en', e.target.value)} dir="ltr" placeholder="Head Coach" className={inputCls} /></Field>
        <Field label="تاريخ البداية"><input type="date" value={f.start_date} onChange={e => set('start_date', e.target.value)} className={inputCls} /></Field>
        <Field label="تاريخ النهاية"><input type="date" value={f.end_date} onChange={e => set('end_date', e.target.value)} className={inputCls} /></Field>
      </div>
      <Field label="الصورة"><PhotoInput token={token} value={f.photo} onChange={v => set('photo', v)} /></Field>
      <Err e={err} />
      <div className="flex gap-2">
        <button onClick={save} disabled={busy || !f.name_ar.trim()} className={btn + ' flex-1'}>{busy ? '…' : 'حفظ'}</button>
        <button onClick={onCancel} disabled={busy} className="flex-1 text-hint border border-bdr rounded-lg text-xs font-bold py-2">إلغاء</button>
      </div>
    </div>
  );
}

function CoachesSection({ token, tid }: { token: string; tid: number }) {
  const [items, setItems] = useState<MTeamCoach[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [editing, setEditing] = useState<MTeamCoach | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const reload = useCallback(() => {
    setLoading(true); setErr(null);
    apiTeamCoaches(token, tid).then(setItems).catch(e => setErr(e instanceof Error ? e.message : 'خطأ')).finally(() => setLoading(false));
  }, [token, tid]);
  useEffect(() => { reload(); }, [reload]);
  const remove = async (c: MTeamCoach) => { if (confirm('حذف هذا المدرّب؟')) { await apiDeleteTeamCoach(token, c.id); reload(); } };
  const move = async (idx: number, dir: -1 | 1) => {
    const j = idx + dir;
    if (j < 0 || j >= items.length) return;
    const next = [...items];
    [next[idx], next[j]] = [next[j], next[idx]];
    setItems(next);
    try { await apiReorderTeamCoaches(token, tid, next.map(x => x.id)); } catch { reload(); }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-aqua font-bold text-sm">👔 الجهاز الفني</p>
        {!adding && !editing && <button onClick={() => setAdding(true)} className="bg-aqua text-on-accent font-bold text-xs px-4 py-1.5 rounded-lg">+ مدرّب</button>}
      </div>
      {adding && <CoachForm token={token} tid={tid} coach={null} onDone={() => { setAdding(false); reload(); }} onCancel={() => setAdding(false)} />}
      <Err e={err} />
      {loading ? <p className="text-hint text-sm text-center py-4">…</p>
        : items.length === 0 && !adding ? <p className="text-hint text-sm text-center py-4">لا يوجد مدرّبون بعد</p>
        : (
          <div className="space-y-2">
            {items.map((c, idx) => editing?.id === c.id ? (
              <CoachForm key={c.id} token={token} tid={tid} coach={c} onDone={() => { setEditing(null); reload(); }} onCancel={() => setEditing(null)} />
            ) : (
              <div key={c.id} className={card + ' flex items-center gap-3'}>
                {items.length > 1 && <Arrows onUp={() => move(idx, -1)} onDown={() => move(idx, 1)} first={idx === 0} last={idx === items.length - 1} />}
                {c.photo ? <img src={c.photo} alt="" className="w-10 h-10 rounded-full object-cover bg-darkBg flex-shrink-0" /> : <div className="w-10 h-10 rounded-full bg-darkBg grid place-items-center flex-shrink-0">👤</div>}
                <div className="flex-1 min-w-0">
                  <p className="text-text font-bold text-sm truncate">{c.name_ar || c.name_en}</p>
                  <p className="text-teal text-[11px] truncate">{c.role_ar || c.role_en || '—'}</p>
                </div>
                {!c.end_date && <span className="text-win text-[10px] font-bold border border-win/40 bg-win/10 rounded px-2 py-0.5 flex-shrink-0">حالي</span>}
                <button onClick={() => setEditing(c)} className="text-aqua text-[11px] font-bold flex-shrink-0">تعديل</button>
                <button onClick={() => remove(c)} className="text-loss text-[11px] font-bold flex-shrink-0">حذف</button>
              </div>
            ))}
          </div>
        )}
    </div>
  );
}

// ── Roster ────────────────────────────────────────────────────────────────────
function PlayerForm({ token, tid, reg, onDone, onCancel }: {
  token: string; tid: number; reg: MRegistration | null; onDone: () => void; onCancel: () => void;
}) {
  const [f, setF] = useState({
    name_ar: reg?.name_ar ?? '', name_en: reg?.name_en ?? '',
    shirt_number: reg?.shirt_number != null ? String(reg.shirt_number) : '',
    birth_year: reg?.birth_year != null && reg.birth_year_verified ? String(reg.birth_year) : '',
    position_ar: reg?.position_ar ?? '', position_en: reg?.position_en ?? '',
    photo: reg?.photo ?? '',
    status: reg?.status ?? 'active',
    start_date: reg?.start_date ?? '', end_date: reg?.end_date ?? '',
  });
  const [err, setErr] = useState<string | null>(null); const [busy, setBusy] = useState(false);
  const set = (k: string, v: string) => setF({ ...f, [k]: v });
  const save = async () => {
    setErr(null); setBusy(true);
    try {
      if (reg) await apiUpdateTeamPlayer(token, reg.id, f);
      else await apiAddTeamPlayer(token, tid, f);
      onDone();
    } catch (e) { setErr(e instanceof Error ? e.message : 'خطأ'); } finally { setBusy(false); }
  };
  return (
    <div className={card + ' space-y-3 border-aqua/40'}>
      <p className="text-aqua font-bold text-sm">{reg ? '✏️ تعديل اللاعب' : '➕ لاعب جديد'}</p>
      <div className="grid grid-cols-2 gap-3">
        <Field label="الاسم (عربي) *"><input value={f.name_ar} onChange={e => set('name_ar', e.target.value)} className={inputCls} /></Field>
        <Field label="الاسم (إنجليزي)"><input value={f.name_en} onChange={e => set('name_en', e.target.value)} dir="ltr" className={inputCls} /></Field>
        <Field label="رقم القميص"><input type="number" value={f.shirt_number} onChange={e => set('shirt_number', e.target.value)} className={inputCls} /></Field>
        <Field label="سنة الميلاد"><input type="number" value={f.birth_year} onChange={e => set('birth_year', e.target.value)} placeholder="2010" className={inputCls} /></Field>
        <Field label="المركز (عربي)"><input value={f.position_ar} onChange={e => set('position_ar', e.target.value)} placeholder="مهاجم" className={inputCls} /></Field>
        <Field label="المركز (إنجليزي)"><input value={f.position_en} onChange={e => set('position_en', e.target.value)} dir="ltr" placeholder="Striker" className={inputCls} /></Field>
        <Field label="الحالة"><select value={f.status} onChange={e => set('status', e.target.value)} className={inputCls}>{STATUS.map(s => <option key={s.v} value={s.v}>{s.l}</option>)}</select></Field>
        <Field label="تاريخ التسجيل"><input type="date" value={f.start_date} onChange={e => set('start_date', e.target.value)} className={inputCls} /></Field>
        <Field label="تاريخ الانتهاء"><input type="date" value={f.end_date} onChange={e => set('end_date', e.target.value)} className={inputCls} /></Field>
      </div>
      <Field label="الصورة"><PhotoInput token={token} value={f.photo} onChange={v => set('photo', v)} /></Field>
      <Err e={err} />
      <div className="flex gap-2">
        <button onClick={save} disabled={busy || !f.name_ar.trim()} className={btn + ' flex-1'}>{busy ? '…' : 'حفظ'}</button>
        <button onClick={onCancel} disabled={busy} className="flex-1 text-hint border border-bdr rounded-lg text-xs font-bold py-2">إلغاء</button>
      </div>
    </div>
  );
}

function RosterSection({ token, tid }: { token: string; tid: number }) {
  const [items, setItems] = useState<MRegistration[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [editing, setEditing] = useState<MRegistration | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const reload = useCallback(() => {
    setLoading(true); setErr(null);
    apiTeamRoster(token, tid).then(setItems).catch(e => setErr(e instanceof Error ? e.message : 'خطأ')).finally(() => setLoading(false));
  }, [token, tid]);
  useEffect(() => { reload(); }, [reload]);
  const remove = async (r: MRegistration) => { if (confirm('حذف هذا اللاعب من القائمة؟')) { await apiDeleteTeamPlayer(token, r.id); reload(); } };
  const move = async (idx: number, dir: -1 | 1) => {
    const j = idx + dir;
    if (j < 0 || j >= items.length) return;
    const next = [...items];
    [next[idx], next[j]] = [next[j], next[idx]];
    setItems(next);
    try { await apiReorderTeamRoster(token, tid, next.map(x => x.id)); } catch { reload(); }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-aqua font-bold text-sm">🧑‍🤝‍🧑 قائمة اللاعبين {items.length > 0 && <span className="text-hint text-xs">({items.length})</span>}</p>
        {!adding && !editing && <button onClick={() => setAdding(true)} className="bg-aqua text-on-accent font-bold text-xs px-4 py-1.5 rounded-lg">+ لاعب</button>}
      </div>
      {adding && <PlayerForm token={token} tid={tid} reg={null} onDone={() => { setAdding(false); reload(); }} onCancel={() => setAdding(false)} />}
      <Err e={err} />
      {loading ? <p className="text-hint text-sm text-center py-4">…</p>
        : items.length === 0 && !adding ? <p className="text-hint text-sm text-center py-4">لا يوجد لاعبون بعد</p>
        : (
          <div className="space-y-2">
            {items.map((r, idx) => editing?.id === r.id ? (
              <PlayerForm key={r.id} token={token} tid={tid} reg={r} onDone={() => { setEditing(null); reload(); }} onCancel={() => setEditing(null)} />
            ) : (
              <div key={r.id} className={card + ' flex items-center gap-3'}>
                {items.length > 1 && <Arrows onUp={() => move(idx, -1)} onDown={() => move(idx, 1)} first={idx === 0} last={idx === items.length - 1} />}
                <div className="w-8 h-8 rounded-lg bg-darkBg grid place-items-center flex-shrink-0 text-aqua font-bold text-sm tnum">{r.shirt_number ?? '—'}</div>
                <div className="flex-1 min-w-0">
                  <p className="text-text font-bold text-sm truncate">{r.name_ar || r.name_en}</p>
                  <p className="text-hint text-[11px] truncate">
                    {r.position_ar || r.position_en || ''}
                    {r.birth_year ? ` · ${r.birth_year}${r.birth_year_verified ? '' : '؟'}` : ''}
                    {r.status !== 'active' ? ` · ${statusLabel(r.status)}` : ''}
                  </p>
                </div>
                {r.end_date && <span className="text-hint text-[10px] border border-bdr rounded px-2 py-0.5 flex-shrink-0">منتهٍ</span>}
                <button onClick={() => setEditing(r)} className="text-aqua text-[11px] font-bold flex-shrink-0">تعديل</button>
                <button onClick={() => remove(r)} className="text-loss text-[11px] font-bold flex-shrink-0">حذف</button>
              </div>
            ))}
          </div>
        )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
function TeamPageInner() {
  const { token, canEdit } = useAdminAuth();
  const params = useSearchParams();
  const id = Number(params.get('id') || 0);
  const [team, setTeam] = useState<MTeamFull | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !id) return;
    apiTeam(token, id).then(setTeam).catch(e => setErr(e instanceof Error ? e.message : 'خطأ'));
  }, [token, id]);

  return (
    <AdminShell title="الفريق">
      <Link href={team ? `/admin/club?id=${team.club_id}` : '/admin/structure'} className="inline-block text-aqua text-xs font-bold mb-3">→ رجوع للنادي</Link>
      {!canEdit ? (
        <div className="bg-cardBg border border-bdr rounded-2xl p-8 text-center">
          <p className="text-3xl mb-3">🔒</p><p className="text-text text-sm font-bold">تحتاج صلاحية «محرّر» أو أعلى</p>
        </div>
      ) : err ? (
        <p className="text-loss text-sm text-center py-8">{err}</p>
      ) : !team ? (
        <p className="text-hint text-sm text-center py-8">…</p>
      ) : (
        <div className="space-y-5">
          <div className={card + ' flex items-center gap-3'}>
            {team.logo ? <img src={team.logo} alt="" className="w-12 h-12 rounded-lg object-contain bg-darkBg flex-shrink-0" /> : <div className="w-12 h-12 rounded-lg bg-darkBg grid place-items-center flex-shrink-0">🛡️</div>}
            <div className="min-w-0">
              <p className="text-text font-extrabold text-base truncate">{team.name_ar || team.name_en || team.club_name}</p>
              <p className="text-hint text-xs truncate">
                {team.age ?? ''}
                {team.seasons.length > 0 && ` · ${team.seasons.join('، ')}`}
              </p>
            </div>
          </div>
          <CoachesSection token={token!} tid={team.id} />
          <RosterSection token={token!} tid={team.id} />
        </div>
      )}
    </AdminShell>
  );
}

export default function TeamPage() {
  return (
    <Suspense fallback={null}>
      <TeamPageInner />
    </Suspense>
  );
}
