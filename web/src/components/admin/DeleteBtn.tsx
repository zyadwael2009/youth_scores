'use client';
import { useState } from 'react';
import {
  apiDeletePreview, apiDeleteSeason, apiDeleteAge, apiDeleteClub,
  apiDeleteComp, apiDeleteTeam,
  type DeleteKind, type DeletePreview,
} from '@/lib/adminApi';

// One place maps the kind to its endpoint, so the same string drives both the
// preview lookup and the delete itself.
const DELETE_FOR: Record<DeleteKind, (t: string, id: number, pw: string) => Promise<unknown>> = {
  'season': apiDeleteSeason,
  'age-group': apiDeleteAge,
  'club': apiDeleteClub,
  'competition': apiDeleteComp,
  'team': apiDeleteTeam,
};

/**
 * Delete control for structural rows (season, age group, club, competition, team).
 *
 * Deleting is only allowed while nothing depends on the row, so this undoes a
 * mistaken entry rather than discarding history. Opening the dialog asks the
 * server what the delete would cost and shows it: what blocks it, and what
 * gets removed along with it. Confirming requires the admin to re-enter their
 * own password, which the server verifies — a misplaced click cannot delete.
 */
export default function DeleteBtn({ token, kind, id, label, onDone }: {
  token: string;
  kind: DeleteKind;
  id: number;
  /** Human name shown in the dialog, e.g. `نادي «الأهلي»`. */
  label: string;
  onDone: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [preview, setPreview] = useState<DeletePreview | null>(null);
  const [password, setPassword] = useState('');
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const show = async () => {
    setErr(null); setPassword(''); setPreview(null); setOpen(true);
    try { setPreview(await apiDeletePreview(token, kind, id)); }
    catch (e) { setErr(e instanceof Error ? e.message : 'خطأ'); }
  };

  const close = () => { setOpen(false); setPassword(''); setErr(null); };

  const confirm = async () => {
    setErr(null); setBusy(true);
    try { await DELETE_FOR[kind](token, id, password); close(); onDone(); }
    catch (e) { setErr(e instanceof Error ? e.message : 'خطأ'); }
    finally { setBusy(false); }
  };

  const blocked = (preview?.blockers.length ?? 0) > 0;

  return (
    <>
      <button onClick={show}
        className="flex-shrink-0 text-[11px] font-bold rounded-lg px-3 py-1.5 border text-loss border-loss/40">
        حذف
      </button>

      {open && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4"
          onClick={close}>
          <div onClick={e => e.stopPropagation()}
            className="w-full max-w-sm bg-cardBg border border-loss/40 rounded-2xl p-5 space-y-4 max-h-[85vh] overflow-y-auto">
            <div>
              <p className="text-loss font-extrabold text-base">⚠️ تأكيد الحذف</p>
              <p className="text-text text-sm mt-1">{label}</p>
            </div>

            {!preview && !err && <p className="text-hint text-sm">…</p>}

            {blocked && (
              <div className="bg-loss/10 border border-loss/30 rounded-xl p-3 space-y-1">
                <p className="text-loss text-xs font-bold">لا يمكن الحذف — مرتبط بـ:</p>
                {preview!.blockers.map(b => (
                  <p key={b.noun} className="text-text text-xs">• {b.count} {b.noun}</p>
                ))}
                <p className="text-hint text-[11px] pt-1">احذف هذه البيانات أولًا أو انقلها.</p>
              </div>
            )}

            {preview && !blocked && (
              <>
                {preview.cascades.length > 0 ? (
                  <div className="bg-gold/10 border border-gold/30 rounded-xl p-3 space-y-1">
                    <p className="text-gold text-xs font-bold">سيُحذف معه نهائيًا:</p>
                    {preview.cascades.map(x => (
                      <p key={x.noun} className="text-text text-xs">• {x.count} {x.noun}</p>
                    ))}
                  </div>
                ) : (
                  <p className="text-hint text-xs">لا توجد بيانات مرتبطة — الحذف آمن.</p>
                )}

                <div>
                  <label className="block text-teal text-[11px] font-bold mb-1">
                    اكتب كلمة المرور الخاصة بك للتأكيد
                  </label>
                  <input type="password" value={password} autoFocus
                    onChange={e => setPassword(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter' && password) confirm(); }}
                    className="w-full bg-darkBg border border-bdr rounded-lg px-3 py-2 text-text text-sm outline-none focus:border-loss" />
                </div>
              </>
            )}

            {err && <p className="text-loss text-xs">{err}</p>}

            <div className="flex gap-2">
              {preview && !blocked && (
                <button onClick={confirm} disabled={busy || !password}
                  className="flex-1 bg-loss text-white font-extrabold py-2.5 rounded-xl text-sm disabled:opacity-40">
                  {busy ? '…' : 'حذف نهائي'}
                </button>
              )}
              <button onClick={close} disabled={busy}
                className="flex-1 text-hint border border-bdr rounded-xl text-xs font-bold py-2.5">
                إلغاء
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
