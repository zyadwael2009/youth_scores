'use client';
// Venue cleanup: the venue on a match was typed as free text for years, so one
// ground shows up under many spellings. The server suggests groups of likely-same
// spellings; the admin ticks the ones that really are the same ground and links
// them to a directory venue (or creates one). Linking only sets the match's
// venue_id — the typed text stays — so any link can be undone.
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useAdminAuth } from '@/context/AdminAuthContext';
import { inputCls } from '@/components/admin/formKit';
import {
  apiVenueCleanup, apiVenueCleanupLink, apiVenueCleanupUnlink, apiMergeVenue,
  type AdminVenue, type VenueCleanupData, type VenueGroup,
} from '@/lib/adminApi';

const PAGE = 25;
const NEW = 'new';

const norm = (s: string) =>
  s.replace(/[أإآ]/g, 'ا').replace(/ى/g, 'ي').replace(/ة/g, 'ه').toLowerCase().trim();
const vname = (v?: AdminVenue | null) => (v ? v.name_ar || v.name_en || `#${v.id}` : '');

type Filter = 'pending' | 'done' | 'all';

export default function VenueCleanup() {
  const { token } = useAdminAuth();
  const [data, setData] = useState<VenueCleanupData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>('pending');
  const [q, setQ] = useState('');
  const [shown, setShown] = useState(PAGE);

  const load = useCallback(() => {
    if (!token) return;
    setErr(null);
    apiVenueCleanup(token).then(setData).catch(e => setErr(e instanceof Error ? e.message : 'خطأ'));
  }, [token]);
  useEffect(() => { load(); }, [load]);

  const venues = useMemo(
    () => [...(data?.venues ?? [])].sort((a, b) => vname(a).localeCompare(vname(b), 'ar')),
    [data?.venues]);
  const byId = useMemo(() => new Map(venues.map(v => [v.id, v])), [venues]);

  const list = useMemo(() => {
    if (!data) return [];
    const nq = norm(q);
    return data.groups.filter(g => {
      if (filter === 'pending' && g.linked >= g.total) return false;
      if (filter === 'done' && g.linked === 0) return false;
      return !nq || g.spellings.some(s => norm(s.text).includes(nq));
    });
  }, [data, filter, q]);
  useEffect(() => { setShown(PAGE); }, [filter, q]);

  // Apply a link/unlink locally so the list doesn't jump while the admin works
  // through it (a full reload regroups and takes a couple of seconds).
  const applyLocal = (texts: string[], venue: AdminVenue | null) => {
    setData(d => {
      if (!d) return d;
      const set = new Set(texts);
      let delta = 0;
      const groups = d.groups.map(g => {
        if (!g.spellings.some(s => set.has(s.text))) return g;
        const spellings = g.spellings.map(s => {
          if (!set.has(s.text)) return s;
          const was = s.linked.reduce((n, l) => n + l.count, 0);
          const now = venue ? s.count : 0;
          delta += now - was;
          return { ...s, linked: venue ? [{ venue_id: venue.id, count: s.count }] : [] };
        });
        return { ...g, spellings, linked: spellings.reduce((n, s) => n + s.linked.reduce((m, l) => m + l.count, 0), 0) };
      });
      const venuesNext = venue && !d.venues.some(v => v.id === venue.id) ? [...d.venues, venue] : d.venues;
      return { ...d, groups, venues: venuesNext, stats: { ...d.stats, linked: d.stats.linked + delta } };
    });
  };

  if (err) return <p className="text-loss text-sm text-center py-6">{err} — <button onClick={load} className="underline">إعادة المحاولة</button></p>;
  if (!data) return <p className="text-hint text-sm text-center py-6">جارٍ تحليل أسماء الملاعب…</p>;

  const pct = data.stats.matches ? Math.round((data.stats.linked / data.stats.matches) * 100) : 0;
  const groupById = new Map(data.groups.map(g => [g.id, g]));

  return (
    <div className="space-y-4">
      <div className="bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-2xl p-4 space-y-2">
        <p className="text-text font-bold text-sm">🧹 توحيد أسماء الملاعب</p>
        <p className="text-hint text-[11px] leading-relaxed">
          الأسماء المتشابهة مجمّعة كاقتراح. حدّد الأسماء التي تخص نفس الملعب فعلًا واربطها بملعب مسجّل.
          الربط لا يغيّر النص المكتوب في المباراة، ويمكن فكّه في أي وقت.
        </p>
        <div className="h-2 rounded-full bg-bdr overflow-hidden">
          <div className="h-full bg-aqua" style={{ width: `${pct}%` }} />
        </div>
        <p className="text-teal text-[11px] font-bold">
          {data.stats.linked.toLocaleString('ar-EG')} / {data.stats.matches.toLocaleString('ar-EG')} مباراة مربوطة ({pct}%)
          · {data.stats.spellings} اسم مكتوب · {data.stats.groups} مجموعة
        </p>
      </div>

      <div className="flex gap-2">
        {([['pending', 'تحتاج ربط'], ['done', 'مربوطة'], ['all', 'الكل']] as const).map(([v, l]) => (
          <button key={v} onClick={() => setFilter(v)}
            className={`flex-1 text-xs font-bold py-2 rounded-xl border ${filter === v ? 'bg-aqua text-on-accent border-transparent' : 'bg-cardBg border-bdr text-teal'}`}>
            {l}
          </button>
        ))}
      </div>
      <input value={q} onChange={e => setQ(e.target.value)} placeholder="🔍 ابحث باسم الملعب…" className={inputCls} />

      <p className="text-hint text-[11px]">{list.length} مجموعة</p>
      {list.slice(0, shown).map(g => (
        <GroupCard key={`${g.id}:${g.main}`} token={token!} group={g} venues={venues} byId={byId}
          maybe={g.maybe.map(i => groupById.get(i)).filter((x): x is VenueGroup => !!x)}
          onSearch={setQ} onApplied={applyLocal} />
      ))}
      {list.length > shown && (
        <button onClick={() => setShown(s => s + PAGE)}
          className="w-full text-sm font-bold py-2.5 rounded-xl border border-bdr text-teal bg-cardBg">
          عرض المزيد ({list.length - shown})
        </button>
      )}
      {list.length === 0 && <p className="text-hint text-xs text-center py-4">لا توجد مجموعات هنا 🎉</p>}

      <MergeVenues token={token!} venues={venues} onMerged={load} />
    </div>
  );
}

