'use client';
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { tLogin, tMe, tRegister, type TUser } from '@/lib/tla3bnyApi';

// Kept separate from the youthscores admin session (ys_admin_token): this is the
// subdomain's own login, so the two never collide in localStorage.
const TOKEN_KEY = 'tla3bny_token';

interface Ctx {
  token: string | null;
  user: TUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<TUser>;
  register: (fd: { name: string; email: string; password: string; phone?: string; address?: string; logo?: File | null }) => Promise<TUser>;
  logout: () => void;
  refresh: () => Promise<void>;
  isSuperAdmin: boolean;
  isApprovedAcademy: boolean;
}

const AuthCtx = createContext<Ctx | null>(null);

export function useTla3bnyAuth() {
  const c = useContext(AuthCtx);
  if (!c) throw new Error('useTla3bnyAuth outside Tla3bnyAuthProvider');
  return c;
}

export function Tla3bnyAuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<TUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const saved = typeof window !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null;
    if (!saved) { setLoading(false); return; }
    setToken(saved);
    tMe(saved)
      .then(u => { if (u) setUser(u); else { localStorage.removeItem(TOKEN_KEY); setToken(null); } })
      .finally(() => setLoading(false));
  }, []);

  const persist = useCallback((t: string, u: TUser) => {
    localStorage.setItem(TOKEN_KEY, t);
    setToken(t);
    setUser(u);
    return u;
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { token: t, user: u } = await tLogin(email, password);
    return persist(t, u);
  }, [persist]);

  const register = useCallback(async (fd: Parameters<Ctx['register']>[0]) => {
    const { token: t, user: u } = await tRegister(fd);
    return persist(t, u);
  }, [persist]);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const refresh = useCallback(async () => {
    if (!token) return;
    const u = await tMe(token);
    if (u) setUser(u);
  }, [token]);

  return (
    <AuthCtx.Provider value={{
      token, user, loading, login, register, logout, refresh,
      isSuperAdmin: user?.role === 'super_admin',
      isApprovedAcademy: user?.role === 'academy' && user?.status === 'approved',
    }}>
      {children}
    </AuthCtx.Provider>
  );
}
