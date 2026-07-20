import '../models/competition_data_model.dart';

class TeamGoalStat {
  final String teamId;
  final Map<String, String> teamName;
  final int goalsFor;
  final int goalsAgainst;

  const TeamGoalStat({
    required this.teamId,
    required this.teamName,
    required this.goalsFor,
    required this.goalsAgainst,
  });

  String getTeamName(String locale) =>
      teamName[locale] ?? teamName['ar'] ?? teamName['en'] ?? '';
}

class PlayerStat {
  final String name;
  final String teamId;
  final Map<String, String> teamName;
  int count;

  PlayerStat({
    required this.name,
    required this.teamId,
    required this.teamName,
    this.count = 0,
  });

  String getTeamName(String locale) =>
      teamName[locale] ?? teamName['ar'] ?? teamName['en'] ?? '';
}

class StatsCalculator {
  static const _assistsDelimiters = ['صناعة الاهداف', 'assists'];

  static List<PlayerStat> topScorers(
    List<Match> matches,
    List<Team> teams,
  ) =>
      _aggregate(matches, teams, scorers: true);

  static List<PlayerStat> topAssisters(
    List<Match> matches,
    List<Team> teams,
  ) =>
      _aggregate(matches, teams, scorers: false);

  static List<PlayerStat> yellowCards(List<Match> matches, List<Team> teams) =>
      _aggregateCards(matches, teams, red: false);

  static List<PlayerStat> redCards(List<Match> matches, List<Team> teams) =>
      _aggregateCards(matches, teams, red: true);

  static List<PlayerStat> _aggregateCards(
    List<Match> matches,
    List<Team> teams, {
    required bool red,
  }) {
    final map = <String, PlayerStat>{};
    for (final m in matches) {
      final home = red ? m.homeRc : m.homeYc;
      final away = red ? m.awayRc : m.awayYc;
      _countCards(home, m.homeTeamId, teams, map);
      _countCards(away, m.awayTeamId, teams, map);
    }
    return map.values.toList()..sort((a, b) => b.count.compareTo(a.count));
  }

  static void _countCards(
    List<String> cards,
    String teamId,
    List<Team> teams,
    Map<String, PlayerStat> map,
  ) {
    final team = teams.where((t) => t.id == teamId).firstOrNull;
    if (team == null) return;
    for (final entry in cards) {
      final name = entry.trim();
      if (name.isEmpty) continue;
      map.putIfAbsent(
        '$teamId:$name',
        () => PlayerStat(name: name, teamId: teamId, teamName: team.name),
      ).count++;
    }
  }

  static List<TeamGoalStat> teamGoalStats(
    List<Match> matches,
    List<Team> teams,
  ) {
    final map = <String, List<int>>{}; // teamId → [goalsFor, goalsAgainst]
    for (final m in matches) {
      if (m.homeScore == null || m.awayScore == null) continue;
      map.putIfAbsent(m.homeTeamId, () => [0, 0]);
      map[m.homeTeamId]![0] += m.homeScore!;
      map[m.homeTeamId]![1] += m.awayScore!;
      map.putIfAbsent(m.awayTeamId, () => [0, 0]);
      map[m.awayTeamId]![0] += m.awayScore!;
      map[m.awayTeamId]![1] += m.homeScore!;
    }
    return map.entries.map((e) {
      final team = teams.where((t) => t.id == e.key).firstOrNull;
      return TeamGoalStat(
        teamId: e.key,
        teamName: team?.name ?? {'ar': e.key, 'en': e.key},
        goalsFor: e.value[0],
        goalsAgainst: e.value[1],
      );
    }).toList();
  }

  static List<PlayerStat> cleanSheets(
    List<Match> matches,
    List<Team> teams,
  ) {
    final map = <String, PlayerStat>{};
    for (final m in matches) {
      if (!m.isCompleted || m.homeScore == null || m.awayScore == null) {
        continue;
      }
      if (m.awayScore == 0) {
        _recordCleanSheet(m.homeTeamId, teams, map);
      }
      if (m.homeScore == 0) {
        _recordCleanSheet(m.awayTeamId, teams, map);
      }
    }
    final result = map.values.toList()..sort((a, b) => b.count.compareTo(a.count));
    return result;
  }

