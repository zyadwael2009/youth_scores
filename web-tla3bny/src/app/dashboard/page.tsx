'use client';
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useTla3bnyAuth } from '@/context/Tla3bnyAuthContext';
import {
  tCategories, tMyPlayers, tSavePlayer, tDeletePlayer, tUpdateProfile,
  type TCategory, type TPlayer,
} from '@/lib/tla3bnyApi';
import Spinner from '@/components/ui/Spinner';
import {
  Card, Field, inputCls, PrimaryButton, ErrorNote, EmptyState,
  LogoAvatar, StatusBadge, useTT,
} from '@/components/tla3bny/kit';

const POSITIONS = ['GK', 'CB', 'LB', 'RB', 'CDM', 'CM', 'CAM', 'LW', 'RW', 'ST'];

function PlayerForm({
  token, cats, editing, onDone, onCancel,
}: {
  token: string; cats: TCategory[]; editing: TPlayer | null;
  onDone: () => void; onCancel: () => void;
}) {
  const tt = useTT();
  const [f, setF] = useState({
    name: editing?.name ?? '',
    age_category_id: editing?.age_category_id ?? (cats[0]?.id ?? ''),
    position: editing?.position ?? '',
    sub_position: editing?.sub_position ?? '',
    dob: editing?.dob ?? '',
    jersey_number: editing?.jersey_number ?? '',
  });
  const [photo, setPhoto] = useState<File | null>(null);
  const [docs, setDocs] = useState<File[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      await tSavePlayer(token, {
        name: f.name,
        age_category_id: f.age_category_id || undefined,
        position: f.position || undefined,
        sub_position: f.sub_position || undefined,
        dob: f.dob || undefined,
        jersey_number: f.jersey_number || undefined,
      }, photo, docs, editing?.id);
      onDone();
    } catch (e2) {
      setErr(e2 instanceof Error ? e2.message : String(e2));
    } finally { setBusy(false); }
  };

  return (
    <Card className="p-4">
      <form onSubmit={submit} className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <Field label={tt('الاسم', 'Name')}>
            <input value={f.name} onChange={e => setF({ ...f, name: e.target.value })} className={inputCls} />
          </Field>
          <Field label={tt('الفئة السنية', 'Age category')}>
            <select value={f.age_category_id} onChange={e => setF({ ...f, age_category_id: Number(e.target.value) })} className={inputCls}>
              {cats.map(c => <option key={c.id} value={c.id}>U{c.label}</option>)}
            </select>
          </Field>
          <Field label={tt('المركز', 'Position')}>
            <select value={f.sub_position} onChange={e => setF({ ...f, sub_position: e.target.value })} className={inputCls}>
              <option value="">—</option>
              {POSITIONS.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </Field>
          <Field label={tt('رقم القميص', 'Jersey #')}>
            <input type="number" value={f.jersey_number} onChange={e => setF({ ...f, jersey_number: e.target.value === '' ? '' : Number(e.target.value) })} className={inputCls} />
          </Field>
          <Field label={tt('تاريخ الميلاد', 'Date of birth')}>
            <input type="date" value={f.dob} onChange={e => setF({ ...f, dob: e.target.value })} className={inputCls} />
          </Field>
          <Field label={tt('الصورة', 'Photo')}>
            <input type="file" accept="image/*" onChange={e => setPhoto(e.target.files?.[0] ?? null)}
              className="w-full text-xs text-hint file:me-2 file:py-2 file:px-2 file:rounded-lg file:border-0 file:bg-cardBg2 file:text-teal file:font-bold" />
          </Field>
        </div>
        <Field label={tt('مستندات التحقق (PDF/صور)', 'Verification documents (PDF/images)')}>
          <input type="file" multiple accept="application/pdf,image/*" onChange={e => setDocs(Array.from(e.target.files ?? []))}
            className="w-full text-xs text-hint file:me-2 file:py-2 file:px-2 file:rounded-lg file:border-0 file:bg-cardBg2 file:text-teal file:font-bold" />
        </Field>
        <ErrorNote>{err}</ErrorNote>
        <div className="flex items-center gap-2">
          <PrimaryButton type="submit" disabled={busy || !f.name}>
            {busy ? tt('جارٍ الحفظ…', 'Saving…') : editing ? tt('تحديث', 'Update') : tt('إضافة لاعب', 'Add player')}
          </PrimaryButton>
          <button type="button" onClick={onCancel} className="text-sm text-hint hover:text-text px-3 py-2">{tt('إلغاء', 'Cancel')}</button>
        </div>
        {editing && <p className="text-[11px] text-gold">{tt('أي تعديل يعيد اللاعب لحالة المراجعة.', 'Any edit resets the player to pending review.')}</p>}
      </form>
    </Card>
  );
}

