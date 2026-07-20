import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../core/l10n/app_l10n.dart';
import '../../core/models/competition_data_model.dart';
import '../../core/models/config_model.dart';
import '../../core/providers/app_provider.dart';
import '../../core/services/api_service.dart';
import '../../core/utils/date_utils.dart';
import '../../widgets/match/match_card.dart';
import '../news/news_detail_screen.dart';
import '../info/about_screen.dart';

const _bannerUrl =
    'https://res.cloudinary.com/debq5s4sn/image/upload/v1783684931/youthscores-banner-v2_yqr3hs.png';

class HomeTab extends StatefulWidget {
  final VoidCallback onGoToCompetitions;
  final VoidCallback onGoToNews;

  const HomeTab({
    super.key,
    required this.onGoToCompetitions,
    required this.onGoToNews,
  });

  @override
  State<HomeTab> createState() => _HomeTabState();
}

class _HomeTabState extends State<HomeTab> {
  final _api = ApiService();

  List<_MatchEntry> _todayMatches = [];
  bool _loading = false;
  bool _fetched = false;

  Future<void> _fetchTodayMatches(ConfigData? config) async {
    if (config == null) return;

    // Dart weekday: 1=Mon...7=Sun → convert to JS: 0=Sun,1=Mon...6=Sat
    final todayJs = DateTime.now().weekday % 7;

    final urls = <String>{};
    for (final season in config.seasons) {
      for (final comp in season.competitions) {
        for (final age in comp.ages) {
          final days = age.matchDays;
          if (days == null || !days.contains(todayJs)) continue;
          if (age.directMatchesUrl != null) { urls.add(age.directMatchesUrl!); }
          for (final sec in age.sectors) { urls.add(sec.url); }
        }
      }
    }

    setState(() => _loading = true);
    try {
      final results = await Future.wait(
        urls.map((url) => _api
            .fetchCompetition(url)
            .catchError((_) => const CompetitionData(matches: [], teams: [], venues: []))),
      );

      final entries = <_MatchEntry>[];
      for (final data in results) {
        final teamMap = {for (final t in data.teams) t.id: t};
        for (final m in data.matches) {
          if (AppDateUtils.isToday(m.date)) {
            entries.add(_MatchEntry(
              match: m,
              home: teamMap[m.homeTeamId],
              away: teamMap[m.awayTeamId],
            ));
          }
        }
      }

      if (mounted) setState(() { _todayMatches = entries; _loading = false; });
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AppProvider>();
    final l10n = L10n(provider.locale);

    if (provider.config != null && !_fetched) {
      _fetched = true;
      WidgetsBinding.instance.addPostFrameCallback(
        (_) => _fetchTodayMatches(provider.config),
      );
    }

    return RefreshIndicator(
      onRefresh: () async {
        _fetched = true;
        await _fetchTodayMatches(provider.config);
      },
      color: AppColors.aqua,
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          // ── Banner ───────────────────────────────────────────────────────
          CachedNetworkImage(
            imageUrl: _bannerUrl,
            width: double.infinity,
            fit: BoxFit.fitWidth,
            errorWidget: (context, url, err) => const SizedBox.shrink(),
          ),

          // ── Today's matches ──────────────────────────────────────────────
          _SectionHeader(
            title: l10n.todaysMatches,
            actionLabel: l10n.competitions,
            onAction: widget.onGoToCompetitions,
          ),
          if (provider.loadingConfig || _loading)
            _LoadingCard()
          else if (_todayMatches.isEmpty)
            _EmptyCard(
              message: l10n.noMatches,
              buttonLabel: l10n.competitions,
              onButton: widget.onGoToCompetitions,
            )
          else
            ...(_todayMatches.map((e) => Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              child: MatchCard(
                match: e.match,
                homeTeam: e.home,
                awayTeam: e.away,
                locale: provider.locale,
              ),
            ))),

          const SizedBox(height: 8),

          // ── Latest news ──────────────────────────────────────────────────
          _SectionHeader(
            title: l10n.news,
            actionLabel: l10n.more,
            onAction: widget.onGoToNews,
          ),
          if (provider.loadingConfig)
            _LoadingCard()
          else if ((provider.config?.news ?? []).isEmpty)
            _EmptyCard(message: l10n.noNews)
          else
            ...(provider.config!.news.take(3).map((item) => _MiniNewsCard(
              item: item,
              locale: provider.locale,
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => NewsDetailScreen(item: item)),
              ),
            ))),

