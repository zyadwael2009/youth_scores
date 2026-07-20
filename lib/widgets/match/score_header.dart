import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../core/models/competition_data_model.dart';
import '../../core/l10n/app_l10n.dart';
import '../../core/utils/date_utils.dart';
import '../common/cached_logo.dart';

class ScoreHeader extends StatelessWidget {
  final Match match;
  final Team? homeTeam;
  final Team? awayTeam;
  final L10n l10n;
  final void Function(String teamId)? onTeamTap;

  const ScoreHeader({
    super.key,
    required this.match,
    this.homeTeam,
    this.awayTeam,
    required this.l10n,
    this.onTeamTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        border: Border.all(color: AppColors.border),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          _teamsRow(),
          const SizedBox(height: 12),
          _infoRow(),
        ],
      ),
    );
  }

  Widget _teamsRow() {
    return Row(
      children: [
        Expanded(child: _teamCol(homeTeam, match.homeTeamId, l10n.homeTeam)),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: _scoreBox(),
        ),
        Expanded(child: _teamCol(awayTeam, match.awayTeamId, l10n.awayTeam)),
      ],
    );
  }

  Widget _teamCol(Team? team, String fallbackId, String label) {
    final col = Column(
      children: [
        CachedLogo(url: team?.logo, size: 64),
        const SizedBox(height: 8),
        Text(
          team?.getName(l10n.locale) ?? fallbackId,
          textAlign: TextAlign.center,
          maxLines: 2,
          style: TextStyle(
            color: AppColors.white,
            fontWeight: FontWeight.bold,
            fontSize: 13,
          ),
        ),
        Text(label, style: TextStyle(color: AppColors.hint, fontSize: 11)),
      ],
    );
    if (onTeamTap == null) return col;
    return GestureDetector(
      onTap: () => onTeamTap!(team?.id ?? fallbackId),
      child: col,
    );
  }

  Widget _scoreBox() {
    if (match.isCompleted && match.homeScore != null) {
      return Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: AppColors.darkBg,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.aqua.withValues(alpha:0.4)),
            ),
            child: Text(
              '${match.homeScore}  -  ${match.awayScore}',
              style: TextStyle(
                color: AppColors.aqua,
                fontSize: 28,
                fontWeight: FontWeight.bold,
                letterSpacing: 2,
              ),
            ),
          ),
          const SizedBox(height: 4),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: AppColors.green.withValues(alpha:0.15),
              borderRadius: BorderRadius.circular(4),
              border: Border.all(color: AppColors.green.withValues(alpha:0.3)),
            ),
            child: Text(
              l10n.completed,
              style: TextStyle(color: AppColors.green, fontSize: 11),
            ),
          ),
          if (match.homePenalty != null && match.awayPenalty != null) ...[
            const SizedBox(height: 6),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: AppColors.orange.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: AppColors.orange.withValues(alpha: 0.4)),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    l10n.isAr ? 'ر.ت  ' : 'Pens  ',
                    style: TextStyle(color: AppColors.hint, fontSize: 11),
                  ),
                  Text(
                    '${match.homePenalty}',
                    style: TextStyle(
                      color: match.homePenalty! > match.awayPenalty!
                          ? AppColors.aqua
                          : AppColors.hint,
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    '  -  ',
                    style: TextStyle(color: AppColors.hint, fontSize: 13),
                  ),
                  Text(
                    '${match.awayPenalty}',
                    style: TextStyle(
                      color: match.awayPenalty! > match.homePenalty!
                          ? AppColors.aqua
                          : AppColors.hint,
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      );
    }

    if (match.isLive) {
      return Column(
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: AppColors.red.withValues(alpha:0.15),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppColors.red),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.circle, color: AppColors.red, size: 8),
                const SizedBox(width: 4),
                Text(
                  'LIVE',
                  style: TextStyle(
                    color: AppColors.red,
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
              ],
            ),
          ),
        ],
      );
    }

    return Column(
      children: [
        Text(
          match.time.isNotEmpty ? match.time : '--:--',
          style: TextStyle(
            color: AppColors.aqua,
            fontSize: 22,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          l10n.upcoming,
          style: TextStyle(color: AppColors.hint, fontSize: 11),
        ),
      ],
    );
  }

  Widget _infoRow() {
    return Wrap(
      alignment: WrapAlignment.center,
      spacing: 16,
      runSpacing: 4,
      children: [
        _infoChip(Icons.calendar_today,
            AppDateUtils.formatMatchDate(match.date, l10n.locale)),
        if (match.week.isNotEmpty)
          _infoChip(Icons.sports_soccer, '${l10n.week} ${match.week}'),
        if (match.venue.isNotEmpty)
          _infoChip(Icons.stadium_outlined, match.venue),
        if (match.group.isNotEmpty)
          _infoChip(
            Icons.group_work_outlined,
            match.group.length <= 2
                ? '${l10n.group} ${match.group}'
                : match.group,
          ),
      ],
    );
  }

  Widget _infoChip(IconData icon, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 13, color: AppColors.hint),
        const SizedBox(width: 4),
        Text(label,
            style: TextStyle(color: AppColors.teal, fontSize: 12)),
      ],
    );
  }
}
