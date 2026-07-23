import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../core/models/profile_models.dart';
import '../../core/providers/app_provider.dart';
import '../../core/services/api_service.dart';
import '../../widgets/common/cached_logo.dart';

class PlayerDetailScreen extends StatefulWidget {
  final int playerId;
  const PlayerDetailScreen({super.key, required this.playerId});

  @override
  State<PlayerDetailScreen> createState() => _PlayerDetailScreenState();
}

class _PlayerDetailScreenState extends State<PlayerDetailScreen> {
  late Future<PlayerFull> _future;

  @override
  void initState() {
    super.initState();
    _future = ApiService().fetchPlayer(widget.playerId);
  }

  @override
  Widget build(BuildContext context) {
    final locale = context.watch<AppProvider>().locale;
    final isAr = locale == 'ar';

    return Scaffold(
      appBar: AppBar(title: Text(isAr ? 'اللاعب' : 'Player')),
      body: FutureBuilder<PlayerFull>(
        future: _future,
        builder: (context, snap) {
          if (snap.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snap.hasError || snap.data == null) {
            return Center(
              child: Text(isAr ? 'تعذّر تحميل البيانات' : 'Could not load data',
                  style: TextStyle(color: AppColors.teal)),
            );
          }
          final p = snap.data!;
          return ListView(
            padding: const EdgeInsets.all(14),
            children: [
              _header(p, locale, isAr),
              const SizedBox(height: 14),
              _statsRow(p, isAr),
              if (p.career.isNotEmpty) ...[
                const SizedBox(height: 14),
                _sectionTitle(isAr ? 'المسيرة' : 'Career'),
                ...p.career.map((c) => _careerTile(c, locale, isAr)),
              ],
            ],
          );
        },
      ),
    );
  }

  Widget _header(PlayerFull p, String locale, bool isAr) {
    final sub = [
      p.getPosition(locale),
      if (p.birthYear != null) '${isAr ? 'مواليد' : 'Born'} ${p.birthYear}',
      p.getNationality(locale),
    ].whereType<String>().join(' · ');
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(30),
            child: CachedLogo(url: p.photo, size: 60, borderRadius: 30),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(p.getName(locale),
                    style: TextStyle(
                        color: AppColors.aqua, fontSize: 18, fontWeight: FontWeight.bold)),
                if (sub.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(sub, style: TextStyle(color: AppColors.teal, fontSize: 13)),
                ],
                if (p.currentClub != null && p.currentClub!.isNotEmpty) ...[
                  const SizedBox(height: 2),
                  Text(p.currentClub!, style: TextStyle(color: AppColors.hint, fontSize: 12)),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _statsRow(PlayerFull p, bool isAr) {
    Widget cell(String label, int value, Color color) => Expanded(
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 4),
            padding: const EdgeInsets.symmetric(vertical: 14),
            decoration: BoxDecoration(
              color: AppColors.cardBg,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border),
            ),
            child: Column(
              children: [
                Text('$value',
                    style: TextStyle(color: color, fontSize: 22, fontWeight: FontWeight.bold)),
                const SizedBox(height: 4),
                Text(label, style: TextStyle(color: AppColors.hint, fontSize: 11)),
              ],
            ),
          ),
        );
    return Row(
      children: [
        cell(isAr ? 'أهداف' : 'Goals', p.goals, AppColors.green),
        cell(isAr ? 'صناعة' : 'Assists', p.assists, AppColors.aqua),
        cell(isAr ? 'مباريات' : 'Apps', p.appearances, AppColors.white),
      ],
    );
  }

  Widget _sectionTitle(String text) => Padding(
        padding: const EdgeInsets.only(bottom: 8, top: 4, right: 4, left: 4),
        child: Text(text,
            style: TextStyle(color: AppColors.aqua, fontSize: 14, fontWeight: FontWeight.bold)),
      );

  Widget _careerTile(PlayerCareerEntry c, String locale, bool isAr) {
    final season = c.seasonName(locale);
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          CachedLogo(url: c.logo, size: 36),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(c.club,
                          style: TextStyle(color: AppColors.white, fontSize: 14, fontWeight: FontWeight.w600)),
                    ),
                    if (c.current)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: AppColors.green.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(isAr ? 'حالي' : 'Current',
                            style: TextStyle(color: AppColors.green, fontSize: 10)),
                      ),
                  ],
                ),
                if (season.isNotEmpty)
                  Text(season, style: TextStyle(color: AppColors.hint, fontSize: 12)),
              ],
            ),
          ),
          if (c.goals > 0)
            Text('${c.goals} ⚽',
                style: TextStyle(color: AppColors.aqua, fontSize: 13, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
