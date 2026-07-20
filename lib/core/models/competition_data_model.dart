class CompetitionData {
  final List<Match> matches;
  final List<Team> teams;
  final List<String> venues;

  const CompetitionData({
    required this.matches,
    required this.teams,
    required this.venues,
  });

  factory CompetitionData.fromJson(Map<String, dynamic> json) => CompetitionData(
    matches: (json['matches'] as List? ?? [])
        .whereType<Map<String, dynamic>>()
        .map(Match.fromJson)
        .toList(),
    teams: (json['teams'] as List? ?? [])
        .whereType<Map<String, dynamic>>()
        .map(Team.fromJson)
        .toList(),
    venues: (json['venues'] as List? ?? [])
        .whereType<String>()
        .toList(),
  );
}

class Match {
  final String id;
  final String group;
  final String week;
  final String date;
  final String time;
  final String homeTeamId;
  final String awayTeamId;
  final String venue;
  final String status;
  final String? note;
  final int? homeScore;
  final int? awayScore;
  final List<String> homeScorers;
  final List<String> awayScorers;
  final int? homePenalty;
  final int? awayPenalty;
  final List<String> homeYc;
  final List<String> awayYc;
  final List<String> homeRc;
  final List<String> awayRc;
  final List<String> homeSub;
  final List<String> awaySub;
  final List<String> homeSquad;
  final List<String> awaySquad;
  final String stage;

  const Match({
    required this.id,
    required this.group,
    required this.week,
    required this.date,
    required this.time,
    required this.homeTeamId,
    required this.awayTeamId,
    required this.venue,
    required this.status,
    this.note,
    this.homeScore,
    this.awayScore,
    required this.homeScorers,
    required this.awayScorers,
    this.homePenalty,
    this.awayPenalty,
    required this.homeYc,
    required this.awayYc,
    required this.homeRc,
    required this.awayRc,
    required this.homeSub,
    required this.awaySub,
    required this.homeSquad,
    required this.awaySquad,
    required this.stage,
  });

  bool get isCompleted => status.toLowerCase() == 'completed';
  bool get isLive      => status.toLowerCase() == 'live';
  bool get isKnockout  => stage.toLowerCase() == 'knockout';

  static List<String> _parseList(dynamic raw) {
    if (raw == null) return const [];
    if (raw is List) {
      return raw
          .map((e) => e?.toString() ?? '')
          .where((s) => s.isNotEmpty)
          .toList();
    }
    if (raw is String && raw.isNotEmpty) return [raw];
    return const [];
  }

  factory Match.fromJson(Map<String, dynamic> json) => Match(
    id:          json['match_id']?.toString() ?? '',
    group:       json['group']?.toString() ?? '',
    week:        json['week']?.toString() ?? '',
    date:        json['date']?.toString() ?? '',
    time:        json['time']?.toString() ?? '',
    homeTeamId:  json['home_team_id']?.toString() ?? '',
    awayTeamId:  json['away_team_id']?.toString() ?? '',
    venue:       json['venue']?.toString() ?? '',
    status:      json['status']?.toString() ?? '',
    note:        json['note']?.toString(),
    homeScore:   _parseInt(json['home_score']),
    awayScore:   _parseInt(json['away_score']),
    homeScorers: _parseList(json['home_scorers']),
    awayScorers: _parseList(json['away_scorers']),
    homePenalty: _parseInt(json['home_penalty']),
    awayPenalty: _parseInt(json['away_penalty']),
    homeYc:      _parseList(json['home_yc']),
    awayYc:      _parseList(json['away_yc']),
    homeRc:      _parseList(json['home_rc']),
    awayRc:      _parseList(json['away_rc']),
    homeSub:     _parseList(json['home_sub']),
    awaySub:     _parseList(json['away_sub']),
    homeSquad:   _parseList(json['home_squade']),
    awaySquad:   _parseList(json['away_squade']),
    stage:       json['stage']?.toString() ?? '',
  );

