'use client';
import InfoPage from '@/components/tla3bny/InfoPage';

// Privacy policy tailored to tla3bny: a management platform that stores academy,
// team and (minor) player data — including national IDs, photos and documents.
export default function PrivacyPage() {
  return (
    <InfoPage
      hero={{ emoji: '🔒', title: 'سياسة الخصوصية', sub: 'Privacy Policy · تلاعبني' }}
      sections={{
        ar: [
          {
            emoji: '🔒',
            title: 'مقدمة',
            body: 'تحترم منصة تلاعبني خصوصيتك. توضّح هذه السياسة البيانات التي نجمعها، ولماذا نجمعها، وكيف نستخدمها ونحميها.',
          },
          {
            emoji: '🗃️',
            title: 'البيانات التي نجمعها',
            items: [
              'بيانات الحساب: اسم المستخدم، البريد أو الهاتف، وكلمة المرور (مخزّنة مشفّرة).',
              'بيانات الأكاديمية والفريق: الاسم، الشعار، الصور، وسائل التواصل، والفروع.',
              'بيانات اللاعبين: الاسم، تاريخ الميلاد، الرقم القومي، الصورة، والمستندات المطلوبة للبطولة.',
              'بيانات تشغيلية أساسية لازمة لعمل الخدمة.',
            ],
          },
          {
            emoji: '🎯',
            title: 'لماذا نستخدمها',
            body: 'لإدارة البطولات وتشغيلها، والتحقق من هوية اللاعبين وأهليتهم للفئة السنية، ومنع تسجيل اللاعب الواحد بأكثر من أكاديمية في البطولة نفسها، وعرض النتائج والترتيب والإحصائيات.',
          },
          {
            emoji: '👁️',
            title: 'من يطّلع على البيانات',
            body: 'تظهر بيانات اللاعب العامة (الاسم، الصورة، المركز، الإحصائيات) للجمهور. أمّا المستندات والرقم القومي فتُتاح فقط لمنظّمي البطولة المسجّل بها اللاعب ولأكاديميته بغرض الاعتماد، ولا تظهر للعامة.',
          },
          {
            emoji: '🧒',
            title: 'بيانات القُصّر',
            body: 'معظم اللاعبين قُصّر. برفعك بيانات لاعب وصورته ومستنداته فأنت تقرّ بأنك حصلت على موافقة وليّ الأمر على إدخالها واستخدامها داخل المنصة.',
          },
          {
            emoji: '🔐',
            title: 'الحماية والاحتفاظ',
            body: 'بعد اعتماد اللاعب في بطولة تُجمَّد بياناته وأوراقه لدى الأكاديمية لمنع التلاعب بالهوية. يمكن للأكاديمية إغلاق حسابها في أي وقت؛ وتبقى سجلات المباريات التاريخية محفوظة للحفاظ على سلامة نتائج بقية الأندية.',
          },
          {
            emoji: '🚫',
            title: 'عدم البيع',
            body: 'لا نبيع بياناتك الشخصية لأطراف ثالثة، ولا نستخدمها خارج أغراض تشغيل المنصة.',
          },
          {
            emoji: '📩',
            title: 'التواصل بشأن الخصوصية',
            body: 'لأي طلب متعلق ببياناتك أو حذفها، تواصل معنا عبر صفحة «تواصل معنا».',
          },
        ],
        en: [
          {
            emoji: '🔒',
            title: 'Introduction',
            body: 'Tla3bny respects your privacy. This policy explains what data we collect, why, and how we use and protect it.',
          },
          {
            emoji: '🗃️',
            title: 'Data We Collect',
            items: [
              'Account data: username, email or phone, and password (stored hashed).',
              'Academy & team data: name, logo, photos, contact channels, and branches.',
              'Player data: name, date of birth, national ID, photo, and the documents a competition requires.',
              'Basic operational data needed to run the service.',
            ],
          },
          {
            emoji: '🎯',
            title: 'Why We Use It',
            body: 'To run competitions, verify players’ identity and age eligibility, stop the same player being entered by more than one academy in the same competition, and display results, standings and statistics.',
          },
          {
            emoji: '👁️',
            title: 'Who Can See It',
            body: 'A player’s public data (name, photo, position, statistics) is visible to everyone. Documents and the national ID are shown only to the organizers of the competition the player is entered in, and to their academy, for approval — never to the public.',
          },
          {
            emoji: '🧒',
            title: 'Minors’ Data',
            body: 'Most players are minors. By uploading a player’s data, photo and documents you confirm you have the guardian’s consent to enter and use them within the platform.',
          },
          {
            emoji: '🔐',
            title: 'Protection & Retention',
            body: 'Once a player is approved in a competition, their data and papers are frozen for the academy to prevent identity tampering. An academy may close its account at any time; historical match records are kept so other clubs’ results stay intact.',
          },
          {
            emoji: '🚫',
            title: 'No Selling',
            body: 'We do not sell your personal data to third parties, nor use it beyond operating the platform.',
          },
          {
            emoji: '📩',
            title: 'Privacy Requests',
            body: 'For any request about your data or its deletion, reach us through the Contact Us page.',
          },
        ],
      }}
    />
  );
}
