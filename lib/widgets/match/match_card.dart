import 'package:flutter/material.dart';
import '../../core/constants/app_colors.dart';
import '../../core/models/competition_data_model.dart';
import '../../core/utils/date_utils.dart';
import '../common/cached_logo.dart';

class MatchCard extends StatelessWidget {
  final Match match;
  final Team? homeTeam;
  final Team? awayTeam;
  final VoidCallback? onTap;
  final String locale;

  const MatchCard({
    super.key,
    required this.match,
    this.homeTeam,
    this.awayTeam,
    this.onTap,
    this.locale = 'ar',
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Column(
            children: [
              _buildTeamRow(),
              if (match.venue.isNotEmpty) ...[
                const SizedBox(height: 4),
                Text(
                  match.venue,
                  style: TextStyle(color: AppColors.hint, fontSize: 11),
                  textAlign: TextAlign.center,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTeamRow() {
    final homeWon = match.isCompleted &&
        match.homeScore != null &&
        (match.homeScore! > match.awayScore! ||
         (match.homeScore == match.awayScore &&
          match.homePenalty != null && match.homePenalty! > match.awayPenalty!));
    final awayWon = match.isCompleted &&
        match.awayScore != null &&
        (match.awayScore! > match.homeScore! ||
         (match.homeScore == match.awayScore &&
          match.awayPenalty != null && match.awayPenalty! > match.homePenalty!));

    return Row(
      children: [
        Expanded(child: _teamCol(homeTeam, match.homeTeamId, winner: homeWon)),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8),
          child: _buildScoreOrTime(),
        ),
        Expanded(child: _teamCol(awayTeam, match.awayTeamId, winner: awayWon)),
      ],
    );
  }

  Widget _teamCol(Team? team, String fallback, {required bool winner}) {
    return Column(
      children: [
        // Winner gets a subtle golden glow ring around the logo
        winner
            ? Container(
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFFFFD700).withValues(alpha: 0.45),
                      blurRadius: 10,
                      spreadRadius: 2,
                    ),
                  ],
                ),
                child: CachedLogo(url: team?.logo, size: 40),
              )
            : CachedLogo(url: team?.logo, size: 40),
        const SizedBox(height: 4),
        Text(
          team?.getName(locale) ?? fallback,
          textAlign: TextAlign.center,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(
            color: winner ? AppColors.aqua : AppColors.white,
            fontSize: 12,
            fontWeight: winner ? FontWeight.bold : FontWeight.w600,
          ),
        ),
      ],
    );
  }

  Widget _buildScoreOrTime() {
    // Completed
    if (match.isCompleted && match.homeScore != null) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: AppColors.darkBg,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: AppColors.border),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              '${match.homeScore} - ${match.awayScore}',
              style: TextStyle(
                color: AppColors.aqua,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            if (match.homePenalty != null && match.awayPenalty != null)
              Text(
                'ر.ت: ${match.homePenalty} - ${match.awayPenalty}',
                style: TextStyle(color: AppColors.orange, fontSize: 10),
              ),
          ],
        ),
      );
    }

    // Live
    if (match.isLive) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: AppColors.red.withValues(alpha: 0.2),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: AppColors.red),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const _PulsingDot(),
            const SizedBox(height: 2),
            Text(
              match.time.isNotEmpty ? match.time : 'LIVE',
              style: TextStyle(
                color: AppColors.red,
                fontSize: 13,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      );
    }

    // Postponed
    if (match.status.toLowerCase() == 'postponed') {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
        decoration: BoxDecoration(
          color: AppColors.orange.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: AppColors.orange.withValues(alpha: 0.5)),
        ),
        child: Text(
          locale == 'ar' ? 'مؤجلة' : 'PPD',
          style: TextStyle(
            color: AppColors.orange,
            fontSize: 11,
            fontWeight: FontWeight.bold,
          ),
        ),
      );
    }

    // Upcoming
    final countdown = AppDateUtils.countdownLabel(match.date, match.time, locale);
    return Column(
      children: [
        Text(
          match.time.isNotEmpty ? match.time : '--:--',
          style: TextStyle(
            color: AppColors.aqua,
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        if (countdown != null)
          Text(
            countdown,
            style: TextStyle(
              color: AppColors.orange,
              fontSize: 9,
              fontWeight: FontWeight.w600,
            ),
            textAlign: TextAlign.center,
          ),
        if (!AppDateUtils.isToday(match.date))
          Text(
            AppDateUtils.formatMatchDate(match.date, locale),
            style: TextStyle(color: AppColors.hint, fontSize: 10),
            textAlign: TextAlign.center,
          ),
      ],
    );
  }
}

// ── Pulsing live indicator ─────────────────────────────────────────────────────

class _PulsingDot extends StatefulWidget {
  const _PulsingDot();

  @override
  State<_PulsingDot> createState() => _PulsingDotState();
}

class _PulsingDotState extends State<_PulsingDot>
    with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double>   _scale;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat(reverse: true);
    _scale = Tween<double>(begin: 0.6, end: 1.4).animate(
      CurvedAnimation(parent: _ctrl, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ScaleTransition(
      scale: _scale,
      child: Icon(Icons.circle, color: AppColors.red, size: 8),
    );
  }
}
