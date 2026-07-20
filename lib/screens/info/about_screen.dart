import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/constants/app_colors.dart';
import '../../core/l10n/app_l10n.dart';
import '../../core/providers/app_provider.dart';

class AboutScreen extends StatelessWidget {
  const AboutScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final locale = context.watch<AppProvider>().locale;
    final l10n   = L10n(locale);
    final isAr   = l10n.isAr;
    final sections = isAr ? _sectionsAr : _sectionsEn;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.about)),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          // ── Hero ──────────────────────────────────────────────────────────
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Column(
              children: [
                const Text('⚽', style: TextStyle(fontSize: 56)),
                const SizedBox(height: 10),
                Text(
                  'Youth Scores',
                  style: TextStyle(
                    color: AppColors.aqua,
                    fontWeight: FontWeight.bold,
                    fontSize: 22,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'بطولات الناشئين | youthscores.org',
                  style: TextStyle(color: AppColors.teal, fontSize: 12),
                ),
              ],
            ),
          ),

          // ── Sections ──────────────────────────────────────────────────────
          ...sections.map((sec) => _SectionCard(sec: sec)),

          const SizedBox(height: 8),

          // ── Contact CTA ───────────────────────────────────────────────────
          Container(
            margin: const EdgeInsets.symmetric(vertical: 4),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.aqua.withValues(alpha: 0.05),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.aqua.withValues(alpha: 0.2)),
            ),
            child: Column(
              children: [
                Text(
                  isAr
                      ? 'هل لديك نتيجة مباراة أو استفسار؟'
                      : 'Have a match result or inquiry?',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: AppColors.teal, fontSize: 13),
                ),
                const SizedBox(height: 12),
                ElevatedButton(
                  onPressed: () async {
                    final uri = Uri.parse('https://wa.me/201064428821');
                    try {
                      await launchUrl(uri, mode: LaunchMode.externalApplication);
                    } catch (_) {
                      await launchUrl(uri, mode: LaunchMode.platformDefault);
                    }
                  },
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.aqua,
                    foregroundColor: AppColors.darkBg,
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10)),
                  ),
                  child: Text(l10n.contactUs,
                      style: const TextStyle(fontWeight: FontWeight.bold)),
                ),
              ],
            ),
          ),

          // ── Footer links ──────────────────────────────────────────────────
          _FooterLinks(locale: locale),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}

// ── Privacy Policy ────────────────────────────────────────────────────────────

class PrivacyPolicyScreen extends StatelessWidget {
  const PrivacyPolicyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final locale = context.watch<AppProvider>().locale;
    final l10n   = L10n(locale);
    final isAr   = l10n.isAr;
    final sections = isAr ? _privacyAr : _privacyEn;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.privacyPolicy)),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: Column(
              children: [
                const Text('🔒', style: TextStyle(fontSize: 48)),
                const SizedBox(height: 8),
                Text(
                  l10n.privacyPolicy,
                  style: TextStyle(
                    color: AppColors.aqua,
                    fontWeight: FontWeight.bold,
                    fontSize: 20,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${l10n.lastUpdated}: 21 ديسمبر 2025',
                  style: TextStyle(color: AppColors.hint, fontSize: 11),
                ),
              ],
            ),
          ),
          ...sections.map((sec) => _SectionCard(sec: sec)),
          _FooterLinks(locale: locale),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}

// ── Terms ─────────────────────────────────────────────────────────────────────

class TermsScreen extends StatelessWidget {
  const TermsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final locale = context.watch<AppProvider>().locale;
    final l10n   = L10n(locale);
    final isAr   = l10n.isAr;
    final sections = isAr ? _termsAr : _termsEn;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.terms)),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: Column(
              children: [
                const Text('📋', style: TextStyle(fontSize: 48)),
                const SizedBox(height: 8),
                Text(
                  l10n.terms,
                  style: TextStyle(
                    color: AppColors.aqua,
                    fontWeight: FontWeight.bold,
                    fontSize: 20,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  isAr
                      ? 'يرجى قراءة هذه الشروط بعناية'
                      : 'Please read these terms carefully',
                  style: TextStyle(color: AppColors.hint, fontSize: 11),
                ),
              ],
            ),
          ),
          ...sections.map((sec) => _SectionCard(sec: sec)),
          _FooterLinks(locale: locale),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}

// ── Shared widgets ────────────────────────────────────────────────────────────

