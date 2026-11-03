'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  authApi,
  getToken,
  setToken,
  clearToken,
  getUser,
  setUser,
  UserProfile,
  AuthResponse
} from '@/lib/api';

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<AuthResponse>;
  register: (payload: {
    company_name: string;
    email: string;
    password: string;
    full_name: string;
    role?: string;
  }) => Promise<AuthResponse>;
  logout: () => void;
  demoLogin: (role?: string) => Promise<AuthResponse>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUserState] = useState<UserProfile | null>(null);
  const [token, setTokenState] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const router = useRouter();

  // Restore session from localStorage on initial client mount
  useEffect(() => {
    try {
      const storedToken = getToken();
      const storedUser = getUser();

      if (storedToken && storedUser) {
        setTokenState(storedToken);
        setUserState(storedUser);
      }
    } catch (e) {
      console.warn('Could not restore auth session from localStorage');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, password: string): Promise<AuthResponse> => {
    setIsLoading(true);
    try {
      const response = await authApi.login({ email, password });
      setToken(response.access_token);
      setUser(response.user);
      setTokenState(response.access_token);
      setUserState(response.user);
      return response;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: {
    company_name: string;
    email: string;
    password: string;
    full_name: string;
    role?: string;
  }): Promise<AuthResponse> => {
    setIsLoading(true);
    try {
      const response = await authApi.register(payload);
      setToken(response.access_token);
      setUser(response.user);
      setTokenState(response.access_token);
      setUserState(response.user);
      return response;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = useCallback(() => {
    clearToken();
    setTokenState(null);
    setUserState(null);
    router.push('/login');
  }, [router]);

  const demoLogin = async (role = 'CEO'): Promise<AuthResponse> => {
    setIsLoading(true);
    const demoEmail = role === 'Director' ? 'director@acme.com' : 'ceo@acme.com';
    const demoPass = 'Password123!';
    const demoCompany = 'Acme Global Enterprise';
    const demoName = role === 'Director' ? 'Alex Vance' : 'Jane Doe';

    try {
      // First attempt to login with demo credentials
      try {
        const loginRes = await authApi.login({ email: demoEmail, password: demoPass });
        setToken(loginRes.access_token);
        setUser(loginRes.user);
        setTokenState(loginRes.access_token);
        setUserState(loginRes.user);
        return loginRes;
      } catch (loginErr) {
        // If login failed (e.g. database freshly reset), auto-register demo tenant
        const regRes = await authApi.register({
          company_name: demoCompany,
          email: demoEmail,
          password: demoPass,
          full_name: demoName,
          role,
        });
        setToken(regRes.access_token);
        setUser(regRes.user);
        setTokenState(regRes.access_token);
        setUserState(regRes.user);
        return regRes;
      }
    } finally {
      setIsLoading(false);
    }
  };

  const refreshProfile = async (): Promise<void> => {
    if (!token) return;
    try {
      const profile = await authApi.getMe();
      setUser(profile);
      setUserState(profile);
    } catch (e) {
      console.warn('Failed to refresh user profile', e);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!token && !!user,
        login,
        register,
        logout,
        demoLogin,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

