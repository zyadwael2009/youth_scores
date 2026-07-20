'use client';
import { useState, useEffect, useCallback } from 'react';
import AdminShell from '@/components/admin/AdminShell';
import { useAdminAuth } from '@/context/AdminAuthContext';
import {
  apiCreateNews, apiUpdateNews, apiCreateVenue, apiListNews, apiDeleteNews, apiUploadImage,
  type NotifyResult, type AdminNews,
} from '@/lib/adminApi';

export default function AdminContentPage() {
  return <AdminShell title="الأخبار والملاعب"><Content /></AdminShell>;
}

const inputCls = "w-full bg-darkBg border border-bdr rounded-lg px-3 py-2 text-text text-sm outline-none focus:border-aqua";

function NotifyBadge({ n }: { n: NotifyResult }) {
  if (n.status === 'dry_run')
    return <p className="text-gold text-[11px] bg-gold/10 border border-gold/30 rounded-lg px-3 py-2">🔔 تم الحفظ. الإشعار في وضع التجربة (يُرسل بعد ربط Firebase) — موضوعه: {n.topic}</p>;
  if (n.status === 'sent')
    return <p className="text-win text-[11px] bg-win/10 border border-win/30 rounded-lg px-3 py-2">✅ تم الحفظ وإرسال الإشعار.</p>;
  return <p className="text-win text-[11px] bg-win/10 border border-win/30 rounded-lg px-3 py-2">✅ تم الحفظ.</p>;
}

function Content() {
  const { canEdit } = useAdminAuth();
  const [tab, setTab] = useState<'news' | 'venue'>('news');

  if (!canEdit) {
    return (
      <div className="bg-cardBg border border-bdr rounded-2xl p-8 text-center">
        <p className="text-3xl mb-3">🔒</p>
        <p className="text-text text-sm font-bold">تحتاج صلاحية «محرّر» أو أعلى</p>
        <p className="text-hint text-xs mt-2">تواصل مع المدير العام لترقية حسابك.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {([['news', '📰 الأخبار'], ['venue', '🏟️ ملعب جديد']] as const).map(([v, l]) => (
          <button key={v} onClick={() => setTab(v)}
            className={`flex-1 text-sm font-bold py-2.5 rounded-xl border transition-colors ${tab === v ? 'bg-aqua text-on-accent border-transparent' : 'bg-cardBg border-bdr text-teal'}`}>
            {l}
          </button>
        ))}
      </div>
      {tab === 'news' ? <NewsTab /> : <VenueForm />}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <div><label className="block text-teal text-[11px] font-bold mb-1">{label}</label>{children}</div>;
}

// ── image picker (URL + device upload with server-side resizing) ─────────────

function ImagePicker({ token, images, onChange }: { token: string; images: string[]; onChange: (imgs: string[]) => void }) {
  const [url, setUrl] = useState('');
  const [uploading, setUploading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const addUrl = () => { const u = url.trim(); if (u) { onChange([...images, u]); setUrl(''); } };
  const onFiles = async (files: FileList | null) => {
    if (!files?.length) return;
    setErr(null); setUploading(true);
    try {
      const uploaded: string[] = [];
      for (const f of Array.from(files)) uploaded.push(await apiUploadImage(token, f));
      onChange([...images, ...uploaded]);
    } catch (e) { setErr(e instanceof Error ? e.message : 'فشل الرفع'); }
    finally { setUploading(false); }
  };

  return (
    <div className="space-y-2">
      {images.length > 0 && (
        <div className="grid grid-cols-3 gap-2">
          {images.map((src, i) => (
            <div key={i} className="relative aspect-video rounded-lg overflow-hidden border border-bdr bg-darkBg">
              <img src={src} alt="" className="w-full h-full object-cover" />
              <button type="button" onClick={() => onChange(images.filter((_, x) => x !== i))}
                className="absolute top-1 left-1 w-5 h-5 rounded-full bg-black/70 text-white text-xs grid place-items-center">×</button>
              {i === 0 && <span className="absolute bottom-1 right-1 text-[8px] bg-gold text-on-accent px-1.5 py-0.5 rounded font-bold">الغلاف</span>}
            </div>
          ))}
        </div>
      )}
      <div className="flex gap-2">
        <input value={url} onChange={e => setUrl(e.target.value)} dir="ltr" placeholder="رابط صورة https://…" className={inputCls}
          onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addUrl(); } }} />
        <button type="button" onClick={addUrl} className="bg-cardBg border border-bdr text-teal text-xs font-bold px-3 rounded-lg whitespace-nowrap">+ رابط</button>
      </div>
      <label className="flex items-center justify-center gap-2 border border-dashed border-aqua/40 rounded-lg py-2.5 text-aqua text-xs font-bold cursor-pointer hover:bg-aqua/5 transition-colors">
        {uploading ? 'جارٍ الرفع…' : '📤 رفع صور من الجهاز (تُضبط أبعادها تلقائيًا)'}
        <input type="file" accept="image/*" multiple hidden disabled={uploading} onChange={e => { onFiles(e.target.files); e.target.value = ''; }} />
      </label>
      {err && <p className="text-loss text-xs">{err}</p>}
    </div>
  );
}

