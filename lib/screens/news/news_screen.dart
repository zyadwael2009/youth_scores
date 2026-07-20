import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/constants/app_colors.dart';
import '../../core/l10n/app_l10n.dart';
import '../../core/providers/app_provider.dart';
import '../../widgets/common/empty_widget.dart';
import '../../widgets/common/loading_widget.dart';
import '../../widgets/common/search_field.dart';
import '../../widgets/news/news_card.dart';
import 'news_detail_screen.dart';

class NewsScreen extends StatefulWidget {
  const NewsScreen({super.key});

  @override
  State<NewsScreen> createState() => _NewsScreenState();
}

class _NewsScreenState extends State<NewsScreen> {
  final _ctrl  = TextEditingController();
  String _query = '';

  static bool _isRecent(String date) {
    try {
      final dt = DateTime.parse(date);
      return DateTime.now().difference(dt).inDays <= 2;
    } catch (_) {
      return false;
    }
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<AppProvider>();
    final l10n     = L10n(provider.locale);

    if (provider.loadingConfig) return LoadingWidget(message: l10n.loading);

    final locale  = provider.locale;
    final allNews = provider.config?.news ?? [];
    final news    = _query.isEmpty
        ? allNews
        : allNews
            .where((n) =>
                n.getTitle(locale).toLowerCase().contains(_query.toLowerCase()) ||
                (n.getDetails(locale)?.toLowerCase().contains(_query.toLowerCase()) ??
                    false))
            .toList();

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
            onRefresh: () => provider.refreshConfig(),
            color: AppColors.aqua,
            child: news.isEmpty
                ? ListView(children: [EmptyWidget(message: l10n.noNews, icon: Icons.newspaper)])
                : ListView.builder(
                    padding: const EdgeInsets.only(bottom: 16),
                    itemCount: news.length,
                    itemBuilder: (_, i) => NewsCard(
                      item: news[i],
                      locale: l10n.locale,
                      isNew: _isRecent(news[i].date),
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => NewsDetailScreen(item: news[i]),
                        ),
                      ),
                    ),
                  ),
          ),
        ),
      ],
    );
  }
}
