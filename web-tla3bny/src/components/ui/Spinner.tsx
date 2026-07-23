export default function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 p-12">
      <div className="w-10 h-10 border-4 border-bdr border-t-aqua rounded-full animate-spin" />
      {label && <p className="text-hint text-sm">{label}</p>}
    </div>
  );
}
