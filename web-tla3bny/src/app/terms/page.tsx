'use client';
import InfoPage from '@/components/tla3bny/InfoPage';

// Terms tailored to tla3bny's roles: organizers run competitions, academies
// register teams/players and are responsible for accurate data and consent.
export default function TermsPage() {
  return (
    <InfoPage
      hero={{ emoji: '📜', title: 'الشروط والأحكام', sub: 'Terms & Conditions · تلاعبني' }}
      sections={{
        ar: [
          {
            emoji: '📜',
            title: 'القبول',
            body: 'باستخدامك منصة تلاعبني فإنك توافق على هذه الشروط. إذا لم توافق عليها، فبرجاء عدم استخدام المنصة.',
          },
          {
            emoji: '✅',
            title: 'الاستخدام السليم',
            items: [
              'أدخل بيانات صحيحة وأوراقًا حقيقية للاعبين.',
              'لا تنتحل شخصية غيرك ولا تسجّل لاعبًا ببيانات مزوّرة.',
              'احترم أدوار المنظّمين والأكاديميات ولا تُسِئ استخدام المنصة أو محتواها.',
            ],
          },
          {
            emoji: '🧑‍⚖️',
            title: 'الأدوار والمسؤوليات',
            body: 'منظّمو البطولة مسؤولون عن إدخال بيانات المباريات واعتماد الفرق واللاعبين. الأكاديميات مسؤولة عن دقة بيانات فرقها ولاعبيها وعن الحصول على الموافقات اللازمة.',
          },
          {
            emoji: '🖼️',
            title: 'المحتوى الذي ترفعه',
            body: 'أنت مسؤول عن الصور والمستندات التي ترفعها وعن حصولك على الموافقات اللازمة لرفعها واستخدامها، خصوصًا لبيانات القُصّر.',
          },
          {
            emoji: '⛔',
            title: 'الإيقاف والحذف',
            body: 'يحق لإدارة المنصة تعليق أو حذف أي حساب يخالف هذه الشروط أو يُدخِل بيانات غير صحيحة أو ينتهك حقوق الآخرين.',
          },
          {
            emoji: '⚠️',
            title: 'إخلاء المسؤولية',
            body: 'البيانات يدخلها المنظّمون والأكاديميات؛ وتلاعبني منصة مستقلة غير رسمية لا تضمن دقة كل البيانات، وتُقدَّم الخدمة «كما هي».',
          },
          {
            emoji: '🔄',
            title: 'تعديل الشروط',
            body: 'قد نحدّث هذه الشروط من وقت لآخر، ويسري التحديث فور نشره على هذه الصفحة.',
          },
        ],
        en: [
          {
            emoji: '📜',
            title: 'Acceptance',
            body: 'By using Tla3bny you agree to these terms. If you do not agree, please do not use the platform.',
          },
          {
            emoji: '✅',
            title: 'Acceptable Use',
            items: [
              'Enter accurate data and genuine documents for players.',
              'Do not impersonate anyone or register a player with falsified data.',
              'Respect the roles of organizers and academies, and don’t misuse the platform or its content.',
            ],
          },
          {
            emoji: '🧑‍⚖️',
            title: 'Roles & Responsibilities',
            body: 'Competition organizers are responsible for entering match data and approving teams and players. Academies are responsible for the accuracy of their team and player data and for obtaining the necessary consents.',
          },
          {
            emoji: '🖼️',
            title: 'Content You Upload',
            body: 'You are responsible for the photos and documents you upload and for having the consent needed to upload and use them — especially for minors’ data.',
          },
          {
            emoji: '⛔',
            title: 'Suspension & Removal',
            body: 'The platform may suspend or remove any account that violates these terms, enters inaccurate data, or infringes others’ rights.',
          },
          {
            emoji: '⚠️',
            title: 'Disclaimer',
            body: 'Data is entered by organizers and academies; Tla3bny is an independent, unofficial platform that does not guarantee the accuracy of all data, and the service is provided “as is”.',
          },
          {
            emoji: '🔄',
            title: 'Changes to Terms',
            body: 'We may update these terms from time to time; updates take effect once posted on this page.',
          },
        ],
      }}
    />
  );
}
