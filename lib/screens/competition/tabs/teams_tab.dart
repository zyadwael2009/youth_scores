import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../core/constants/app_colors.dart';
import '../../../core/l10n/app_l10n.dart';
import '../../../core/models/competition_data_model.dart';
import '../../../core/providers/app_provider.dart';
import '../../../widgets/common/empty_widget.dart';
import '../../../widgets/common/search_field.dart';
import '../../team/team_detail_screen.dart';

class TeamsTab extends StatefulWidget {
  const TeamsTab({super.key});

  @override
  State<TeamsTab> createState() => _TeamsTabState();
}

class _TeamsTabState extends State<TeamsTab>
    with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;

  final _ctrl = TextEditingController();
  String _query = '';
  final Map<String, bool> _expanded = {};

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  /// Groups teams with group keys sorted alphabetically (empty key last).
  Map<String, List<Team>> _group(List<Team> teams) {
    final map = <String, List<Team>>{};
    for (final t in teams) {
      final g = (t.groupKey ?? '').trim();
      map.putIfAbsent(g, () => []).add(t);
    }
    final sortedKeys = map.keys.toList()
      ..sort((a, b) {
        if (a.isEmpty) return 1;
        if (b.isEmpty) return -1;
        return a.compareTo(b);
      });
    return {for (final k in sortedKeys) k: map[k]!};
  }

  void _navigate(BuildContext context, String teamId) {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => TeamDetailScreen(teamId: teamId)),
    );
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    final provider = context.watch<AppProvider>();
    final comp     = provider.competition!;
    final l10n     = L10n(provider.locale);

    // Filter by search query, keep original order within each group
    final locale = provider.locale;
    final filtered = comp.teams
        .where((t) => t.getName(locale).toLowerCase().contains(_query.toLowerCase()))
        .toList();

    final grouped = _group(filtered);

    // Determine whether to show grouped view:
    // more than one distinct non-empty group key = grouped
    final groupKeys = grouped.keys.where((k) => k.isNotEmpty).toList();
    final isGrouped = groupKeys.length > 1;

    // Seed expanded state (default open)
    if (isGrouped) {
      for (final g in grouped.keys) {
        _expanded.putIfAbsent(g, () => true);
      }
    }

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: SearchField(
            controller: _ctrl,
            hint: l10n.search,
            onChanged: (v) => setState(() => _query = v),
          ),
        ),
        Expanded(
          child: RefreshIndicator(
            onRefresh: () => context.read<AppProvider>().refreshCompetition(),
            color: AppColors.aqua,
            child: filtered.isEmpty
                ? ListView(children: [EmptyWidget(message: l10n.noTeams, icon: Icons.shield_outlined)])
                : isGrouped
                    ? _GroupedList(
                        grouped: grouped,
                        expanded: _expanded,
                        onToggle: (g) => setState(() => _expanded[g] = !(_expanded[g] ?? true)),
                        onTeamTap: (id) => _navigate(context, id),
                      )
                    : _FlatList(
                        teams: filtered,
                        onTeamTap: (id) => _navigate(context, id),
                      ),
          ),
        ),
      ],
    );
  }
}

// ── Flat list (single group / no groups) ─────────────────────────────────────

class _FlatList extends StatelessWidget {
  final List<Team> teams;
  final ValueChanged<String> onTeamTap;

  const _FlatList({required this.teams, required this.onTeamTap});

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.only(bottom: 16),
      itemCount: teams.length,
      itemBuilder: (_, i) => _TeamNameTile(
        team: teams[i],
        onTap: () => onTeamTap(teams[i].id),
      ),
    );
  }
}

// ── Grouped list with collapsible headers ─────────────────────────────────────

class _GroupedList extends StatelessWidget {
  final Map<String, List<Team>> grouped;
  final Map<String, bool> expanded;
  final ValueChanged<String> onToggle;
  final ValueChanged<String> onTeamTap;

  const _GroupedList({
    required this.grouped,
    required this.expanded,
    required this.onToggle,
    required this.onTeamTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(12, 4, 12, 16),
      children: grouped.entries.map((entry) {
        final gName  = entry.key;
        final teams  = entry.value;
        final isOpen = expanded[gName] ?? true;

        // Teams with no group — flat, no header
        if (gName.isEmpty) {
          return Column(
            children: teams
                .map((t) => _TeamNameTile(team: t, onTap: () => onTeamTap(t.id)))
                .toList(),
          );
        }

        return Card(
          margin: const EdgeInsets.only(bottom: 10),
          child: Column(
            children: [
              // ── Collapsible group header ──────────────────────────────────
              InkWell(
                onTap: () => onToggle(gName),
                borderRadius: BorderRadius.vertical(
                  top: const Radius.circular(12),
                  bottom: isOpen ? Radius.zero : const Radius.circular(12),
                ),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: AppColors.darkBg,
                    borderRadius: BorderRadius.vertical(
                      top: const Radius.circular(12),
                      bottom: isOpen ? Radius.zero : const Radius.circular(12),
                    ),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        isOpen ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                        color: AppColors.aqua,
                        size: 20,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          gName,
                          style: TextStyle(
                            color: AppColors.aqua,
                            fontWeight: FontWeight.bold,
                            fontSize: 13,
                          ),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: AppColors.aqua.withValues(alpha: 0.12),
                          borderRadius: BorderRadius.circular(10),
                        ),
                        child: Text(
                          '${teams.length}',
                          style: TextStyle(
                            color: AppColors.aqua,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              // ── Team list ─────────────────────────────────────────────────
              if (isOpen)
                Column(
                  children: teams
                      .map((t) => _TeamNameTile(team: t, onTap: () => onTeamTap(t.id)))
                      .toList(),
                ),
            ],
          ),
        );
      }).toList(),
    );
  }
}

// ── Single team row ───────────────────────────────────────────────────────────

class _TeamNameTile extends StatelessWidget {
  final Team team;
  final VoidCallback onTap;

  const _TeamNameTile({required this.team, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          border: Border(bottom: BorderSide(color: AppColors.border, width: 0.5)),
        ),
        child: Row(
          children: [
            Expanded(
              child: Text(
                team.getName(Provider.of<AppProvider>(context, listen: false).locale),
                style: TextStyle(
                  color: AppColors.white,
                  fontSize: 15,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            Icon(Icons.chevron_right, color: AppColors.border, size: 20),
          ],
        ),
      ),
    );
  }
}