function GroupCard({ token, group, venues, byId, maybe, onSearch, onApplied }: {
  token: string; group: VenueGroup; venues: AdminVenue[]; byId: Map<number, AdminVenue>;
  maybe: VenueGroup[]; onSearch: (q: string) => void;
  onApplied: (texts: string[], venue: AdminVenue | null) => void;
}) {
  const unlinked = (s: VenueGroup['spellings'][number]) => s.linked.length === 0;
  const [picked, setPicked] = useState<Set<string>>(
    () => new Set(group.spellings.filter(unlinked).map(s => s.text)));
  const [target, setTarget] = useState<string>(
    group.suggested_venue_id != null ? String(group.suggested_venue_id) : NEW);
  const [nv, setNv] = useState({ name_ar: group.main, url: '' });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const chosen = group.spellings.filter(s => picked.has(s.text));
  const chosenCount = chosen.reduce((n, s) => n + s.count, 0);
  const chosenLinked = chosen.filter(s => !unlinked(s));
  const done = group.linked >= group.total;

  const toggle = (t: string) => setPicked(p => {
    const n = new Set(p); if (n.has(t)) n.delete(t); else n.add(t); return n;
  });

  const link = async () => {
    const texts = chosen.map(s => s.text);
    if (!texts.length) return;
    setBusy(true); setMsg(null);
    try {
      const r = await apiVenueCleanupLink(token, texts, target === NEW
        ? { new_venue: { name_ar: nv.name_ar.trim(), url: nv.url.trim() } }
        : { venue_id: Number(target) });
      onApplied(texts, r.venue);
      setTarget(String(r.venue.id));
      setPicked(new Set());
      setMsg({ ok: true, text: `✅ تم ربط ${r.linked} مباراة بـ «${vname(r.venue)}»` });
    } catch (e) { setMsg({ ok: false, text: e instanceof Error ? e.message : 'خطأ' }); }
    finally { setBusy(false); }
  };

  const unlink = async () => {
    const texts = chosenLinked.map(s => s.text);
    if (!texts.length || !confirm(`فك ربط ${texts.length} اسم؟ يبقى النص المكتوب في المباريات كما هو.`)) return;
    setBusy(true); setMsg(null);
    try {
      const r = await apiVenueCleanupUnlink(token, texts);
      onApplied(texts, null);
      setMsg({ ok: true, text: `تم فك ربط ${r.unlinked} مباراة` });
    } catch (e) { setMsg({ ok: false, text: e instanceof Error ? e.message : 'خطأ' }); }
    finally { setBusy(false); }
  };

  const canLink = chosen.length > 0 && (target !== NEW || nv.name_ar.trim().length > 0);

  return (
    <div className={`border rounded-2xl p-3 space-y-2.5 ${done ? 'bg-win/5 border-win/30' : 'bg-cardBg border-bdr'}`}>
      <div className="flex items-start justify-between gap-2">
        <p className="text-text font-bold text-sm">{group.main}</p>
        <span className={`shrink-0 text-[10px] font-bold rounded-full px-2 py-0.5 ${done ? 'bg-win/15 text-win' : 'bg-aqua/10 text-aqua'}`}>
          {done ? '✓ مربوطة' : `${group.linked}/${group.total} مباراة`}
        </span>
      </div>

      <div className="space-y-1">
        {group.spellings.map(s => (
          <label key={s.text} className="flex items-center gap-2 text-xs cursor-pointer">
            <input type="checkbox" checked={picked.has(s.text)} onChange={() => toggle(s.text)} className="accent-aqua" />
            <span className="text-text flex-1 min-w-0 truncate">{s.text}</span>
            {s.linked.map(l => (
              <span key={l.venue_id} className="text-win text-[10px] truncate max-w-[40%]">🔗 {vname(byId.get(l.venue_id))}</span>
            ))}
            <span className="text-hint tabular-nums">{s.count}</span>
          </label>
        ))}
      </div>

      {maybe.length > 0 && (
        <p className="text-hint text-[11px]">
          قد يكون نفس الملعب:{' '}
          {maybe.slice(0, 4).map((m, i) => (
            <button key={m.id} onClick={() => onSearch(m.main)} className="text-aqua hover:underline">
              {i > 0 && '، '}{m.main}
            </button>
          ))}
        </p>
      )}

      <div className="flex flex-col sm:flex-row gap-2">
        <select value={target} onChange={e => setTarget(e.target.value)} className={`${inputCls} sm:flex-1`}>
          <option value={NEW}>➕ ملعب جديد…</option>
          {venues.map(v => (
            <option key={v.id} value={v.id}>
              {v.id === group.suggested_venue_id ? '⭐ ' : ''}{vname(v)}{v.url ? ' 📍' : ''}
            </option>
          ))}
        </select>
      </div>
      {target === NEW && (
        <div className="grid sm:grid-cols-2 gap-2">
          <input value={nv.name_ar} onChange={e => setNv({ ...nv, name_ar: e.target.value })}
            placeholder="اسم الملعب الصحيح" className={inputCls} />
          <input value={nv.url} onChange={e => setNv({ ...nv, url: e.target.value })} dir="ltr"
            placeholder="رابط الخريطة (اختياري)" className={inputCls} />
        </div>
      )}

      {msg && <p className={`text-[11px] ${msg.ok ? 'text-win' : 'text-loss'}`}>{msg.text}</p>}

      <div className="flex gap-2">
        <button onClick={link} disabled={busy || !canLink}
          className="flex-1 bg-aqua text-on-accent text-xs font-extrabold py-2 rounded-xl disabled:opacity-50">
          {busy ? 'جارٍ الحفظ…' : chosen.length ? `ربط ${chosenCount} مباراة` : 'حدّد الأسماء أولًا'}
        </button>
        {chosenLinked.length > 0 && (
          <button onClick={unlink} disabled={busy}
            className="text-xs font-bold px-3 py-2 rounded-xl border border-loss/40 text-loss disabled:opacity-50">
            فك الربط
          </button>
        )}
      </div>
    </div>
  );
}