  static int? _parseInt(dynamic v) {
    if (v is int) return v;
    if (v == null) return null;
    return int.tryParse(v.toString());
  }
}

class Team {
  final String id;
  final Map<String, String>? group;
  final Map<String, String> name;
  final String? logo;
  final String? field;
  final String? fieldUrl;
  final Map<String, String>? city;
  final String? information;
  final Players? players;
  final int pointDeduction;

  const Team({
    required this.id,
    this.group,
    required this.name,
    this.logo,
    this.field,
    this.fieldUrl,
    this.city,
    this.information,
    this.players,
    this.pointDeduction = 0,
  });

  String getName(String locale) =>
      name[locale] ?? name['ar'] ?? name['en'] ?? '';

  // Stable key used for filtering (matches match.group which is always Arabic).
  String? get groupKey => group?['ar'] ?? group?['en'];

  String? getGroup(String locale) {
    if (group == null) return null;
    final val = group![locale] ?? group!['ar'] ?? group!['en'];
    return (val == null || val.isEmpty) ? null : val;
  }

  String? getCity(String locale) {
    if (city == null) return null;
    final val = city![locale] ?? city!['ar'] ?? city!['en'];
    return (val == null || val.isEmpty) ? null : val;
  }

  static Map<String, String>? _toLocalizedMap(dynamic raw) {
    if (raw == null) return null;
    if (raw is Map) {
      final map = Map<String, String>.from(
        raw.map((k, v) => MapEntry(k.toString(), v?.toString() ?? '')),
      );
      return map.isEmpty ? null : map;
    }
    if (raw is String && raw.isNotEmpty) return {'ar': raw, 'en': raw};
    return null;
  }

  factory Team.fromJson(Map<String, dynamic> json) {
    final nameRaw = json['name'];
    Map<String, String> nameMap = {};
    if (nameRaw is Map) {
      nameMap = Map<String, String>.from(
        nameRaw.map((k, v) => MapEntry(k.toString(), v?.toString() ?? '')),
      );
    } else if (nameRaw is String) {
      nameMap = {'ar': nameRaw, 'en': nameRaw};
    }
    return Team(
      id:             json['team_id']?.toString() ?? '',
      group:          _toLocalizedMap(json['group']),
      name:           nameMap,
      logo:           json['logo']?.toString(),
      field:          json['field']?.toString(),
      fieldUrl:       json['fieldurl']?.toString(),
      city:           _toLocalizedMap(json['city']),
      information:    json['information']?.toString(),
      players: json['players'] is Map<String, dynamic>
          ? Players.fromJson(json['players'] as Map<String, dynamic>)
          : null,
      pointDeduction: int.tryParse(json['point_deduction']?.toString() ?? '0') ?? 0,
    );
  }
}

class Players {
  final List<String> coach;
  final List<String> goalkeepers;
  final List<String> defenders;
  final List<String> midfielders;
  final List<String> attackers;

  const Players({
    this.coach = const [],
    required this.goalkeepers,
    required this.defenders,
    required this.midfielders,
    required this.attackers,
  });

  bool get isEmpty =>
      coach.isEmpty &&
      goalkeepers.isEmpty &&
      defenders.isEmpty &&
      midfielders.isEmpty &&
      attackers.isEmpty;

  static List<String> _parseList(dynamic raw) {
    if (raw == null) return const [];
    if (raw is List) {
      return raw
          .map((e) => e?.toString() ?? '')
          .where((s) => s.isNotEmpty)
          .toList();
    }
    if (raw is String && raw.isNotEmpty) return [raw];
    return const [];
  }

  factory Players.fromJson(Map<String, dynamic> json) => Players(
    coach:       _parseList(json['coach']),
    goalkeepers: _parseList(json['goalkeepers']),
    defenders:   _parseList(json['defenders']),
    midfielders: _parseList(json['midfielders']),
    attackers:   _parseList(json['attackers']),
  );
}
