import 'dart:async';
import 'dart:math';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/constants/app_colors.dart';
import '../../core/models/config_model.dart';
import '../../core/providers/app_provider.dart';

class AdInterstitialScreen extends StatefulWidget {
  final WidgetBuilder destinationBuilder;
  final String dataUrl;

  const AdInterstitialScreen({
    super.key,
    required this.destinationBuilder,
    required this.dataUrl,
  });

  @override
  State<AdInterstitialScreen> createState() => _AdInterstitialScreenState();
}

class _AdInterstitialScreenState extends State<AdInterstitialScreen>
    with SingleTickerProviderStateMixin {
  int _countdown = 5;
  bool _canClose = false;
  Timer? _timer;
  late AnimationController _pulseController;
  AdItem? _ad;
  bool _adPicked = false;

  @override
  void initState() {
    super.initState();

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    )..repeat(reverse: true);

    _timer = Timer.periodic(const Duration(seconds: 1), (t) {
      if (!mounted) { t.cancel(); return; }
      setState(() {
        if (_countdown > 1) {
          _countdown--;
        } else {
          _countdown = 0;
          _canClose = true;
          _pulseController.stop();
          t.cancel();
        }
      });
    });

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) context.read<AppProvider>().loadCompetition(widget.dataUrl);
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _pulseController.dispose();
    super.dispose();
  }

  void _close() {
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: widget.destinationBuilder),
    );
  }

  @override
  Widget build(BuildContext context) {
    final ads = context.watch<AppProvider>().config?.ads ?? [];
    if (!_adPicked) {
      _adPicked = true;
      _ad = ads.isNotEmpty ? ads[Random().nextInt(ads.length)] : null;
    }
    final ad = _ad;
    final topPad  = MediaQuery.of(context).padding.top;
    final botPad  = MediaQuery.of(context).padding.bottom;

    // Determine which action buttons to show
    final hasActions = ad != null && (
      ad.whatsappNumber != null ||
      ad.mobileNumber   != null ||
      ad.facebookLink   != null ||
      ad.youtubeVideo   != null ||
      ad.locationUrl    != null
    );

    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        fit: StackFit.expand,
        children: [
          // ── Fullscreen image ───────────────────────────────────────────────
          if (ad?.image != null && ad!.image!.startsWith('http'))
            CachedNetworkImage(
              imageUrl: ad.image!,
              fit: BoxFit.contain,
              width: double.infinity,
              height: double.infinity,
              errorWidget: (_, __, ___) => const _Placeholder(),
            )
          else
            const _Placeholder(),

          // ── Bottom gradient + ad info + actions ────────────────────────────
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            child: Container(
              padding: EdgeInsets.fromLTRB(16, 32, 16, botPad + 16),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.transparent,
                    Colors.black.withValues(alpha: 0.92),
                  ],
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (ad != null)
                    Text(
                      ad.name,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        shadows: [Shadow(color: Colors.black, blurRadius: 8)],
                      ),
                    ),
                  if (hasActions) ...[
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 10,
                      runSpacing: 10,
                      children: [
                        if (ad.whatsappNumber != null)
                          _ActionBtn(
                            icon: Icons.chat,
                            label: 'WhatsApp',
                            color: const Color(0xFF25D366),
                            onTap: () => launchUrl(
                              Uri.parse('https://wa.me/${ad.whatsappNumber}'),
                              mode: LaunchMode.externalApplication,
                            ),
                          ),
                        if (ad.mobileNumber != null)
                          _ActionBtn(
                            icon: Icons.phone,
                            label: 'Call',
                            color: AppColors.teal,
                            onTap: () => launchUrl(
                              Uri.parse('tel:${ad.mobileNumber}'),
                            ),
                          ),
                        if (ad.facebookLink != null)
                          _ActionBtn(
                            icon: Icons.facebook,
                            label: 'Facebook',
                            color: const Color(0xFF1877F2),
                            onTap: () => launchUrl(
                              Uri.parse(ad.facebookLink!),
                              mode: LaunchMode.externalApplication,
                            ),
                          ),
                        if (ad.youtubeVideo != null)
                          _ActionBtn(
                            icon: Icons.play_circle,
                            label: 'YouTube',
                            color: const Color(0xFFFF0000),
                            onTap: () => launchUrl(
                              Uri.parse(ad.youtubeVideo!),
                              mode: LaunchMode.externalApplication,
                            ),
                          ),
                        if (ad.locationUrl != null)
                          _ActionBtn(
                            icon: Icons.map,
                            label: 'Map',
                            color: AppColors.hint,
                            onTap: () => launchUrl(
                              Uri.parse(ad.locationUrl!),
                              mode: LaunchMode.externalApplication,
                            ),
                          ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ),

          // ── Top-right: countdown or close ──────────────────────────────────
          Positioned(
            top: topPad + 12,
            right: 12,
            child: _canClose
                ? _CloseButton(onTap: _close)
                : _CountdownBadge(count: _countdown, pulse: _pulseController),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────

class _Placeholder extends StatelessWidget {
  const _Placeholder();

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.darkBg,
      child: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.campaign, color: AppColors.aqua, size: 100),
            const SizedBox(height: 16),
            Text(
              'إعلان  ·  Advertisement',
              style: TextStyle(color: AppColors.teal, fontSize: 16),
            ),
          ],
        ),
      ),
    );
  }
}

class _ActionBtn extends StatelessWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _ActionBtn({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.18),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: color.withValues(alpha: 0.6)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, color: color, size: 16),
            const SizedBox(width: 6),
            Text(label, style: TextStyle(color: color, fontSize: 13, fontWeight: FontWeight.w600)),
          ],
        ),
      ),
    );
  }
}

class _CloseButton extends StatelessWidget {
  final VoidCallback onTap;
  const _CloseButton({required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 44,
        height: 44,
        decoration: BoxDecoration(
          color: Colors.black.withValues(alpha: 0.65),
          shape: BoxShape.circle,
          border: Border.all(color: Colors.white70, width: 1.5),
        ),
        child: const Icon(Icons.close, color: Colors.white, size: 22),
      ),
    );
  }
}

class _CountdownBadge extends StatelessWidget {
  final int count;
  final AnimationController pulse;
  const _CountdownBadge({required this.count, required this.pulse});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: pulse,
      builder: (_, __) {
        final scale = 1.0 + pulse.value * 0.08;
        return Transform.scale(
          scale: scale,
          child: Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: Colors.black.withValues(alpha: 0.65),
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white38, width: 1.5),
            ),
            child: Center(
              child: Text(
                '$count',
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 18,
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