// ── news: create form + manage/delete list ───────────────────────────────────

function NewsTab() {
  const { token } = useAdminAuth();
  const [items, setItems] = useState<AdminNews[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<AdminNews | null>(null);

  const load = useCallback(() => {
    if (!token) return;
    apiListNews(token).then(setItems).catch(() => {}).finally(() => setLoading(false));
  }, [token]);
  useEffect(() => { load(); }, [load]);

  return (
    <div className="space-y-5">
      {/* Only one form on screen at a time, so there is no doubt about which
          one a save applies to. */}
      {editing
        // Keyed by id: the form seeds its fields on mount, so picking a
        // different item has to remount it or it would keep the first one's text.
        ? <NewsForm key={editing.id} token={token!} news={editing} onCancel={() => setEditing(null)}
            onCreated={() => { setEditing(null); load(); }} />
        : <NewsForm token={token!} onCreated={load} />}
      <div>
        <p className="text-text font-bold text-sm mb-2">الأخبار المنشورة {!loading && `(${items.length})`}</p>
        {loading ? <p className="text-hint text-sm text-center py-4">جارٍ التحميل…</p> : (
          <div className="space-y-2">
            {items.map(n => (
              <div key={n.id} className="bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-xl p-3 flex items-center gap-3">
                {n.image_url
                  ? <img src={n.image_url} alt="" className="w-14 h-14 rounded-lg object-cover flex-shrink-0" />
                  : <div className="w-14 h-14 rounded-lg bg-darkBg grid place-items-center text-xl flex-shrink-0">📰</div>}
                <div className="flex-1 min-w-0">
                  <p className="text-text text-sm font-bold truncate">{n.title_ar || n.title_en}</p>
                  <p className="text-hint text-[11px] mt-0.5">
                    {n.date}{n.images.length > 1 && ` · ${n.images.length} صور`}{!n.is_published && ' · مسودة'}
                  </p>
                </div>
                <button
                  onClick={() => { setEditing(n); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                  className="text-aqua text-xs font-bold border border-aqua/40 bg-aqua/10 rounded-lg px-3 py-1.5">
                  تعديل
                </button>
                <button
                  onClick={async () => { if (confirm(`حذف الخبر: «${n.title_ar || n.title_en}»؟`)) { await apiDeleteNews(token!, n.id); load(); } }}
                  className="text-loss text-xs font-bold border border-loss/40 bg-loss/10 rounded-lg px-3 py-1.5">
                  حذف
                </button>
              </div>
            ))}
            {items.length === 0 && <p className="text-hint text-sm text-center py-4">لا توجد أخبار</p>}
          </div>
        )}
      </div>
    </div>
  );
}

// Serves both jobs: with `news` it edits that item, without it creates a new
// one. Sharing the form keeps the two from drifting apart, which is how an
// edit screen ends up missing a field the create screen has.
function NewsForm({ token, news, onCreated, onCancel }: {
  token: string; news?: AdminNews; onCreated: () => void; onCancel?: () => void;
}) {
  const today = new Date().toISOString().slice(0, 10);
  const blank = { title_ar: '', title_en: '', details_ar: '', date: today, is_published: true };
  const [f, setF] = useState(news
    ? {
      title_ar: news.title_ar ?? '', title_en: news.title_en ?? '',
      details_ar: news.details_ar ?? '', date: news.date,
      is_published: news.is_published,
    }
    : blank);
  const [images, setImages] = useState<string[]>(news?.images ?? []);
  const [result, setResult] = useState<NotifyResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const set = (k: string, v: string | boolean) => setF({ ...f, [k]: v });

  const submit = async () => {
    setError(null); setBusy(true);
    try {
      if (news) {
        await apiUpdateNews(token, news.id, { ...f, images });
      } else {
        const r = await apiCreateNews(token, { ...f, images });
        setResult(r.notification);
        setF(blank); setImages([]);
      }
      onCreated();
    } catch (e) { setError(e instanceof Error ? e.message : 'خطأ'); }
    finally { setBusy(false); }
  };

  return (
    <div className={`bg-gradient-to-b from-cardBg to-cardBg2 border rounded-2xl p-4 space-y-3 ${news ? 'border-aqua/40' : 'border-bdr'}`}>
      <p className="text-aqua font-bold text-sm">{news ? '✏️ تعديل الخبر' : '➕ خبر جديد'}</p>
      <Field label="العنوان (عربي) *"><input value={f.title_ar} onChange={e => set('title_ar', e.target.value)} className={inputCls} /></Field>
      <Field label="العنوان (إنجليزي)"><input value={f.title_en} onChange={e => set('title_en', e.target.value)} dir="ltr" className={inputCls} /></Field>
      <Field label="التفاصيل"><textarea value={f.details_ar} onChange={e => set('details_ar', e.target.value)} rows={3} className={inputCls} /></Field>
      <Field label="الصور (رابط أو رفع — عدة صور)"><ImagePicker token={token} images={images} onChange={setImages} /></Field>
      <div className="flex items-center gap-3">
        <Field label="التاريخ"><input type="date" value={f.date} onChange={e => set('date', e.target.value)} className={inputCls} /></Field>
        <label className="flex items-center gap-2 text-teal text-xs pt-4">
          <input type="checkbox" checked={f.is_published} onChange={e => set('is_published', e.target.checked)} />
          {news ? 'منشور' : 'نشر + إشعار'}
        </label>
      </div>
      {news && (
        // Editing never re-notifies: the push goes out once, when the item is
        // first published, so a typo fix cannot buzz every phone again.
        <p className="text-hint text-[11px]">لن يُرسل إشعار عند التعديل.</p>
      )}
      {error && <p className="text-loss text-xs">{error}</p>}
      {result && <NotifyBadge n={result} />}
      <div className="flex gap-2">
        <button onClick={submit} disabled={busy || !f.title_ar.trim()}
          className="flex-1 bg-aqua text-on-accent font-extrabold py-2.5 rounded-xl disabled:opacity-50">
          {busy ? 'جارٍ الحفظ…' : news ? 'حفظ التعديل' : 'نشر الخبر'}
        </button>
        {onCancel && (
          <button onClick={onCancel} disabled={busy}
            className="flex-1 text-hint border border-bdr rounded-xl text-xs font-bold py-2.5">إلغاء</button>
        )}
      </div>
    </div>
  );
}

function VenueForm() {
  const { token } = useAdminAuth();
  const [f, setF] = useState({ name_ar: '', name_en: '', url: '' });
  const [result, setResult] = useState<NotifyResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const set = (k: string, v: string) => setF({ ...f, [k]: v });

  const submit = async () => {
    setError(null); setBusy(true);
    try { const r = await apiCreateVenue(token!, { ...f }); setResult(r.notification); setF({ name_ar: '', name_en: '', url: '' }); }
    catch (e) { setError(e instanceof Error ? e.message : 'خطأ'); }
    finally { setBusy(false); }
  };

  return (
    <div className="bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-2xl p-4 space-y-3">
      <Field label="اسم الملعب (عربي) *"><input value={f.name_ar} onChange={e => set('name_ar', e.target.value)} className={inputCls} /></Field>
      <Field label="اسم الملعب (إنجليزي)"><input value={f.name_en} onChange={e => set('name_en', e.target.value)} dir="ltr" className={inputCls} /></Field>
      <Field label="رابط الخريطة (اختياري)"><input value={f.url} onChange={e => set('url', e.target.value)} dir="ltr" placeholder="https://maps.google.com/…" className={inputCls} /></Field>
      {error && <p className="text-loss text-xs">{error}</p>}
      {result && <NotifyBadge n={result} />}
      <button onClick={submit} disabled={busy || !f.name_ar.trim()}
        className="w-full bg-aqua text-on-accent font-extrabold py-2.5 rounded-xl disabled:opacity-50">
        {busy ? 'جارٍ الحفظ…' : 'إضافة الملعب'}
      </button>
    </div>
  );
}
