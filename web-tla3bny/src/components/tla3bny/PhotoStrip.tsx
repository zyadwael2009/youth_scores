'use client';
import { useEffect, useRef, useState } from 'react';
import { useApp } from '@/context/AppContext';
import PhotoGalleryViewer from './PhotoGalleryViewer';

// A horizontal strip of rectangular photos: on wide screens several sit side by
// side; on small screens they overflow and left/right arrows appear (only while
// there is more to see) to hint you can swipe. Tapping a photo opens it in a
// 90%-of-screen popup you can swipe through and close with ✕ / tap-outside.
export default function PhotoStrip({ photos }: { photos: string[] }) {
  const { locale } = useApp();
  const ref = useRef<HTMLDivElement>(null);
  const [overflow, setOverflow] = useState(false);
  const [viewIdx, setViewIdx] = useState<number | null>(null);

  const update = () => {
    const el = ref.current;
    if (el) setOverflow(el.scrollWidth > el.clientWidth + 4);
  };
  useEffect(() => {
    update();
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, [photos.length]);

  const scroll = (dir: number) => {
    const el = ref.current;
    if (el) el.scrollBy({ left: dir * el.clientWidth * 0.8, behavior: 'smooth' });
  };

  if (!photos.length) return null;
  return (
    <div className="relative">
      <div ref={ref} className="flex gap-3 overflow-x-auto no-scrollbar snap-x snap-mandatory pb-1">
        {photos.map((src, i) => (
          <button key={i} type="button" onClick={() => setViewIdx(i)}
            className="snap-center shrink-0 w-72 sm:w-60 aspect-[4/3] rounded-xl overflow-hidden border border-bdr hover:border-aqua/60 transition-colors cursor-zoom-in">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={src} alt="" className="w-full h-full object-cover" />
          </button>
        ))}
      </div>
      {overflow && (
        <>
          <button type="button" onClick={() => scroll(-1)} aria-label="السابق"
            className="absolute top-1/2 -translate-y-1/2 left-1 w-9 h-9 rounded-full bg-black/55 text-white text-xl grid place-items-center backdrop-blur-sm hover:bg-black/75 transition-colors">‹</button>
          <button type="button" onClick={() => scroll(1)} aria-label="التالي"
            className="absolute top-1/2 -translate-y-1/2 right-1 w-9 h-9 rounded-full bg-black/55 text-white text-xl grid place-items-center backdrop-blur-sm hover:bg-black/75 transition-colors">›</button>
        </>
      )}
      {viewIdx !== null && (
        <PhotoGalleryViewer
          photos={photos}
          index={viewIdx}
          rtl={locale === 'ar'}
          windowed
          onClose={() => setViewIdx(null)}
          onIndex={setViewIdx}
        />
      )}
    </div>
  );
}
