'use client';

interface Tab { label: string; icon?: string; }
interface Props { tabs: Tab[]; current: number; onChange: (i: number) => void; }

export default function TabStrip({ tabs, current, onChange }: Props) {
  return (
    <div className="bg-cardBg border-b border-bdr flex overflow-x-auto no-scrollbar">
      {tabs.map((tab, i) => {
        const active = i === current;
        return (
          <button key={i} onClick={() => onChange(i)}
            className={`flex-shrink-0 flex flex-col items-center gap-0.5 px-4 py-2.5 text-xs border-b-2 transition-all ${active ? 'border-aqua text-aqua font-bold' : 'border-transparent text-hint hover:text-teal'}`}>
            {tab.icon && <span className={`text-base ${active ? 'drop-shadow-[0_0_8px_rgb(var(--accent-rgb)/0.6)]' : ''}`}>{tab.icon}</span>}
            <span>{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
}