export default function DashboardPage() {
  const tt = useTT();
  const router = useRouter();
  const { user, token, loading, isSuperAdmin, refresh } = useTla3bnyAuth();
  const [cats, setCats] = useState<TCategory[]>([]);
  const [players, setPlayers] = useState<TPlayer[]>([]);
  const [dataLoading, setDataLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<TPlayer | null>(null);
  const [editingProfile, setEditingProfile] = useState(false);

  useEffect(() => {
    if (loading) return;
    if (!user) { router.replace('/login'); return; }
    if (isSuperAdmin) { router.replace('/admin'); return; }
  }, [loading, user, isSuperAdmin, router]);

  const loadPlayers = useCallback(() => {
    if (!token) return;
    setDataLoading(true);
    tMyPlayers(token).then(setPlayers).catch(() => setPlayers([])).finally(() => setDataLoading(false));
  }, [token]);

  useEffect(() => {
    tCategories().then(setCats).catch(() => {});
  }, []);
  useEffect(() => {
    if (user?.status === 'approved') loadPlayers();
    else setDataLoading(false);
  }, [user?.status, loadPlayers]);

  if (loading || !user) return <Spinner />;

  // Pending / rejected gate
  if (user.status !== 'approved') {
    return (
      <div className="max-w-md mx-auto py-8">
        <Card className="p-6 text-center space-y-3">
          <LogoAvatar src={user.logo_path} name={user.name} size={64} />
          <h1 className="text-xl font-black text-text">{user.name}</h1>
          <StatusBadge status={user.status} label={user.status === 'pending' ? tt('قيد المراجعة', 'Pending review') : tt('مرفوض', 'Rejected')} />
          <p className="text-sm text-hint">
            {user.status === 'pending'
              ? tt('تم استلام طلبك. سيتم تفعيل الحساب بعد موافقة المسؤول.', 'Your request was received. The account will be activated after admin approval.')
              : (user.rejection_reason || tt('تم رفض الطلب.', 'Your request was rejected.'))}
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Profile */}
      <Card className="p-4">
        {editingProfile ? (
          <ProfileForm token={token!} user={user} onDone={async () => { await refresh(); setEditingProfile(false); }} onCancel={() => setEditingProfile(false)} />
        ) : (
          <div className="flex items-center gap-3">
            <LogoAvatar src={user.logo_path} name={user.name} size={56} />
            <div className="min-w-0 flex-1">
              <h1 className="text-lg font-black text-text truncate">{user.name}</h1>
              <p className="text-xs text-hint truncate">{user.phone || '—'}{user.address ? ` · ${user.address}` : ''}</p>
            </div>
            <button onClick={() => setEditingProfile(true)} className="text-xs font-bold text-aqua hover:underline shrink-0">{tt('تعديل', 'Edit')}</button>
          </div>
        )}
      </Card>

      {/* Players */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-black text-text">{tt('اللاعبون', 'Players')} <span className="text-hint text-sm">({players.length})</span></h2>
        {!showForm && !editing && (
          <PrimaryButton onClick={() => { setEditing(null); setShowForm(true); }} className="py-2 px-4 text-sm">+ {tt('لاعب', 'Player')}</PrimaryButton>
        )}
      </div>

      {(showForm || editing) && (
        <PlayerForm
          token={token!} cats={cats} editing={editing}
          onDone={() => { setShowForm(false); setEditing(null); loadPlayers(); }}
          onCancel={() => { setShowForm(false); setEditing(null); }}
        />
      )}

      {dataLoading ? <Spinner /> :
        players.length === 0 ? <EmptyState icon="👥" text={tt('لم تُضِف لاعبين بعد', 'No players added yet')} /> :
        <div className="space-y-2">
          {players.map(p => (
            <Card key={p.id} className="p-3">
              <div className="flex items-center gap-3">
                <LogoAvatar src={p.photo_path} name={p.name} size={44} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-text text-sm truncate">{p.name}</span>
                    {p.jersey_number != null && <span className="text-aqua font-bold text-xs tnum">#{p.jersey_number}</span>}
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <StatusBadge status={p.status} label={{ approved: tt('معتمد', 'Approved'), pending: tt('مراجعة', 'Pending'), rejected: tt('مرفوض', 'Rejected') }[p.status]} />
                    {p.age_category && <span className="text-[11px] text-hint">U{p.age_category}</span>}
                    {p.sub_position && <span className="text-[11px] text-hint">{p.sub_position}</span>}
                    <span className="text-[11px] text-hint">📄 {p.file_count}/{p.required_files}</span>
                  </div>
                  {p.status === 'rejected' && p.rejection_reason && <p className="text-[11px] text-loss mt-1">{p.rejection_reason}</p>}
                </div>
                <div className="flex flex-col gap-1 shrink-0">
                  <button onClick={() => { setEditing(p); setShowForm(false); }} className="text-xs font-bold text-teal hover:text-aqua">{tt('تعديل', 'Edit')}</button>
                  <button onClick={async () => { if (confirm(tt('حذف اللاعب؟', 'Delete player?'))) { await tDeletePlayer(token!, p.id); loadPlayers(); } }} className="text-xs font-bold text-hint hover:text-loss">{tt('حذف', 'Delete')}</button>
                </div>
              </div>
            </Card>
          ))}
        </div>}
    </div>
  );
}

function ProfileForm({
  token, user, onDone, onCancel,
}: {
  token: string; user: { name: string | null; phone?: string | null; address?: string | null };
  onDone: () => void; onCancel: () => void;
}) {
  const tt = useTT();
  const [f, setF] = useState({ name: user.name ?? '', phone: user.phone ?? '', address: user.address ?? '' });
  const [logo, setLogo] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      await tUpdateProfile(token, { ...f, logo });
      onDone();
    } catch (e2) { setErr(e2 instanceof Error ? e2.message : String(e2)); }
    finally { setBusy(false); }
  };

  return (
    <form onSubmit={submit} className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <Field label={tt('الاسم', 'Name')}><input value={f.name} onChange={e => setF({ ...f, name: e.target.value })} className={inputCls} /></Field>
        <Field label={tt('الهاتف', 'Phone')}><input value={f.phone} onChange={e => setF({ ...f, phone: e.target.value })} className={inputCls} /></Field>
      </div>
      <Field label={tt('العنوان', 'Address')}><input value={f.address} onChange={e => setF({ ...f, address: e.target.value })} className={inputCls} /></Field>
      <Field label={tt('الشعار', 'Logo')}>
        <input type="file" accept="image/*" onChange={e => setLogo(e.target.files?.[0] ?? null)}
          className="w-full text-xs text-hint file:me-2 file:py-2 file:px-2 file:rounded-lg file:border-0 file:bg-cardBg2 file:text-teal file:font-bold" />
      </Field>
      <ErrorNote>{err}</ErrorNote>
      <div className="flex items-center gap-2">
        <PrimaryButton type="submit" disabled={busy}>{busy ? tt('جارٍ الحفظ…', 'Saving…') : tt('حفظ', 'Save')}</PrimaryButton>
        <button type="button" onClick={onCancel} className="text-sm text-hint hover:text-text px-3 py-2">{tt('إلغاء', 'Cancel')}</button>
      </div>
    </form>
  );
}
