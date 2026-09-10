'use client';
import { useEffect, useState } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { tNews, tNewsItem, mediaUrl, type TNews } from '@/lib/tla3bnyApi';
import { useApp } from '@/context/AppContext';
import Spinner from '@/components/ui/Spinner';
import PhotoGalleryViewer from './PhotoGalleryViewer';
import { getReadNews, markNewsRead, seedReadNewsIfFirstRun } from '@/lib/seen';
import { EmptyState, useTT } from './kit';

/**
 * The public news feed, presented like youthscores': a cover-photo card that
 * opens the full item, with a fullscreen photo viewer for the gallery.
 *
 * With `compId` it shows one competition's news; without it, everything.
 */

function formatNewsDate(date: string | null, locale: string): string {
  if (!date) return '';
  try {
    return new Date(date + 'T00:00:00').toLocaleDateString(
      locale === 'ar' ? 'ar-EG' : 'en-US',
      { day: 'numeric', month: 'long', year: 'numeric' },
    );
  } catch { return date; }
}

function NewsDetail({ item, onClose }: { item: TNews; onClose: () => void }) {
  const tt = useTT();
  const { locale } = useApp();
  const [photoIdx, setPhotoIdx] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);
  const photos = item.images.map(i => mediaUrl(i)).filter(Boolean) as string[];

  // Share the current URL — it now carries ?news=<id>, and the server injects
  // this item's title + cover into the link's WhatsApp/social preview.
  const share = async () => {
    const url = typeof window !== 'undefined' ? window.location.href : '';
    if (!url) return;
    try {
      if (navigator.share) { await navigator.share({ title: item.title, url }); return; }
    } catch { return; }  // user dismissed the native sheet
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      window.open(`https://wa.me/?text=${encodeURIComponent(`${item.title} ${url}`)}`, '_blank');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-darkBg overflow-y-auto">
      <div className="sticky top-0 z-10 flex items-center gap-3 bg-cardBg/95 backdrop-blur border-b border-bdr px-4 py-3">
        <button onClick={onClose} className="text-aqua text-xl">✕</button>
        <span className="text-text font-bold text-sm truncate flex-1">{tt('الخبر', 'Article')}</span>
        <button onClick={share} className="text-aqua text-sm font-bold flex items-center gap-1.5 shrink-0">
          {copied ? tt('✓ تم النسخ', '✓ Copied') : <>🔗 {tt('مشاركة', 'Share')}</>}
        </button>
      </div>

      {photos.length > 0 && (
        <div className="relative">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={photos[0]} alt="" onClick={() => setPhotoIdx(0)}
            className="w-full max-h-[320px] object-contain bg-darkBg cursor-zoom-in" />
          {photos.length > 1 && (
            <div className="flex gap-2 overflow-x-auto no-scrollbar p-2">
              {photos.slice(1).map((src, i) => (
                // eslint-disable-next-line @next/next/no-img-element
                <img key={i} src={src} alt="" onClick={() => setPhotoIdx(i + 1)}
                  className="h-16 w-24 object-cover rounded-lg border border-bdr shrink-0 cursor-zoom-in" />
              ))}
            </div>
          )}
        </div>
      )}

      <div className="p-4 space-y-4">
        <h1 className="text-aqua font-bold text-xl leading-relaxed">{item.title}</h1>
        <div className="flex items-center gap-3 text-hint text-sm flex-wrap">
          <span className="flex items-center gap-1.5">📅 {formatNewsDate(item.date, locale)}</span>
          {item.competition_name && <span className="flex items-center gap-1.5">🏆 {item.competition_name}</span>}
          {!item.is_published && (
            <span className="text-gold text-[11px] border border-gold/40 bg-gold/10 rounded px-1.5 py-0.5 font-bold">
              {tt('مسودة', 'Draft')}
            </span>
          )}
        </div>
        <hr className="border-bdr" />
        {item.body && <p className="text-text text-base leading-[1.9] whitespace-pre-line">{item.body}</p>}
      </div>

      {photoIdx !== null && (
        <PhotoGalleryViewer
          photos={photos}
          index={photoIdx}
          rtl={locale === 'ar'}
          onClose={() => setPhotoIdx(null)}
          onIndex={setPhotoIdx}
        />
      )}
    </div>
  );
}

