// Minimal date helpers used by the tla3bny components (a trimmed copy of the
// youthscores web utils — only what this app needs).

export function todayStr(): string {
  const t = new Date();
  return `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, '0')}-${String(t.getDate()).padStart(2, '0')}`;
}

export function formatMatchDate(dateStr: string, locale: string): string {
  if (!dateStr) return locale === 'ar' ? 'غير محدد' : 'TBD';
  try {
    const dt = new Date(dateStr);
    const today = todayStr();
    const tomorrow = new Date(); tomorrow.setDate(tomorrow.getDate() + 1);
    const tomStr = `${tomorrow.getFullYear()}-${String(tomorrow.getMonth() + 1).padStart(2, '0')}-${String(tomorrow.getDate()).padStart(2, '0')}`;
    if (dateStr === today) return locale === 'ar' ? 'اليوم' : 'Today';
    if (dateStr === tomStr) return locale === 'ar' ? 'غداً' : 'Tomorrow';
    return dt.toLocaleDateString(locale === 'ar' ? 'ar-EG' : 'en-US', { weekday: 'long', day: 'numeric', month: 'long' });
  } catch { return dateStr; }
}
