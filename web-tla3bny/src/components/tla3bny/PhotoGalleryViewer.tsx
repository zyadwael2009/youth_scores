'use client';
import { useEffect, useRef, useState } from 'react';
import { useTT } from './kit';

// Fullscreen image with pinch / double-tap / wheel zoom and drag-to-pan. Pointer
// events cover both touch and mouse; no external dependency. Zoom resets when the
// photo changes. When not zoomed, a horizontal drag is treated as a swipe and
// reported via onSwipe(+1 = next, -1 = prev). Direction follows reading order: in
// RTL a right-swipe advances, in LTR a left-swipe advances. Ported from the
// youthscores web news viewer.
function ZoomImage({ src, rtl, onSwipe }: { src: string; rtl?: boolean; onSwipe?: (dir: number) => void }) {
  const [scale, setScale] = useState(1);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [active, setActive] = useState(false);
  const pts = useRef<Map<number, { x: number; y: number }>>(new Map());
  const pinch = useRef<{ dist: number; scale: number } | null>(null);
  const pan = useRef<{ x: number; y: number; px: number; py: number } | null>(null);
  const lastTap = useRef(0);

  useEffect(() => { setScale(1); setPos({ x: 0, y: 0 }); }, [src]);

  const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
  const gap = (a: { x: number; y: number }, b: { x: number; y: number }) => Math.hypot(a.x - b.x, a.y - b.y);

  const down = (e: React.PointerEvent) => {
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    pts.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    setActive(true);
    if (pts.current.size === 2) {
      const [a, b] = [...pts.current.values()];
      pinch.current = { dist: gap(a, b), scale };
      pan.current = null;
    } else if (pts.current.size === 1) {
      pan.current = { x: e.clientX, y: e.clientY, px: pos.x, py: pos.y };
      const now = Date.now();
      if (now - lastTap.current < 300) {           // double-tap toggles zoom
        if (scale > 1) { setScale(1); setPos({ x: 0, y: 0 }); } else setScale(2.5);
        lastTap.current = 0;
      } else {
        lastTap.current = now;
      }
    }
  };

  const move = (e: React.PointerEvent) => {
    if (!pts.current.has(e.pointerId)) return;
    pts.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (pts.current.size === 2 && pinch.current) {
      const [a, b] = [...pts.current.values()];
      setScale(clamp(pinch.current.scale * (gap(a, b) / pinch.current.dist), 1, 4));
    } else if (pts.current.size === 1 && scale > 1 && pan.current) {
      setPos({ x: pan.current.px + (e.clientX - pan.current.x), y: pan.current.py + (e.clientY - pan.current.y) });
    }
  };

  const up = (e: React.PointerEvent) => {
    pts.current.delete(e.pointerId);
    if (pts.current.size < 2) pinch.current = null;
    if (pts.current.size === 0) {
      const start = pan.current;
      pan.current = null;
      setActive(false);
      if (scale <= 1) {
        setPos({ x: 0, y: 0 });
        // Not zoomed: a dominant horizontal drag navigates between photos.
        if (start && onSwipe) {
          const dx = e.clientX - start.x, dy = e.clientY - start.y;
          // LTR: swipe left (dx<0) = next. RTL: swipe right (dx>0) = next.
          if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) onSwipe((dx < 0 ? 1 : -1) * (rtl ? -1 : 1));
        }
      }
    }
  };

  const wheel = (e: React.WheelEvent) => {
    setScale(s => {
      const next = clamp(s * (e.deltaY < 0 ? 1.15 : 0.87), 1, 4);
      if (next <= 1) setPos({ x: 0, y: 0 });
      return next;
    });
  };

  return (
    <div className="flex-1 overflow-hidden flex items-center justify-center touch-none"
      onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={up} onWheel={wheel}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt="" draggable={false}
        style={{ transform: `translate(${pos.x}px, ${pos.y}px) scale(${scale})`, transition: active ? 'none' : 'transform 0.15s ease-out', cursor: scale > 1 ? 'grab' : 'default' }}
        className="max-w-full max-h-full object-contain select-none" />
    </div>
  );
}

/**
 * A gallery of the zoomable photo plus counter, keyboard/desktop arrows and dot
 * navigation. `index` is controlled by the parent so the same URL/state drives
 * which photo is shown. Escape / arrow keys work on desktop; pinch, double tap
 * and swipe work on touch. By default it fills the screen; pass `windowed` to
 * show it as a 90%-of-screen popup over a dimmed backdrop (tap outside to close).
 */
export default function PhotoGalleryViewer({
  photos, index, rtl, windowed, onClose, onIndex,
}: {
  photos: string[];
  index: number;
  rtl?: boolean;
  windowed?: boolean;
  onClose: () => void;
  onIndex: (i: number) => void;
}) {
  const tt = useTT();
  const go = (dir: number) => onIndex(Math.min(photos.length - 1, Math.max(0, index + dir)));

  // Desktop keyboard: arrows navigate, Escape closes.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') go(1);
      else if (e.key === 'ArrowLeft') go(-1);
      else if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index, photos.length]);

  const body = (
    <>
      <div className="flex items-center justify-between px-4 py-3 bg-black/50">
        <button onClick={onClose} className="text-white text-2xl" aria-label={tt('إغلاق', 'Close')}>✕</button>
        <span className="text-white/60 text-[11px]">{tt('قرّب بإصبعين أو اضغط مرتين', 'Pinch or double-tap to zoom')}</span>
        {photos.length > 1
          ? <span className="text-white text-sm tnum">{index + 1} / {photos.length}</span>
          : <span className="w-6" />}
      </div>

      <ZoomImage key={index} src={photos[index]} rtl={rtl} onSwipe={photos.length > 1 ? go : undefined} />

      {photos.length > 1 && (
        <>
          {/* Desktop arrows; hidden on touch where swipe is natural. */}
          <button onClick={() => go(-1)} disabled={index === 0} aria-label={tt('السابق', 'Previous')}
            className="hidden sm:flex absolute left-2 top-1/2 -translate-y-1/2 h-11 w-11 items-center justify-center rounded-full bg-black/40 text-white text-2xl disabled:opacity-25">‹</button>
          <button onClick={() => go(1)} disabled={index === photos.length - 1} aria-label={tt('التالي', 'Next')}
            className="hidden sm:flex absolute right-2 top-1/2 -translate-y-1/2 h-11 w-11 items-center justify-center rounded-full bg-black/40 text-white text-2xl disabled:opacity-25">›</button>
          <div className="flex justify-center gap-2 pb-8">
            {photos.map((_, i) => (
              <button key={i} onClick={() => onIndex(i)} aria-label={`${i + 1}`}
                className={`rounded-full transition-all ${i === index ? 'bg-white w-4 h-2' : 'bg-white/40 w-2 h-2'}`} />
            ))}
          </div>
        </>
      )}
    </>
  );

  // Windowed: a 90%-of-screen panel centred over a dimmed backdrop; tapping the
  // backdrop closes it. Fullscreen (default) fills the viewport.
  if (windowed) {
    return (
      <div className="fixed inset-0 z-[60] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
        onClick={onClose}>
        <div onClick={e => e.stopPropagation()}
          className="relative w-[90vw] h-[90vh] bg-black rounded-2xl overflow-hidden flex flex-col shadow-2xl">
          {body}
        </div>
      </div>
    );
  }

  return <div className="fixed inset-0 z-[60] bg-black flex flex-col">{body}</div>;
}
