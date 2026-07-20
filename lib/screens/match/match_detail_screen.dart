import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:share_plus/share_plus.dart';
import '../../core/constants/app_colors.dart';
import '../../core/l10n/app_l10n.dart';
import '../../core/models/competition_data_model.dart';
import '../../core/providers/app_provider.dart';
import '../../widgets/match/score_header.dart';
import '../team/team_detail_screen.dart';

// ── Helpers ───────────────────────────────────────────────────────────────────

const _assistDelimiters = ['صناعة الاهداف', 'assists'];

/// Splits a scorers list into (goals, assists) at the delimiter entry.
(List<String>, List<String>) _splitScorers(List<String> raw) {
  final goals   = <String>[];
  final assists = <String>[];
  bool inAssists = false;
  for (final s in raw) {
    final lower = s.trim().toLowerCase();
    if (_assistDelimiters.any((d) => lower == d.toLowerCase())) {
      inAssists = true;
      continue;
    }
    if (inAssists) { assists.add(s); } else { goals.add(s); }
  }
  return (goals, assists);
}

// ── Screen ────────────────────────────────────────────────────────────────────

class MatchDetailScreen extends StatefulWidget {
  final String matchId;
  const MatchDetailScreen({super.key, required this.matchId});

  @override
  State<MatchDetailScreen> createState() => _MatchDetailScreenState();
}

class _MatchDetailScreenState extends State<MatchDetailScreen> {
  final _pageCtrl = PageController();
  int _page = 0;

  @override
  void dispose() {
    _pageCtrl.dispose();
    super.dispose();
  }