class _SectionCard extends StatelessWidget {
  final _Section sec;
  const _SectionCard({required this.sec});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.cardBg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (sec.emoji != null) ...[
                Text(sec.emoji!, style: const TextStyle(fontSize: 20)),
                const SizedBox(width: 8),
              ],
              Expanded(
                child: Text(
                  sec.title,
                  style: TextStyle(
                    color: AppColors.aqua,
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
                ),
              ),
            ],
          ),
          if (sec.body != null) ...[
            const SizedBox(height: 8),
            Text(
              sec.body!,
              style: TextStyle(
                color: AppColors.teal,
                fontSize: 13,
                height: 1.8,
              ),
            ),
          ],
          if (sec.items != null) ...[
            const SizedBox(height: 8),
            ...sec.items!.map(
              (item) => Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('•  ',
                        style: TextStyle(
                            color: AppColors.aqua,
                            fontWeight: FontWeight.bold)),
                    Expanded(
                      child: Text(
                        item,
                        style: TextStyle(
                            color: AppColors.teal, fontSize: 13, height: 1.6),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _FooterLinks extends StatelessWidget {
  final String locale;
  const _FooterLinks({required this.locale});

  @override
  Widget build(BuildContext context) {
    final l10n = L10n(locale);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          _link(context, l10n.about,         () => _push(context, const AboutScreen())),
          _dot(),
          _link(context, l10n.privacyPolicy, () => _push(context, const PrivacyPolicyScreen())),
          _dot(),
          _link(context, l10n.terms,         () => _push(context, const TermsScreen())),
        ],
      ),
    );
  }

  void _push(BuildContext ctx, Widget screen) =>
      Navigator.push(ctx, MaterialPageRoute(builder: (_) => screen));

  Widget _link(BuildContext context, String label, VoidCallback onTap) =>
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

// ── Data model ────────────────────────────────────────────────────────────────

class _Section {
  final String? emoji;
  final String  title;
  final String? body;
  final List<String>? items;
  const _Section({this.emoji, required this.title, this.body, this.items});
}

// ── About content ─────────────────────────────────────────────────────────────

const _sectionsAr = [
  _Section(emoji: '🏆', title: 'من نحن',
    body: 'Youth Scores هو تطبيق مخصص لمتابعة وتوثيق نتائج بطولات كرة القدم للناشئين في مصر. نغطي جميع المراحل السنية من تحت 13 سنة حتى تحت 21 سنة، ونوفر نتائج المباريات والترتيب والإحصائيات بشكل مستمر.',
  ),
  _Section(emoji: '📖', title: 'قصتنا',
    body: 'نشأت المنصة استجابةً لحاجة حقيقية؛ كان أولياء الأمور والمهتمون بكرة قدم الناشئين يجدون صعوبة في الحصول على نتائج المباريات ومعلومات البطولات في مكان واحد. جمعنا كل هذا في منصة واحدة سهلة الاستخدام.',
  ),
  _Section(emoji: '⚽', title: 'خدماتنا',
    items: [
      'نتائج المباريات فور انتهائها',
      'جداول الترتيب والمجموعات',
      'إحصائيات شاملة (أهداف، تمريرات حاسمة، بطاقات)',
      'معلومات الفرق والملاعب',
      'أخبار كرة قدم الناشئين',
    ],
  ),
  _Section(emoji: '📊', title: 'مصادر البيانات',
    body: 'نجمع المعلومات عن طريق المتابعة الشخصية للمباريات، ورسائل أولياء الأمور واللاعبين، وصفحات الأندية الرسمية على وسائل التواصل الاجتماعي، ومراسلين متطوعين. هذه البيانات ليست بيانات رسمية من الاتحاد المصري لكرة القدم.',
  ),
  _Section(emoji: '👥', title: 'جمهورنا',
    body: 'نخدم أولياء أمور اللاعبين الراغبين في متابعة أداء أبنائهم، واللاعبين الشباب، والمدربين، والأندية، وجميع المهتمين بتطوير كرة القدم في مصر.',
  ),
  _Section(emoji: '⚠️', title: 'إخلاء المسؤولية',
    body: 'Youth Scores هو تطبيق غير رسمي ومستقل، ولا ينتمي إلى الاتحاد المصري لكرة القدم أو أي جهة رسمية أخرى. جميع البيانات المنشورة هي لأغراض إعلامية فقط.',
  ),
];

const _sectionsEn = [
  _Section(emoji: '🏆', title: 'About Us',
    body: 'Youth Scores is an app dedicated to tracking and documenting youth football tournament results in Egypt. We cover all age groups from under-13 to under-21, providing match results, standings, and statistics continuously.',
  ),
  _Section(emoji: '📖', title: 'Our Story',
    body: 'The platform was born from a real need — parents and football enthusiasts struggled to find match results and tournament information in one place. We brought everything together into one easy-to-use platform.',
  ),
  _Section(emoji: '⚽', title: 'Our Services',
    items: [
      'Match results as soon as they finish',
      'Standings tables and group tables',
      'Comprehensive statistics (goals, assists, cards)',
      'Team and venue information',
      'Youth football news',
    ],
  ),
  _Section(emoji: '📊', title: 'Data Sources',
    body: 'We collect information through personal match monitoring, messages from parents and players, official club social media pages, and volunteer reporters. This data is not official data from the Egyptian Football Association.',
  ),
  _Section(emoji: '👥', title: 'Our Audience',
    body: "We serve parents who want to follow their children's performance, young players, coaches, clubs, and all those interested in football development in Egypt.",
  ),
  _Section(emoji: '⚠️', title: 'Disclaimer',
    body: 'Youth Scores is an unofficial, independent app and is not affiliated with the Egyptian Football Association or any other official body. All published data is for informational purposes only.',
  ),
];

// ── Privacy Policy content ────────────────────────────────────────────────────

const _privacyAr = [
  _Section(title: '1. مقدمة',
    body: 'نحن في Youth Scores نلتزم بحماية خصوصيتك. تشرح هذه السياسة كيفية جمع معلوماتك الشخصية واستخدامها وحمايتها عند استخدام التطبيق.',
  ),
  _Section(title: '2. المعلومات التي نجمعها',
    items: [
      'طوعياً: عناوين البريد الإلكتروني وأرقام الهواتف والرسائل التي تشاركها معنا',
      'تلقائياً: عناوين IP ونوع الجهاز والصفحات المزارة والتوقيت',
    ],
  ),
  _Section(title: '3. أغراض الاستخدام',
    items: [
      'تحسين المحتوى والخدمات',
      'الرد على الاستفسارات',
      'تحليل استخدام التطبيق',
      'الكشف عن الاحتيال وحماية الأمان',
    ],
  ),
  _Section(title: '4. مشاركة البيانات مع الأطراف الثالثة',
    body: 'لا نبيع بياناتك الشخصية لأي طرف. قد نشارك البيانات مع مزودي الخدمة ضمن الحدود القانونية اللازمة فقط.',
  ),
  _Section(title: '5. أمان البيانات',
    body: 'نطبق تدابير أمنية معقولة لحماية بياناتك. مع ذلك، لا يمكن ضمان أمان نقل البيانات عبر الإنترنت بنسبة 100%.',
  ),
  _Section(title: '6. خصوصية الأطفال',
    body: 'لا نجمع عن قصد بيانات شخصية من مستخدمين أقل من 13 عاماً. إذا اكتشفنا ذلك، سنحذف البيانات فوراً.',
  ),
  _Section(title: '7. حقوق المستخدم',
    items: [
      'الوصول إلى بياناتك الشخصية',
      'تصحيح أو حذف بياناتك',
      'الاعتراض على معالجة بياناتك',
    ],
  ),
  _Section(title: '8. التواصل',
    body: 'للاستفسار عن سياسة الخصوصية، تواصل معنا عبر: zyadwael2009@gmail.com أو واتساب: 01064428821',
  ),
];

const _privacyEn = [
  _Section(title: '1. Introduction',
    body: 'At Youth Scores, we are committed to protecting your privacy. This policy explains how we collect, use, and protect your personal information when using our app.',
  ),
  _Section(title: '2. Information We Collect',
    items: [
      'Voluntarily: email addresses, phone numbers, and messages you share with us',
      'Automatically: IP addresses, device type, visited pages, and timestamps',
    ],
  ),
  _Section(title: '3. How We Use Your Information',
    items: [
      'Improving content and services',
      'Responding to inquiries',
      'Analyzing app usage',
      'Fraud detection and security',
    ],
  ),
  _Section(title: '4. Third-Party Data Sharing',
    body: 'We do not sell your personal data. We may share data with service providers only within the necessary legal limits.',
  ),
  _Section(title: '5. Data Security',
    body: 'We implement reasonable security measures to protect your data. However, 100% security of Internet data transmission cannot be guaranteed.',
  ),
  _Section(title: "6. Children's Privacy",
    body: 'We do not intentionally collect personal data from users under 13. If discovered, we will delete the data immediately.',
  ),
  _Section(title: '7. Your Rights',
    items: [
      'Access your personal data',
      'Correct or delete your data',
      'Object to data processing',
    ],
  ),
  _Section(title: '8. Contact',
    body: 'For questions about this privacy policy, contact us at: zyadwael2009@gmail.com or WhatsApp: 01064428821',
  ),
];

// ── Terms content ─────────────────────────────────────────────────────────────

const _termsAr = [
  _Section(title: '1. وصف الخدمة',
    body: 'يقدم Youth Scores معلومات عن بطولات كرة القدم للناشئين في مصر، تشمل نتائج المباريات، والترتيب، وإحصائيات اللاعبين، وأخبار رياضية. باستخدامك للتطبيق، فأنت توافق على هذه الشروط.',
  ),
  _Section(title: '2. إخلاء المسؤولية عن البيانات',
    body: 'البيانات المنشورة على Youth Scores ليست بيانات رسمية من الاتحاد المصري لكرة القدم أو أي جهة رسمية. يتم جمعها عن طريق المتابعة الشخصية للمباريات، ورسائل أولياء الأمور واللاعبين، وصفحات الأندية على وسائل التواصل الاجتماعي.',
  ),
  _Section(title: '3. الاستخدام المحظور',
    items: [
      'نسخ أو إعادة نشر محتوى التطبيق بشكل جماعي دون إذن مسبق',
      'استخدام أدوات آلية للوصول إلى البيانات',
      'نشر معلومات كاذبة أو مضللة',
      'محاولة الوصول غير المصرح به إلى أنظمة التطبيق',
    ],
  ),
  _Section(title: '4. حماية القاصرين',
    body: 'ينشر التطبيق معلومات عامة عن الناشئين. نتجنب نشر البيانات الشخصية الحساسة للأطفال. يحق لأولياء الأمور طلب إزالة أي معلومات تخص أبنائهم.',
  ),
  _Section(title: '5. حدود المسؤولية',
    body: 'يقدم Youth Scores خدماته "كما هي" دون أي ضمانات تتعلق بدقة البيانات أو استمرارية الخدمة. لا نتحمل مسؤولية أي أضرار ناجمة عن الاعتماد على المعلومات المنشورة.',
  ),
  _Section(title: '6. الملكية الفكرية',
    body: 'جميع المحتويات الأصلية على التطبيق (التصميم، الشعار، النصوص) هي ملك لـ Youth Scores. لا يجوز استخدامها دون إذن خطي مسبق.',
  ),
  _Section(title: '7. القانون المطبق',
    body: 'تخضع هذه الشروط لقوانين جمهورية مصر العربية. أي نزاعات تندرج ضمن اختصاص المحاكم المصرية.',
  ),
  _Section(title: '8. التواصل',
    body: 'للاستفسار عن هذه الشروط: zyadwael2009@gmail.com أو واتساب: +201064428821',
  ),
];

const _termsEn = [
  _Section(title: '1. Service Description',
    body: 'Youth Scores provides information about youth football tournaments in Egypt, including match results, standings, player statistics, and sports news. By using the app, you agree to these terms.',
  ),
  _Section(title: '2. Data Disclaimer',
    body: 'Data published on Youth Scores is not official data from the Egyptian Football Association or any official body. It is collected through personal match monitoring, messages from parents and players, and club social media pages.',
  ),
  _Section(title: '3. Prohibited Activities',
    items: [
      'Copying or republishing app content collectively without prior permission',
      'Using automated tools to access data',
      'Publishing false or misleading information',
      'Attempting unauthorized access to app systems',
    ],
  ),
  _Section(title: '4. Minor Protection',
    body: 'The app publishes general information about youth players. We avoid publishing sensitive personal data about children. Parents have the right to request removal of any information about their children.',
  ),
  _Section(title: '5. Limitation of Liability',
    body: 'Youth Scores provides its services "as-is" without any guarantees regarding data accuracy or service continuity. We are not responsible for any damages resulting from reliance on published information.',
  ),
  _Section(title: '6. Intellectual Property',
    body: 'All original content in the app (design, logo, text) belongs to Youth Scores. It may not be used without prior written permission.',
  ),
  _Section(title: '7. Governing Law',
    body: 'These terms are governed by the laws of the Arab Republic of Egypt. Any disputes fall under the jurisdiction of Egyptian courts.',
  ),
  _Section(title: '8. Contact',
    body: 'For inquiries about these terms: zyadwael2009@gmail.com or WhatsApp: +201064428821',
  ),
];