          // ── Footer ──────────────────────────────────────────────────────
          _InfoFooter(locale: provider.locale),

          const SizedBox(height: 20),
        ],
      ),
    );
  }
}

// ── Data holder ───────────────────────────────────────────────────────────────

class _MatchEntry {
  final Match match;
  final Team? home;
  final Team? away;
  const _MatchEntry({required this.match, this.home, this.away});
}

// ── Section header ────────────────────────────────────────────────────────────

class _SectionHeader extends StatelessWidget {
  final String title;
  final String? actionLabel;
  final VoidCallback? onAction;

  const _SectionHeader({required this.title, this.actionLabel, this.onAction});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      child: Row(
        children: [
          Text(
            title,
            style: TextStyle(
              color: AppColors.white,
              fontWeight: FontWeight.bold,
              fontSize: 15,
            ),
          ),
          const Spacer(),
          if (actionLabel != null && onAction != null)
            GestureDetector(
              onTap: onAction,
              child: Text(
                actionLabel!,
                style: TextStyle(color: AppColors.aqua, fontSize: 12),
              ),
            ),
        ],
      ),
    );
  }
}

// ── Loading card ──────────────────────────────────────────────────────────────

class _LoadingCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Center(
        child: CircularProgressIndicator(color: AppColors.aqua, strokeWidth: 2),
      ),
    );
  }
}

// ── Empty card ────────────────────────────────────────────────────────────────

class _EmptyCard extends StatelessWidget {
  final String message;
  final String? buttonLabel;
  final VoidCallback? onButton;

  const _EmptyCard({required this.message, this.buttonLabel, this.onButton});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(message, style: TextStyle(color: AppColors.teal, fontSize: 13)),
          if (buttonLabel != null && onButton != null) ...[
            const SizedBox(height: 10),
            TextButton(
              onPressed: onButton,
              child: Text(buttonLabel!, style: TextStyle(color: AppColors.aqua)),
            ),
          ],
        ],
      ),
    );
  }
}

// ── Mini news card ────────────────────────────────────────────────────────────

class _MiniNewsCard extends StatelessWidget {
  final NewsItem item;
  final String locale;
  final VoidCallback onTap;

  const _MiniNewsCard({
    required this.item,
    required this.locale,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final thumb = item.allImages.isNotEmpty ? item.allImages.first : null;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: AppColors.cardBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.border),
        ),
        child: Row(
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: thumb != null
                  ? CachedNetworkImage(
                      imageUrl: thumb,
                      width: 72,
                      height: 56,
                      fit: BoxFit.cover,
                      errorWidget: (context, url, err) => _fallback(),
                    )
                  : _fallback(),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.getTitle(locale),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: AppColors.aqua,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    AppDateUtils.formatNewsDate(item.date, locale),
                    style: TextStyle(color: AppColors.hint, fontSize: 10),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _fallback() => Container(
    width: 72,
    height: 56,
    color: AppColors.darkBg,
    child: Icon(Icons.newspaper, color: AppColors.teal, size: 24),
  );
}

// ── Footer with info links ─────────────────────────────────────────────────────

class _InfoFooter extends StatelessWidget {
  final String locale;
  const _InfoFooter({required this.locale});

  void _push(BuildContext ctx, Widget screen) =>
      Navigator.push(ctx, MaterialPageRoute(builder: (_) => screen));

  @override
  Widget build(BuildContext context) {
    final l10n = L10n(locale);
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
      child: Column(
        children: [
          Divider(color: AppColors.border),
          const SizedBox(height: 6),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _link(context, l10n.about,
                  () => _push(context, const AboutScreen())),
              _dot(),
              _link(context, l10n.privacyPolicy,
                  () => _push(context, const PrivacyPolicyScreen())),
              _dot(),
              _link(context, l10n.terms,
                  () => _push(context, const TermsScreen())),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            '© 2025 Youth Scores · youthscores.org',
            style: TextStyle(color: AppColors.border, fontSize: 10),
          ),
        ],
      ),
    );
  }

  Widget _link(BuildContext ctx, String label, VoidCallback onTap) =>
      GestureDetector(
        onTap: onTap,
        child: Text(label,
            style: TextStyle(color: AppColors.hint, fontSize: 11)),
      );

  Widget _dot() => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8),
        child: Text('·', style: TextStyle(color: AppColors.border)),
      );
}
