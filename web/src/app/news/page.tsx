'use client';
import { useState } from 'react';
import Image from 'next/image';
import { useApp } from '@/context/AppContext';
import AppBar from '@/components/ui/AppBar';
import Spinner from '@/components/ui/Spinner';
import { formatNewsDate, isRecent, localize } from '@/lib/utils';
import type { NewsItem } from '@/lib/types';

function NewsDetail({ item, locale, onClose }: { item: NewsItem; locale: string; onClose: () => void }) {
  const photos = item.images?.length ? item.images : (item.image?.startsWith('http') ? [item.image] : []);
  const [photoIdx, setPhotoIdx] = useState<number | null>(null);
  const isAr = locale === 'ar';
  const title   = localize(item.title, locale);
  const details = localize(item.details, locale) || null;

  return (
    <div className="fixed inset-0 z-50 bg-darkBg flex flex-col">
      <div className="flex items-center bg-cardBg border-b border-bdr px-4 py-3 gap-3">
        <button onClick={onClose} className="text-aqua text-xl font-bold">✕</button>
        <span className="flex-1 text-aqua font-bold text-sm">{isAr ? 'الأخبار' : 'News'}</span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* Gallery */}
        {photos.length > 0 && (
          <div className="relative">
            {photos.length === 1 ? (
              <img src={photos[0]} alt={title} className="w-full aspect-video object-cover cursor-pointer" onClick={() => setPhotoIdx(0)} />
            ) : (
              <div className="flex gap-1 p-1 overflow-x-auto no-scrollbar">
                {photos.map((p, i) => (
                  <img key={i} src={p} alt="" className="h-48 aspect-video object-cover rounded-lg flex-shrink-0 cursor-pointer" onClick={() => setPhotoIdx(i)} />
                ))}
              </div>
            )}
          </div>
        )}

        <div className="p-4 space-y-4">
          <h1 className="text-aqua font-bold text-xl leading-relaxed">{title}</h1>
          <div className="flex items-center gap-2 text-hint text-sm">
            <span>📅</span>
            <span>{formatNewsDate(item.date, locale)}</span>
          </div>
          <hr className="border-bdr" />
          {details && <p className="text-text text-base leading-[1.9] whitespace-pre-line">{details}</p>}
        </div>
      </div>

      {/* Fullscreen photo viewer */}
      {photoIdx !== null && (
        <div className="fixed inset-0 z-[60] bg-black flex flex-col">
          <div className="flex items-center justify-between px-4 py-3 bg-black/50">
            <button onClick={() => setPhotoIdx(null)} className="text-white text-2xl">✕</button>
            {photos.length > 1 && <span className="text-white text-sm">{photoIdx + 1} / {photos.length}</span>}
          </div>
          <div className="flex-1 flex items-center justify-center overflow-hidden">
            <img src={photos[photoIdx]} alt="" className="max-w-full max-h-full object-contain" />
          </div>
          {photos.length > 1 && (
            <div className="flex justify-center gap-2 pb-8">
              {photos.map((_, i) => (
                <button key={i} onClick={() => setPhotoIdx(i)}
                  className={`rounded-full transition-all ${i === photoIdx ? 'bg-white w-4 h-2' : 'bg-white/40 w-2 h-2'}`} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function NewsPage() {
  const { config, configLoading, configError, refreshConfig, locale } = useApp();
  const [q, setQ] = useState('');
  const [selected, setSelected] = useState<NewsItem | null>(null);
  const isAr = locale === 'ar';

  const news = (config?.news ?? []).filter(n =>
    !q || localize(n.title, locale).toLowerCase().includes(q.toLowerCase()) || localize(n.details, locale).toLowerCase().includes(q.toLowerCase())
  );

  return (
    <>
      <AppBar title={isAr ? 'الأخبار' : 'News'} />

      <div className="p-3">
        <input value={q} onChange={e => setQ(e.target.value)} placeholder={isAr ? 'بحث...' : 'Search...'}
          className="w-full bg-cardBg border border-bdr rounded-xl px-4 py-2.5 text-text text-sm placeholder-hint outline-none focus:border-aqua mb-3" />

        {configLoading && !config && <Spinner />}
        {configError && (
          <div className="text-center py-8 space-y-3">
            <p className="text-red-400 text-sm">{configError}</p>
            <button onClick={refreshConfig} className="bg-aqua text-on-accent font-bold px-5 py-2 rounded-xl text-sm">
              {isAr ? 'إعادة المحاولة' : 'Retry'}
            </button>
          </div>
        )}

        <div className="space-y-3">
          {news.map((item, i) => {
            const recent = isRecent(item.date);
            const thumb  = item.images?.[0] ?? (item.image?.startsWith('http') ? item.image : null);
            return (
              <button key={i} onClick={() => setSelected(item)} className="w-full bg-gradient-to-b from-cardBg to-cardBg2 border border-bdr rounded-2xl overflow-hidden text-start transition-all hover:border-aqua/30 hover:shadow-[0_14px_34px_-20px_rgba(0,0,0,0.7)] active:opacity-80">
                {thumb && (
                  <div className="relative">
                    <img src={thumb} alt={localize(item.title, locale)} className="w-full h-40 object-cover" />
                    <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-cardBg to-transparent" />
                  </div>
                )}
                <div className="p-3.5 space-y-1.5">
                  <div className="flex items-start gap-2">
                    <span className="flex-1 text-aqua font-bold text-sm leading-relaxed line-clamp-2">{localize(item.title, locale)}</span>
                    {recent && (
                      <span className="flex-shrink-0 text-[10px] text-gold bg-gold/15 border border-gold/40 rounded-md px-1.5 py-0.5 font-extrabold tracking-wide">NEW</span>
                    )}
                  </div>
                  {localize(item.details, locale) && <p className="text-teal text-xs line-clamp-2 leading-relaxed">{localize(item.details, locale)}</p>}
                  <div className="flex items-center gap-1.5 text-hint text-xs">
                    <span>📅</span>
                    <span>{formatNewsDate(item.date, locale)}</span>
                  </div>
                </div>
              </button>
            );
          })}
          {!configLoading && news.length === 0 && (
            <p className="text-center text-hint py-12">{isAr ? 'لا توجد أخبار' : 'No news'}</p>
          )}
        </div>
      </div>

      {selected && <NewsDetail item={selected} locale={locale} onClose={() => setSelected(null)} />}
    </>
  );
}
