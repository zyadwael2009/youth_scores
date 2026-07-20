import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../core/models/competition_data_model.dart';
import '../../core/models/standing.dart';
import '../../core/l10n/app_l10n.dart';
import '../common/cached_logo.dart';

// W / D / L result for the last-5 form guide
List<String> _teamForm(String teamId, List<Match> matches) {
  final completed = matches
      .where((m) =>
          (m.homeTeamId == teamId || m.awayTeamId == teamId) &&
          m.isCompleted &&
          m.homeScore != null &&
          m.awayScore != null)
      .toList()
    ..sort((a, b) => b.date.compareTo(a.date));
  return completed.take(5).map((m) {
    final isHome = m.homeTeamId == teamId;
    final gf = isHome ? m.homeScore! : m.awayScore!;
    final ga = isHome ? m.awayScore! : m.homeScore!;
    if (gf > ga) return 'W';
    if (gf == ga) return 'D';
    return 'L';
  }).toList();
}

class StandingsTable extends StatelessWidget {
  final List<Standing> standings;
  final List<Team> teams;
  final List<Match> matches;
  final L10n l10n;
  final void Function(String teamId)? onTeamTap;

  const StandingsTable({
    super.key,
    required this.standings,
    required this.teams,
    required this.l10n,
    this.matches = const [],
    this.onTeamTap,
  });

