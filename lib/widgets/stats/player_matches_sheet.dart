import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../core/l10n/app_l10n.dart';
import '../../core/models/competition_data_model.dart';
import '../../core/providers/app_provider.dart';
import '../../core/utils/stats_calculator.dart';
import '../../screens/match/match_detail_screen.dart';

enum PlayerStatType { scorers, assists, cleanSheets }

void showPlayerMatchesSheet(
  BuildContext context, {
  required String playerName,
  required String teamId,
  required List<Match> matches,
  required List<Team> teams,
  required PlayerStatType statType,
}) {
  final List<(Match, int)> contributions;
  if (statType == PlayerStatType.cleanSheets) {
    contributions = StatsCalculator.playerCleanSheetMatches(matches, teamId);
  } else {
    contributions = StatsCalculator.playerMatchContributions(
      matches,
      playerName,
      teamId,
      forScorers: statType == PlayerStatType.scorers,
    );
  }
  if (contributions.isEmpty) return;

  Navigator.push(
    context,
    MaterialPageRoute(
      builder: (_) => _PlayerMatchesPage(
        playerName: playerName,
        teamId: teamId,
        contributions: contributions,
        teams: teams,
        statType: statType,
      ),
    ),
  );
}

String _formatDate(String dateStr) {
  try {
    final parts = dateStr.split('-');
    if (parts.length != 3) return dateStr;
    return '${parts[2]}/${parts[1]}/${parts[0]}';
  } catch (_) {
    return dateStr;
  }
}

class _PlayerMatchesPage extends StatelessWidget {
  final String playerName;
  final String teamId;
  final List<(Match, int)> contributions;
  final List<Team> teams;
  final PlayerStatType statType;

  const _PlayerMatchesPage({
    required this.playerName,
    required this.teamId,
    required this.contributions,
    required this.teams,
    required this.statType,
  });

  @override
  Widget build(BuildContext context) {
    final locale     = Provider.of<AppProvider>(context, listen: false).locale;
    final l10n       = L10n(locale);
    final isAr       = l10n.isAr;
    final playerTeam = teams.where((t) => t.id == teamId).firstOrNull;
    final totalCount = contributions.fold<int>(0, (s, e) => s + e.$2);

    final Color statColor;
    final String emoji;
    final String unit;
    switch (statType) {
      case PlayerStatType.scorers:
        statColor = const Color(0xFF22c55e);
        emoji     = '⚽';
        unit      = l10n.goalsUnit;
      case PlayerStatType.assists:
        statColor = AppColors.aqua;
        emoji     = '🎯';
        unit      = l10n.assistUnit;
      case PlayerStatType.cleanSheets:
        statColor = const Color(0xFFa78bfa);
        emoji     = '🛡️';
        unit      = l10n.cleanSheetUnit;
    }

    return Scaffold(
      backgroundColor: AppColors.darkBg,
      body: SafeArea(
        child: Column(
          children: [
            // ── Header bar ────────────────────────────────────────────────
            Container(
              color: AppColors.cardBg,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Row(
                children: [
                  GestureDetector(
                    onTap: () => Navigator.pop(context),
                    child: Text(
                      '✕',
                      style: TextStyle(
                        color: AppColors.aqua,
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          playerName,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            color: AppColors.aqua,
                            fontWeight: FontWeight.bold,
                            fontSize: 14,
                          ),
                        ),
                        if (playerTeam != null)
                          Text(
                            playerTeam.getName(locale),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(color: AppColors.teal, fontSize: 12),
                          ),
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
                    decoration: BoxDecoration(
                      color: statColor.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      '$totalCount $unit',
                      style: TextStyle(
                        color: statColor,
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            Divider(height: 1, color: AppColors.border),

            // ── Match list ────────────────────────────────────────────────
            Expanded(
              child: ListView.builder(
                padding: const EdgeInsets.all(12),
                itemCount: contributions.length,
                itemBuilder: (ctx, i) {
                  final (match, count) = contributions[i];
                  final isHome       = match.homeTeamId == teamId;
                  final opponentId   = isHome ? match.awayTeamId : match.homeTeamId;
                  final opponent     = teams.where((t) => t.id == opponentId).firstOrNull;
                  final opponentName = opponent?.getName(locale) ?? opponentId;

                  return GestureDetector(
                    onTap: () => Navigator.push(
                      ctx,
                      MaterialPageRoute(
                        builder: (_) => MatchDetailScreen(matchId: match.id),
                      ),
                    ),
                    child: Container(
                      margin: const EdgeInsets.only(bottom: 8),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.cardBg,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.border),
                      ),
                      child: Row(
                        children: [
                          // Opponent + date
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '${isAr ? 'ضد' : 'vs'} $opponentName',
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                    color: AppColors.white,
                                    fontSize: 13,
                                  ),
                                ),
                                if (match.date.isNotEmpty)
                                  Padding(
                                    padding: const EdgeInsets.only(top: 3),
                                    child: Text(
                                      _formatDate(match.date),
                                      style: TextStyle(
                                        color: AppColors.hint,
                                        fontSize: 11,
                                      ),
                                    ),
                                  ),
                              ],
                            ),
                          ),

                          const SizedBox(width: 8),

                          // Score + Home/Away
                          Column(
                            children: [
                              Text(
                                '${match.homeScore ?? "-"} - ${match.awayScore ?? "-"}',
                                style: TextStyle(
                                  color: AppColors.aqua,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13,
                                ),
                              ),
                              Text(
                                isHome
                                    ? (isAr ? 'ديار' : 'Home')
                                    : (isAr ? 'ضيف' : 'Away'),
                                style: TextStyle(
                                  color: AppColors.hint,
                                  fontSize: 10,
                                ),
                              ),
                            ],
                          ),

                          const SizedBox(width: 8),

                          // Badge: emoji only for cleansheets, emoji+count for others
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 5),
                            decoration: BoxDecoration(
                              color: statColor.withValues(alpha: 0.12),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              statType == PlayerStatType.cleanSheets
                                  ? emoji
                                  : '$emoji $count',
                              style: TextStyle(
                                color: statColor,
                                fontWeight: FontWeight.bold,
                                fontSize: 12,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
