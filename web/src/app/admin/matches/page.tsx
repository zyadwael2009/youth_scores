'use client';
import AdminShell from '@/components/admin/AdminShell';
import MatchesEntry from '@/components/admin/MatchesEntry';

// Kept as a route so existing links and bookmarks still work; the nav points at
// the المباريات tab inside المسابقات instead.
export default function AdminMatchesPage() {
  return <AdminShell title="إدخال المباريات"><MatchesEntry /></AdminShell>;
}
