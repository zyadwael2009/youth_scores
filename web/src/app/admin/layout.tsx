import { AdminAuthProvider } from '@/context/AdminAuthContext';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  // Full-screen shell that sits above the public site's chrome.
  return (
    <AdminAuthProvider>
      <div dir="rtl" className="fixed inset-0 z-[100] bg-darkBg text-text overflow-y-auto font-arabic">
        {children}
      </div>
    </AdminAuthProvider>
  );
}