  void _goTo(int i) => _pageCtrl.animateToPage(
        i,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AppProvider>();
    final l10n     = L10n(provider.locale);
    final match    = provider.matchById(widget.matchId);

    if (match == null) {
      return Scaffold(
        appBar: AppBar(title: Text(l10n.matches)),
        body: Center(child: Text(l10n.noData, style: TextStyle(color: AppColors.teal))),
      );
    }

    final homeTeam = provider.teamById(match.homeTeamId);
    final awayTeam = provider.teamById(match.awayTeamId);
    final homeName = homeTeam?.getName(l10n.locale) ?? '';
    final awayName = awayTeam?.getName(l10n.locale) ?? '';

    final (homeGoals,   homeAssists)   = _splitScorers(match.homeScorers);
    final (awayGoals,   awayAssists)   = _splitScorers(match.awayScorers);

    final tabs = [
      _Tab(
        label: l10n.lineup,
        icon: Icons.format_list_numbered,
        count: match.homeSquad.length + match.awaySquad.length,
      ),
      _Tab(
        label: l10n.scorers,
        icon: Icons.sports_score,
        count: homeGoals.length + awayGoals.length,
      ),
      _Tab(
        label: l10n.substitutions,
        icon: Icons.swap_horiz,
        count: match.homeSub.length + match.awaySub.length,
      ),
      _Tab(
        label: l10n.yellowCards,
        icon: Icons.square_rounded,
        count: match.homeYc.length + match.awayYc.length,
      ),
      _Tab(
        label: l10n.redCards,
        icon: Icons.square_rounded,
        count: match.homeRc.length + match.awayRc.length,
      ),
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text(
          '$homeName vs $awayName',
          style: TextStyle(fontSize: 14),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        actions: [
          IconButton(
            icon: Icon(Icons.share),
            onPressed: () => _share(match, homeTeam, awayTeam, l10n),
          ),
        ],
      ),
      body: Column(
        children: [
          // ── Fixed score header ───────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
            child: ScoreHeader(
              match: match,
              homeTeam: homeTeam,
              awayTeam: awayTeam,
              l10n: l10n,
              onTeamTap: (id) => Navigator.push(context,
                  MaterialPageRoute(builder: (_) => TeamDetailScreen(teamId: id))),
            ),
          ),

          // ── Note card ────────────────────────────────────────────────────
          if (match.note != null && match.note!.isNotEmpty)
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
              child: _NoteCard(note: match.note!),
            ),

          // ── Page tab strip ───────────────────────────────────────────────
          const SizedBox(height: 8),
          _TabStrip(tabs: tabs, current: _page, onTap: _goTo),

          // ── 5-page PageView ──────────────────────────────────────────────
          Expanded(
            child: PageView(
              controller: _pageCtrl,
              onPageChanged: (i) => setState(() => _page = i),
              children: [
                // 1 — Lineup
                _TwoColPage(
                  home: match.homeSquad,
                  away: match.awaySquad,
                  homeName: homeName,
                  awayName: awayName,
                  color: AppColors.teal,
                  emptyMessage: l10n.noData,
                ),

                // 2 — Scorers (goals + assists)
                _ScorersPage(
                  homeGoals:   homeGoals,
                  awayGoals:   awayGoals,
                  homeAssists: homeAssists,
                  awayAssists: awayAssists,
                  homeName: homeName,
                  awayName: awayName,
                  l10n: l10n,
                ),

                // 3 — Substitutes
                _TwoColPage(
                  home: match.homeSub,
                  away: match.awaySub,
                  homeName: homeName,
                  awayName: awayName,
                  color: AppColors.teal,
                  emptyMessage: l10n.noData,
                ),

                // 4 — Yellow cards
                _TwoColPage(
                  home: match.homeYc,
                  away: match.awayYc,
                  homeName: homeName,
                  awayName: awayName,
                  color: AppColors.yellow,
                  emptyMessage: l10n.noData,
                ),

                // 5 — Red cards
                _TwoColPage(
                  home: match.homeRc,
                  away: match.awayRc,
                  homeName: homeName,
                  awayName: awayName,
                  color: AppColors.red,
                  emptyMessage: l10n.noData,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _share(Match match, Team? home, Team? away, L10n l10n) {
    final score = match.isCompleted && match.homeScore != null
        ? '${match.homeScore} - ${match.awayScore}'
        : match.time;

    final (homeGoals, _) = _splitScorers(match.homeScorers);
    final (awayGoals, _) = _splitScorers(match.awayScorers);

    final buf = StringBuffer();
    buf.write('${home?.getName(l10n.locale) ?? ''} $score ${away?.getName(l10n.locale) ?? ''}');
    buf.write('\n${match.date}  ${match.time}');
    if (match.venue.isNotEmpty) { buf.write('\n📍 ${match.venue}'); }
    if (homeGoals.isNotEmpty) {
      buf.write('\n⚽ ${home?.getName(l10n.locale) ?? ''}: ${homeGoals.join(' · ')}');
    }
    if (awayGoals.isNotEmpty) {
      buf.write('\n⚽ ${away?.getName(l10n.locale) ?? ''}: ${awayGoals.join(' · ')}');
    }
    buf.write('\n\nبطولات الناشئين | Youth Scores\nyouthscores.org');

    SharePlus.instance.share(ShareParams(text: buf.toString()));
  }
}

// ── Tab strip ─────────────────────────────────────────────────────────────────

class _Tab {
  final String label;
  final IconData icon;
  final int count; // 0 = no data
  const _Tab({required this.label, required this.icon, this.count = 0});
}

class _TabStrip extends StatelessWidget {
  final List<_Tab> tabs;
  final int current;
  final ValueChanged<int> onTap;

  const _TabStrip({required this.tabs, required this.current, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.cardBg,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: List.generate(tabs.length, (i) {
            final active  = i == current;
            final tab     = tabs[i];
            final hasData = tab.count > 0;
            final iconColor = i == 3
                ? (active
                    ? AppColors.yellow
                    : AppColors.yellow.withValues(alpha: hasData ? 0.6 : 0.25))
                : i == 4
                    ? (active
                        ? AppColors.red
                        : AppColors.red.withValues(alpha: hasData ? 0.6 : 0.25))
                    : (active
                        ? AppColors.aqua
                        : hasData
                            ? AppColors.hint
                            : AppColors.hint.withValues(alpha: 0.4));
            final textColor = active
                ? AppColors.aqua
                : hasData
                    ? AppColors.hint
                    : AppColors.hint.withValues(alpha: 0.4);

            return InkWell(
              onTap: () => onTap(i),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  border: Border(
                    bottom: BorderSide(
                      color: active ? AppColors.aqua : Colors.transparent,
                      width: 2.5,
                    ),
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Icon with optional count badge
                    Stack(
                      clipBehavior: Clip.none,
                      children: [
                        Icon(tab.icon, size: 15, color: iconColor),
                        if (hasData && !active)
                          Positioned(
                            top: -5,
                            right: -6,
                            child: Container(
                              padding: const EdgeInsets.all(2),
                              constraints: const BoxConstraints(
                                  minWidth: 13, minHeight: 13),
                              decoration: BoxDecoration(
                                color: i == 3
                                    ? AppColors.yellow
                                    : i == 4
                                        ? AppColors.red
                                        : AppColors.aqua,
                                shape: BoxShape.circle,
                              ),
                              child: Text(
                                '${tab.count}',
                                textAlign: TextAlign.center,
                                style: const TextStyle(
                                  color: Colors.black,
                                  fontSize: 7,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(width: 5),
                    Text(
                      tab.label,
                      style: TextStyle(
                        fontSize: 12,
                        color: textColor,
                        fontWeight: active ? FontWeight.bold : FontWeight.normal,
                      ),
                    ),
                  ],
                ),
              ),
            );
          }),
        ),
      ),
    );
  }
}

// ── Note card ─────────────────────────────────────────────────────────────────

class _NoteCard extends StatelessWidget {
  final String note;
  const _NoteCard({required this.note});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.border),
      ),
      child: Row(
        children: [
          Icon(Icons.info_outline, color: AppColors.hint, size: 16),
          const SizedBox(width: 8),
          Expanded(
            child: Text(note, style: TextStyle(color: AppColors.teal, fontSize: 13)),
          ),
        ],
      ),
    );
  }
}

// ── Generic two-column page ───────────────────────────────────────────────────

class _TwoColPage extends StatelessWidget {
  final List<String> home;
  final List<String> away;
  final String homeName;
  final String awayName;
  final Color color;
  final String emptyMessage;

  const _TwoColPage({
    required this.home,
    required this.away,
    required this.homeName,
    required this.awayName,
    required this.color,
    required this.emptyMessage,
  });

  @override
  Widget build(BuildContext context) {
    if (home.isEmpty && away.isEmpty) {
      return Center(child: Text(emptyMessage, style: TextStyle(color: AppColors.teal)));
    }
    return SingleChildScrollView(
      padding: const EdgeInsets.all(12),
      child: _TwoColTable(
        home: home,
        away: away,
        homeName: homeName,
        awayName: awayName,
        color: color,
      ),
    );
  }
}

// ── Scorers page (goals + assists sections) ───────────────────────────────────

class _ScorersPage extends StatelessWidget {
  final List<String> homeGoals;
  final List<String> awayGoals;
  final List<String> homeAssists;
  final List<String> awayAssists;
  final String homeName;
  final String awayName;
  final L10n l10n;

  const _ScorersPage({
    required this.homeGoals,
    required this.awayGoals,
    required this.homeAssists,
    required this.awayAssists,
    required this.homeName,
    required this.awayName,
    required this.l10n,
  });

  @override
  Widget build(BuildContext context) {
    final hasGoals   = homeGoals.isNotEmpty   || awayGoals.isNotEmpty;
    final hasAssists = homeAssists.isNotEmpty || awayAssists.isNotEmpty;

    if (!hasGoals && !hasAssists) {
      return Center(child: Text(l10n.noData, style: TextStyle(color: AppColors.teal)));
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (hasGoals) ...[
            _SectionLabel(emoji: '⚽', label: l10n.goals),
            const SizedBox(height: 6),
            _TwoColTable(
              home: homeGoals,
              away: awayGoals,
              homeName: homeName,
              awayName: awayName,
              color: AppColors.teal,
            ),
            const SizedBox(height: 16),
          ],
          if (hasAssists) ...[
            _SectionLabel(emoji: '🎯', label: l10n.assists),
            const SizedBox(height: 6),
            _TwoColTable(
              home: homeAssists,
              away: awayAssists,
              homeName: homeName,
              awayName: awayName,
              color: AppColors.teal,
            ),
          ],
        ],
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  final String emoji;
  final String label;
  const _SectionLabel({required this.emoji, required this.label});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 2),
      child: Text(
        '$emoji  $label',
        style: TextStyle(
          color: AppColors.aqua,
          fontWeight: FontWeight.bold,
          fontSize: 14,
        ),
      ),
    );
  }
}

// ── Shared two-column table ───────────────────────────────────────────────────

class _TwoColTable extends StatelessWidget {
  final List<String> home;
  final List<String> away;
  final String homeName;
  final String awayName;
  final Color color;

  const _TwoColTable({
    required this.home,
    required this.away,
    required this.homeName,
    required this.awayName,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    final maxLen = home.length > away.length ? home.length : away.length;

    return Container(
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: [
          // Team name headers
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    homeName,
                    style: TextStyle(
                        color: AppColors.aqua, fontSize: 12, fontWeight: FontWeight.bold),
                  ),
                ),
                Expanded(
                  child: Text(
                    awayName,
                    textAlign: TextAlign.end,
                    style: TextStyle(
                        color: AppColors.aqua, fontSize: 12, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
          ),
          Divider(height: 1, color: AppColors.border),
          // Rows
          ...List.generate(maxLen, (i) {
            final h = i < home.length ? home[i] : '';
            final a = i < away.length ? away[i] : '';
            return Column(
              children: [
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
                  child: Row(
                    children: [
                      Expanded(
                        child: Text(h, style: TextStyle(color: color, fontSize: 13)),
                      ),
                      Expanded(
                        child: Text(
                          a,
                          textAlign: TextAlign.end,
                          style: TextStyle(color: color, fontSize: 13),
                        ),
                      ),
                    ],
                  ),
                ),
                if (i < maxLen - 1)
                  Divider(height: 1, indent: 12, endIndent: 12, color: AppColors.border),
              ],
            );
          }),
          const SizedBox(height: 4),
        ],
      ),
    );
  }
}
