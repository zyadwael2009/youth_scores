import 'package:intl/intl.dart';

class AppDateUtils {
  static String formatMatchDate(String dateStr, String locale) {
    try {
      final dt = DateTime.parse(dateStr);
      final today    = _today();
      final tomorrow = today.add(const Duration(days: 1));
      final yesterday = today.subtract(const Duration(days: 1));

      if (_sameDay(dt, today)) {
        return locale == 'ar' ? 'اليوم' : 'Today';
      }
      if (_sameDay(dt, tomorrow)) {
        return locale == 'ar' ? 'غداً' : 'Tomorrow';
      }
      if (_sameDay(dt, yesterday)) {
        return locale == 'ar' ? 'أمس' : 'Yesterday';
      }
      final pattern = locale == 'ar' ? 'EEEE d MMMM yyyy' : 'EEEE, MMMM d, yyyy';
      return DateFormat(pattern, locale).format(dt);
    } catch (_) {
      return dateStr;
    }
  }

  static String formatNewsDate(String dateStr, String locale) {
    try {
      final dt = DateTime.parse(dateStr);
      final pattern = locale == 'ar' ? 'd MMMM yyyy' : 'MMMM d, yyyy';
      return DateFormat(pattern, locale).format(dt);
    } catch (_) {
      return dateStr;
    }
  }

  static DateTime _today() {
    final n = DateTime.now();
    return DateTime(n.year, n.month, n.day);
  }

  static bool _sameDay(DateTime a, DateTime b) =>
      a.year == b.year && a.month == b.month && a.day == b.day;

  static bool isUpcoming(String dateStr) {
    try {
      final dt = DateTime.parse(dateStr);
      return dt.isAfter(_today());
    } catch (_) {
      return false;
    }
  }

  static bool isToday(String dateStr) {
    try {
      return _sameDay(DateTime.parse(dateStr), _today());
    } catch (_) {
      return false;
    }
  }

  static int compareDates(String a, String b) => a.compareTo(b);

  /// Returns a human-readable countdown label for an upcoming match, or null
  /// if the match is in the past or the date can't be parsed.
  static String? countdownLabel(String date, String time, String locale) {
    if (date.isEmpty) return null;
    try {
      final parts = date.split('-');
      if (parts.length != 3) return null;
      final y = int.parse(parts[0]);
      final mo = int.parse(parts[1]);
      final d  = int.parse(parts[2]);
      int h = 0, mi = 0;
      if (time.isNotEmpty && time.contains(':')) {
        final tp = time.split(':');
        h  = int.tryParse(tp[0]) ?? 0;
        mi = int.tryParse(tp[1]) ?? 0;
      }
      final matchDt = DateTime(y, mo, d, h, mi);
      final now     = DateTime.now();
      if (!matchDt.isAfter(now)) return null;
      final diff = matchDt.difference(now);
      final isAr = locale == 'ar';
      if (diff.inDays >= 2)  return isAr ? 'بعد ${diff.inDays} أيام' : 'in ${diff.inDays}d';
      if (diff.inDays == 1)  return isAr ? 'غداً'                    : 'Tomorrow';
      if (diff.inHours >= 1) return isAr ? 'بعد ${diff.inHours}س'    : 'in ${diff.inHours}h';
      if (diff.inMinutes >= 1) return isAr ? 'بعد ${diff.inMinutes}د' : 'in ${diff.inMinutes}m';
      return isAr ? 'قريباً' : 'Soon';
    } catch (_) {
      return null;
    }
  }
}
