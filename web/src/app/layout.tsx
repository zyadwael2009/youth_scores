import type { Metadata, Viewport } from 'next';
import './globals.css';
import { AppProvider } from '@/context/AppContext';
import BottomNav from '@/components/ui/BottomNav';
import ControlsBar from '@/components/ui/ControlsBar';
import AdOverlay from '@/components/ui/AdOverlay';

export const metadata: Metadata = {
  title: 'بطولات الناشئين | Youth Scores',
  description: 'متابعة بطولات كرة القدم للناشئين في مصر - نتائج، ترتيب، إحصائيات',
  manifest: '/manifest.json',
  icons: { apple: '/icons/icon-192.png' },
  appleWebApp: { capable: true, statusBarStyle: 'black-translucent', title: 'Youth Scores' },
  other: { 'mobile-web-app-capable': 'yes' },
};

export const viewport: Viewport = {
  themeColor: '#15D8FF',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  viewportFit: 'cover',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl" className="dark" suppressHydrationWarning>
      <body className="bg-dark font-arabic antialiased" suppressHydrationWarning>
        <AppProvider>
          <div className="flex flex-col min-h-dvh">
            {/* Held to the same width as the bottom nav and the page content.
                Left full-width it stretched across a desktop viewport while
                everything below it stayed in a phone-width column, and
                object-cover without a height did nothing to stop it. */}
            <div className="w-full max-w-lg mx-auto">
              <img
                src="https://res.cloudinary.com/debq5s4sn/image/upload/v1783684931/youthscores-banner-v2_yqr3hs.png"
                alt="Youth Scores"
                className="w-full h-auto"
              />
            </div>
            <ControlsBar />
            {/* The bottom nav has always been max-w-lg, so on a wide screen the
                content used to run edge to edge under a phone-width nav. The
                whole column is held to one width instead. */}
            <main className="flex-1 pb-20 w-full max-w-lg mx-auto">{children}</main>
            <BottomNav />
            <AdOverlay />
          </div>
        </AppProvider>
      </body>
    </html>
  );
}
