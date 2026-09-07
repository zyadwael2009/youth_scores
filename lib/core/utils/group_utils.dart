// Group ordering + labelling, mirroring the web `groupLabel` / `sortGroups`.
// The canonical order is the sequence the server returns the standings blocks in
// (the admin-set order the standings follow), so every group control — filters,
// headers — reads in that order instead of a raw alphabetical sort.

/// Display name for a group. A short code («A», «1») gets the «Group»/«المجموعة»
/// prefix; a name that already spells the group out is shown as-is.
String groupLabel(String g, String locale) {
  if (g.isEmpty) return '';
  return g.length <= 2 ? (locale == 'ar' ? 'المجموعة $g' : 'Group $g') : g;
}

/// Order group names by the canonical [order]; names not in it fall to the end,
/// ties broken by name. Returns a new list.
List<String> sortGroups(List<String> names, List<String> order) {
  final rank = <String, int>{for (var i = 0; i < order.length; i++) order[i]: i};
  final out = [...names];
  const last = 1 << 30;
  out.sort((a, b) {
    final ra = rank[a] ?? last;
    final rb = rank[b] ?? last;
    return ra != rb ? ra - rb : a.compareTo(b);
  });
  return out;
}

/// Group items by their group key, ordered by the canonical [order] when given,
/// otherwise by first appearance. Preserves item order within a group.
List<MapEntry<String, List<T>>> groupItemsBy<T>(
  List<T> items,
  String Function(T) key, {
  List<String> order = const [],
}) {
  final map = <String, List<T>>{};
  for (final it in items) {
    map.putIfAbsent(key(it), () => []).add(it);
  }
  final keys = order.isEmpty
      ? map.keys.toList()
      : sortGroups(map.keys.toList(), order);
  return [for (final k in keys) MapEntry(k, map[k]!)];
}