  static void _recordCleanSheet(
    String teamId,
    List<Team> teams,
    Map<String, PlayerStat> map,
  ) {
    final team = teams.where((t) => t.id == teamId).firstOrNull;
    if (team == null) return;
    final gks = team.players?.goalkeepers ?? [];
    if (gks.isEmpty) {
      // No goalkeeper data — record for the team itself
      map.putIfAbsent(
        teamId,
        () => PlayerStat(name: team.getName('ar'), teamId: teamId, teamName: team.name),
      ).count++;
      return;
    }
    for (final gk in gks) {
      map.putIfAbsent(
        '$teamId:$gk',
        () => PlayerStat(name: gk, teamId: teamId, teamName: team.name),
      ).count++;
    }
  }

  static List<PlayerStat> _aggregate(
    List<Match> matches,
    List<Team> teams, {
    required bool scorers,
  }) {
    final map = <String, PlayerStat>{};
    for (final m in matches) {
      if (!m.isCompleted) continue;
      _processEventList(m.homeScorers, m.homeTeamId, teams, map, scorers: scorers);
      _processEventList(m.awayScorers, m.awayTeamId, teams, map, scorers: scorers);
    }
    final result = map.values.toList()..sort((a, b) => b.count.compareTo(a.count));
    return result;
  }

  static void _processEventList(
    List<String> events,
    String teamId,
    List<Team> teams,
    Map<String, PlayerStat> map, {
    required bool scorers,
  }) {
    final team = teams.where((t) => t.id == teamId).firstOrNull;
    if (team == null) return;

    bool inAssistsSection = false;
    for (final entry in events) {
      final lower = entry.toLowerCase().trim();
      if (_assistsDelimiters.any((d) => lower == d.toLowerCase())) {
        inAssistsSection = true;
        continue;
      }
      // scorers=true → skip assist section; scorers=false → only assist section
      if (scorers && inAssistsSection) continue;
      if (!scorers && !inAssistsSection) continue;

      final parsed = _parseEvent(entry);
      final name  = parsed.$1;
      final count = parsed.$2;
      if (name.isEmpty) continue;

      final key = '$teamId:$name';
      map.putIfAbsent(
        key,
        () => PlayerStat(name: name, teamId: teamId, teamName: team.name),
      ).count += count;
    }
  }

  /// Returns all completed matches where [teamId] kept a clean sheet (sorted newest first).
  static List<(Match, int)> playerCleanSheetMatches(
    List<Match> matches,
    String teamId,
  ) {
    final result = <(Match, int)>[];
    for (final m in matches) {
      if (!m.isCompleted || m.homeScore == null || m.awayScore == null) continue;
      final isHome   = m.homeTeamId == teamId;
      if (!isHome && m.awayTeamId != teamId) continue;
      final conceded = isHome ? m.awayScore! : m.homeScore!;
      if (conceded == 0) result.add((m, 1));
    }
    result.sort((a, b) => b.$1.date.compareTo(a.$1.date));
    return result;
  }

  /// Returns all completed matches where [playerName] scored/assisted for [teamId].
  /// Each entry is (match, count_in_that_match).
  static List<(Match, int)> playerMatchContributions(
    List<Match> matches,
    String playerName,
    String teamId, {
    required bool forScorers,
  }) {
    final result = <(Match, int)>[];
    for (final m in matches) {
      if (!m.isCompleted) continue;
      final events = m.homeTeamId == teamId ? m.homeScorers : m.awayScorers;
      int count = 0;
      bool inAssists = false;
      for (final entry in events) {
        final lower = entry.toLowerCase().trim();
        if (_assistsDelimiters.any((d) => lower == d.toLowerCase())) {
          inAssists = true;
          continue;
        }
        if (forScorers && inAssists) continue;
        if (!forScorers && !inAssists) continue;
        final parsed = _parseEvent(entry);
        if (parsed.$1 == playerName) count += parsed.$2;
      }
      if (count > 0) result.add((m, count));
    }
    result.sort((a, b) => b.$1.date.compareTo(a.$1.date));
    return result;
  }

  static (String, int) _parseEvent(String event) {
    // Format: "PlayerName" or "PlayerName x2" or "PlayerName (2)"
    final parts = event.trim().split(RegExp(r'\s+'));
    if (parts.isEmpty) return ('', 1);
    if (parts.length == 1) return (parts[0], 1);

    final last = parts.last;
    final count = int.tryParse(last.replaceAll(RegExp(r'[()x×]'), ''));
    if (count != null) {
      return (parts.sublist(0, parts.length - 1).join(' '), count);
    }
    return (event.trim(), 1);
  }
}