// Two directory entries for the same ground: fold one into the other.
function MergeVenues({ token, venues, onMerged }: { token: string; venues: AdminVenue[]; onMerged: () => void }) {
  const [from, setFrom] = useState('');
  const [into, setInto] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const byId = new Map(venues.map(v => [String(v.id), v]));

  const merge = async () => {
    const a = byId.get(from), b = byId.get(into);
    if (!a || !b || a.id === b.id) return;
    if (!confirm(`دمج «${vname(a)}» في «${vname(b)}»؟ سيُحذف «${vname(a)}» وتنتقل مبارياته.`)) return;
    setBusy(true); setMsg(null);
    try {
      const r = await apiMergeVenue(token, a.id, b.id);
      setMsg({ ok: true, text: `✅ تم الدمج ونقل ${r.moved} مباراة` });
      setFrom(''); onMerged();
    } catch (e) { setMsg({ ok: false, text: e instanceof Error ? e.message : 'خطأ' }); }
    finally { setBusy(false); }
  };

  return (
    <div className="bg-cardBg border border-bdr rounded-2xl p-4 space-y-2">
      <p className="text-text font-bold text-sm">🔀 دمج ملعبين مسجّلين مكررين</p>
      <p className="text-hint text-[11px]">ينقل المباريات إلى الملعب الثاني ويحذف الأول (يُحتفظ برابط الخريطة).</p>
      <select value={from} onChange={e => setFrom(e.target.value)} className={inputCls}>
        <option value="">الملعب المكرر (سيُحذف)…</option>
        {venues.map(v => <option key={v.id} value={v.id}>{vname(v)}</option>)}
      </select>
      <select value={into} onChange={e => setInto(e.target.value)} className={inputCls}>
        <option value="">يُدمج في…</option>
        {venues.filter(v => String(v.id) !== from).map(v => <option key={v.id} value={v.id}>{vname(v)}</option>)}
      </select>
      {msg && <p className={`text-[11px] ${msg.ok ? 'text-win' : 'text-loss'}`}>{msg.text}</p>}
      <button onClick={merge} disabled={busy || !from || !into || from === into}
        className="w-full bg-aqua text-on-accent text-xs font-extrabold py-2 rounded-xl disabled:opacity-50">
        {busy ? 'جارٍ الدمج…' : 'دمج'}
      </button>
    </div>
  );
}
