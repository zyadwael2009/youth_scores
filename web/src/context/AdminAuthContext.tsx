'use client';
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { apiLogin, apiMe, type AdminUser } from '@/lib/adminApi';

const TOKEN_KEY = 'ys_admin_token';

interface Ctx {
  token: string | null;
  user: AdminUser | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isSuperadmin: boolean;
  canEdit: boolean; // editor or above
}

const AdminAuthCtx = createContext<Ctx | null>(null);

export function useAdminAuth() {
  const c = useContext(AdminAuthCtx);
  if (!c) throw new Error('useAdminAuth outside AdminAuthProvider');
  return c;
}

export function AdminAuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser]   = useState<AdminUser | null>(null);
  const [loading, setLoading] = useState(true);

  // Restore a saved session and validate it against /me.
  useEffect(() => {
    const saved = typeof window !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null;
    if (!saved) { setLoading(false); return; }
    setToken(saved);
    apiMe(saved)
      .then(u => { if (u) setUser(u); else { localStorage.removeItem(TOKEN_KEY); setToken(null); } })
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const { token: t, user: u } = await apiLogin(username, password);
    localStorage.setItem(TOKEN_KEY, t);
    setToken(t);
    setUser(u);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AdminAuthCtx.Provider value={{
      token, user, loading, login, logout,
      isSuperadmin: user?.role === 'superadmin',
      canEdit: user?.role === 'superadmin' || user?.role === 'editor',
    }}>
      {children}
    </AdminAuthCtx.Provider>
  );
}
