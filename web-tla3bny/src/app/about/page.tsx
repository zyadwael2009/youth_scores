'use client';
import InfoPage from '@/components/tla3bny/InfoPage';

// About tla3bny — a management platform for youth academy leagues, NOT the
// youthscores result-tracking observer site. Content reflects that model:
// organizers run competitions; academies register teams and players.
export default function AboutPage() {
  return (
    <InfoPage
      hero={{ emoji: '🏆', title: 'تلاعبني · Tla3bny', sub: 'دوري الأكاديميات | tla3bny.youthscores.org' }}
      sections={{
        ar: [
          {
            emoji: '🏆',
            title: 'من نحن',
            body: 'تلاعبني منصة لإدارة ومتابعة دوريات وبطولات أكاديميات كرة القدم للناشئين في مصر. ينظّم المشرفون بطولاتهم، وتسجّل الأكاديميات فرقها ولاعبيها، ويتابع الجميع النتائج والترتيب والإحصائيات والتشكيلات في مكان واحد.',
          },
          {
            emoji: '⚙️',
            title: 'ماذا نقدّم',
            items: [
              'إنشاء البطولات وبطولاتها الفرعية حسب الفئة السنية',
              'تسجيل الفرق واعتماد اللاعبين بأوراقهم الرسمية',
              'جدول المباريات والنتائج المباشرة',
              'الترتيب والمجموعات وجداول الأدوار وهدّافو البطولة',
              'تشكيلات المباريات، الجوائز والألقاب، والعقوبات',
              'إشعارات فورية ومحادثة بين الأكاديميات والمنظّمين',
            ],
          },
          {
            emoji: '👥',
            title: 'لمن هذه المنصة',
            body: 'لمنظّمي البطولات، والأكاديميات وفرقها، وأولياء الأمور واللاعبين، والجماهير المهتمة بكرة قدم الناشئين في مصر.',
          },
          {
            emoji: '🗂️',
            title: 'من أين تأتي البيانات',
            body: 'يُدخل منظّمو البطولات بيانات المباريات (النتائج والتشكيلات)، وتُدخل الأكاديميات تشكيلات لاعبيها. يُستخدم الرقم القومي والصورة وتاريخ الميلاد للتحقق من هوية اللاعب وأهليته للفئة السنية ومنع تسجيله بأكثر من أكاديمية في البطولة نفسها.',
          },
          {
            emoji: '⚠️',
            title: 'إخلاء المسؤولية',
            body: 'تلاعبني منصة مستقلة غير رسمية، لا تنتمي إلى الاتحاد المصري لكرة القدم أو أي جهة رسمية. البيانات يدخلها المنظّمون والأكاديميات، وهي لأغراض تنظيمية وإعلامية.',
          },
        ],
        en: [
          {
            emoji: '🏆',
            title: 'About Us',
            body: 'Tla3bny is a platform for running and following youth football academy leagues and tournaments in Egypt. Organizers run their competitions, academies register their teams and players, and everyone follows results, standings, statistics and lineups in one place.',
          },
          {
            emoji: '⚙️',
            title: 'What We Offer',
            items: [
              'Create competitions and age-based sub-competitions',
              'Register teams and approve players with their official papers',
              'Fixtures and live results',
              'Standings, groups, knockout brackets and top scorers',
              'Match lineups, awards and titles, and disciplinary actions',
              'Instant notifications and academy–organizer chat',
            ],
          },
          {
            emoji: '👥',
            title: 'Who It’s For',
            body: 'Competition organizers, academies and their teams, parents and players, and everyone following youth football in Egypt.',
          },
          {
            emoji: '🗂️',
            title: 'Where the Data Comes From',
            body: 'Competition organizers enter match data (results and lineups) and academies enter their squads. A player’s national ID, photo and date of birth are used to verify identity and age eligibility and to stop the same player being entered by more than one academy in the same competition.',
          },
          {
            emoji: '⚠️',
            title: 'Disclaimer',
            body: 'Tla3bny is an independent, unofficial platform, not affiliated with the Egyptian Football Association or any official body. Data is entered by organizers and academies for organizational and informational purposes.',
          },
        ],
      }}
    />
  );
}
