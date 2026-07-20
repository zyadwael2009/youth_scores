import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../core/providers/app_provider.dart';
import '../../core/utils/stats_calculator.dart';

class PlayerStatItem extends StatelessWidget {
  final int rank;
  final PlayerStat stat;
  final String unit;
  final VoidCallback? onTap;

  const PlayerStatItem({
    super.key,
    required this.rank,
    required this.stat,
    required this.unit,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final locale = Provider.of<AppProvider>(context, listen: false).locale;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: Container(
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: rank == 1
              ? const Color(0xFFFFD700).withValues(alpha: 0.5)
              : rank == 2
                  ? const Color(0xFFC0C0C0).withValues(alpha: 0.4)
                  : rank == 3
                      ? const Color(0xFFCD7F32).withValues(alpha: 0.4)
                      : AppColors.border,
        ),
      ),
      child: Row(
        children: [
          SizedBox(
            width: 28,
            child: Text(
              rank == 1 ? '🥇' : rank == 2 ? '🥈' : rank == 3 ? '🥉' : '$rank',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: rank == 1
                    ? const Color(0xFFFFD700)
                    : rank == 2
                        ? const Color(0xFFC0C0C0)
                        : rank == 3
                            ? const Color(0xFFCD7F32)
                            : AppColors.hint,
                fontWeight: rank <= 3 ? FontWeight.bold : FontWeight.normal,
                fontSize: rank <= 3 ? 16 : 13,
              ),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  stat.name,
                  style: TextStyle(
                    color: AppColors.white,
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                  ),
                ),
                Text(
                  stat.getTeamName(locale),
                  style: TextStyle(
                    color: AppColors.teal,
                    fontSize: 11,
                  ),
                ),
              ],
            ),
          ),
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: AppColors.aqua.withValues(alpha:0.12),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              '${stat.count} $unit',
              style: TextStyle(
                color: AppColors.aqua,
                fontWeight: FontWeight.bold,
                fontSize: 13,
              ),
            ),
          ),
        ],
      ),
      ),
    );
  }
}