export default function NewsList({ compId, search = false }: { compId?: number; search?: boolean }) {
  const tt = useTT();
  const { locale } = useApp();
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const [items, setItems] = useState<TNews[] | null>(null);
  const [selected, setSelected] = useState<TNews | null>(null);
  const [q, setQ] = useState('');
  const [readIds, setReadIds] = useState<Set<string>>(new Set());
  const newsParam = params.get('news');

  useEffect(() => {
    setItems(null);
    tNews({ competition_id: compId }).then(setItems).catch(() => setItems([]));
  }, [compId]);

  // Per-article "NEW" tag by read state: on first ever run, seed the whole
  // current feed as read so only later arrivals light up; then reflect the
  // stored read-set. Independent of the per-feed seen baseline (badge counts).
  useEffect(() => {
    if (!items) return;
    seedReadNewsIfFirstRun(items.map(n => n.id));
    setReadIds(getReadNews());
  }, [items]);

  // Opening an article (by click or by a shared ?news=<id> deep link) marks it
  // read, clearing its NEW tag.
  useEffect(() => {
    if (!selected) return;
    markNewsRead(selected.id);
    setReadIds(prev => (prev.has(String(selected.id)) ? prev : new Set(prev).add(String(selected.id))));
  }, [selected]);

  // The open item is driven by the ?news=<id> param, so every article has its
  // own shareable URL (and the server can inject its WhatsApp preview for it).
  useEffect(() => {
    const id = Number(newsParam);
    if (!newsParam || !id) { setSelected(null); return; }
    const found = items?.find(n => n.id === id);
    if (found) { setSelected(found); return; }
    if (!items) return;  // wait for the list; then fall back to a direct fetch
    let alive = true;
    tNewsItem(id).then(n => { if (alive) setSelected(n); }).catch(() => undefined);
    return () => { alive = false; };
  }, [newsParam, items]);

  // Open/close by editing the URL (preserving the page's other params, e.g. the
  // competition id + tab) so back/forward and deep links both work.
  const openNews = (n: TNews) => {
    const p = new URLSearchParams(params.toString());
    p.set('news', String(n.id));
    router.replace(`${pathname}?${p.toString()}`, { scroll: false });
  };
  const closeNews = () => {
    const p = new URLSearchParams(params.toString());
    p.delete('news');
    const qs = p.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
  };

  if (!items) return <Spinner />;

  const shown = items.filter(n =>
    !q || n.title.toLowerCase().includes(q.toLowerCase())
       || (n.body ?? '').toLowerCase().includes(q.toLowerCase()));

  return (
    <>
      {search && (
        <input value={q} onChange={e => setQ(e.target.value)} placeholder={tt('بحث...', 'Search...')}
          className="w-full bg-cardBg border border-bdr rounded-xl px-4 py-2.5 text-text text-sm placeholder-hint outline-none focus:border-aqua mb-3" />
      )}

      {shown.length === 0 ? (
        <EmptyState icon="📰" text={tt('لا أخبار', 'No news')} />
      ) : (
        <div className="space-y-3">
          {shown.map(n => {
            const thumb = mediaUrl(n.image_path);
            return (
              <button key={n.id} onClick={() => openNews(n)}
                className="w-full bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-2xl overflow-hidden text-start transition-all hover:border-aqua/30 hover:shadow-[0_14px_34px_-20px_rgba(0,0,0,0.7)] active:opacity-80">
                {thumb && (
                  <div className="relative">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={thumb} alt={n.title} className="w-full h-40 object-cover" />
                    <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-cardBg to-transparent" />
                    {n.images.length > 1 && (
                      <span className="absolute top-2 end-2 text-[10px] text-white bg-black/60 rounded-md px-1.5 py-0.5 font-bold tnum">
                        📷 {n.images.length}
                      </span>
                    )}
                  </div>
                )}
                <div className="p-3.5 space-y-1.5">
                  <div className="flex items-start gap-2">
                    <span className="flex-1 text-aqua font-bold text-sm leading-relaxed line-clamp-2">{n.title}</span>
                    {!readIds.has(String(n.id)) && (
                      <span className="flex-shrink-0 text-[10px] text-gold bg-gold/15 border border-gold/40 rounded-md px-1.5 py-0.5 font-extrabold tracking-wide">
                        NEW
                      </span>
                    )}
                  </div>
                  {n.body && <p className="text-teal text-xs line-clamp-2 leading-relaxed">{n.body}</p>}
                  <div className="flex items-center gap-3 text-hint text-xs flex-wrap">
                    <span className="flex items-center gap-1.5">📅 {formatNewsDate(n.date, locale)}</span>
                    {compId == null && n.competition_name && (
                      <span className="flex items-center gap-1.5 truncate">🏆 {n.competition_name}</span>
                    )}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {selected && <NewsDetail item={selected} onClose={closeNews} />}
    </>
  );
}