  @override
  Widget build(BuildContext context) {
    if (standings.isEmpty) return const SizedBox.shrink();

    final hasDeduction = teams.any((t) => t.pointDeduction > 0);

    final rules = l10n.isAr
        ? ['النقاط', 'نتيجة المواجهة المباشرة', 'فارق أهداف المواجهة المباشرة', 'فارق الأهداف العام', 'الأهداف المسجلة']
        : ['Points', 'Head-to-head result', 'Head-to-head goal difference', 'Overall goal difference', 'Goals scored'];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: DataTable(
          columnSpacing: 8,
          headingRowHeight: 36,
          dataRowMinHeight: 44,
          dataRowMaxHeight: 56,
          headingRowColor: WidgetStateProperty.all(AppColors.darkBg),
          border: TableBorder(
            horizontalInside: BorderSide(
              color: AppColors.border.withValues(alpha:0.4),
              width: 0.5,
            ),
          ),
          columns: [
            _col(l10n.pos,    width: 28),
            _col(l10n.teamCol, width: 120, left: true),
            _col(l10n.played, width: 30),
            _col(l10n.points, width: 36),
            _col(l10n.gf,     width: 30),
            _col(l10n.ga,     width: 30),
            _col(l10n.gd,     width: 36),
            _col(l10n.won,    width: 28),
            _col(l10n.drawn,  width: 28),
            _col(l10n.lost,   width: 28),
          ],
          rows: List.generate(standings.length, (i) {
            final s    = standings[i];
            final team = teams.where((t) => t.id == s.teamId).firstOrNull;
            return DataRow(
              color: WidgetStateProperty.resolveWith((states) {
                if (i == 0) return AppColors.aqua.withValues(alpha:0.05);
                return i.isEven ? AppColors.darkBg.withValues(alpha:0.3) : null;
              }),
              cells: [
                _posCell(s.position, i),
                _teamCell(team, s.teamId),
                _numCell(s.played),
                _ptsCell(s.points),
                _numCell(s.goalsFor),
                _numCell(s.goalsAgainst),
                _numCell(s.goalDiff, signed: true),
                _numCell(s.won),
                _numCell(s.drawn),
                _numCell(s.lost),
              ],
            );
          }),
        ),
      ),
        ),
        const SizedBox(height: 8),
        // Tiebreaker rules
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          decoration: BoxDecoration(
            color: AppColors.darkBg.withValues(alpha: 0.6),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: AppColors.border.withValues(alpha: 0.5)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                l10n.isAr
                    ? 'معايير الفصل عند التساوي في النقاط'
                    : 'Tiebreaker rules (equal points)',
                style: TextStyle(
                  color: AppColors.hint,
                  fontSize: 9,
                  fontWeight: FontWeight.bold,
                  letterSpacing: 0.5,
                ),
              ),
              const SizedBox(height: 6),
              Wrap(
                spacing: 12,
                runSpacing: 4,
                children: List.generate(rules.length, (i) => Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 14,
                      height: 14,
                      decoration: BoxDecoration(
                        color: AppColors.border,
                        shape: BoxShape.circle,
                      ),
                      child: Center(
                        child: Text(
                          '${i + 1}',
                          style: TextStyle(
                            color: AppColors.teal,
                            fontSize: 7,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 4),
                    Text(
                      rules[i],
                      style: TextStyle(color: AppColors.hint, fontSize: 10),
                    ),
                  ],
                )),
              ),
              if (hasDeduction) ...[
                const SizedBox(height: 6),
                Divider(height: 1, color: AppColors.border.withValues(alpha: 0.4)),
                const SizedBox(height: 6),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                      decoration: BoxDecoration(
                        color: AppColors.red.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(4),
                        border: Border.all(color: AppColors.red.withValues(alpha: 0.5)),
                      ),
                      child: Text(
                        '-N',
                        style: TextStyle(
                          color: AppColors.red,
                          fontSize: 9,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      l10n.isAr
                          ? 'خصم نقاط مطبق على هذا الفريق'
                          : 'point deduction applied to this team',
                      style: TextStyle(color: AppColors.hint, fontSize: 10),
                    ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ],
    );
  }

  DataColumn _col(String label, {double? width, bool left = false}) {
    return DataColumn(
      label: SizedBox(
        width: width,
        child: Text(
          label,
          textAlign: left ? TextAlign.start : TextAlign.center,
          style: TextStyle(
            color: AppColors.aqua,
            fontWeight: FontWeight.bold,
            fontSize: 11,
          ),
        ),
      ),
    );
  }

  DataCell _posCell(int pos, int index) {
    return DataCell(SizedBox(
      width: 28,
      child: Text(
        '$pos',
        textAlign: TextAlign.center,
        style: TextStyle(
          color: index == 0 ? AppColors.aqua : AppColors.teal,
          fontWeight: index == 0 ? FontWeight.bold : FontWeight.normal,
          fontSize: 12,
        ),
      ),
    ));
  }

  DataCell _teamCell(Team? team, String fallback) {
    final id         = team?.id ?? fallback;
    final form       = _teamForm(id, matches);
    final deduction  = team?.pointDeduction ?? 0;

    return DataCell(
      SizedBox(
        width: 120,
        child: Row(
          children: [
            CachedLogo(url: team?.logo, size: 24, borderRadius: 4),
            const SizedBox(width: 6),
            Expanded(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          team?.getName(l10n.locale) ?? fallback,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                              color: AppColors.white, fontSize: 12),
                        ),
                      ),
                      if (deduction > 0)
                        Container(
                          margin: const EdgeInsets.only(left: 4),
                          padding: const EdgeInsets.symmetric(
                              horizontal: 4, vertical: 1),
                          decoration: BoxDecoration(
                            color: AppColors.red.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(4),
                            border: Border.all(
                                color: AppColors.red.withValues(alpha: 0.5)),
                          ),
                          child: Text(
                            '-$deduction',
                            style: TextStyle(
                              color: AppColors.red,
                              fontSize: 9,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                    ],
                  ),
                  if (form.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.only(top: 3),
                      child: Row(
                        children: form.map((r) {
                          final c = r == 'W'
                              ? AppColors.green
                              : r == 'D'
                                  ? AppColors.yellow
                                  : AppColors.red;
                          return Container(
                            width: 11,
                            height: 11,
                            margin: const EdgeInsets.only(right: 2),
                            decoration: BoxDecoration(
                                color: c, shape: BoxShape.circle),
                            child: Center(
                              child: Text(r,
                                  style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 6,
                                      fontWeight: FontWeight.bold)),
                            ),
                          );
                        }).toList(),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
      onTap: onTeamTap != null ? () => onTeamTap!(id) : null,
    );
  }

  DataCell _numCell(int v, {bool signed = false}) {
    final text = signed && v > 0 ? '+$v' : '$v';
    return DataCell(SizedBox(
      width: 30,
      child: Text(
        text,
        textAlign: TextAlign.center,
        style: TextStyle(
          color: signed
              ? (v > 0
                  ? AppColors.green
                  : v < 0
                      ? AppColors.red
                      : AppColors.teal)
              : AppColors.teal,
          fontSize: 12,
        ),
      ),
    ));
  }

  DataCell _ptsCell(int pts) {
    return DataCell(SizedBox(
      width: 36,
      child: Text(
        '$pts',
        textAlign: TextAlign.center,
        style: TextStyle(
          color: AppColors.aqua,
          fontWeight: FontWeight.bold,
          fontSize: 13,
        ),
      ),
    ));
  }
}
