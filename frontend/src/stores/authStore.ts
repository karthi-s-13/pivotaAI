/**
 * Pivota Auth Store (Zustand).
 *
 * Manages authentication state: user, tokens, login/logout actions.
 */

import { create } from 'zustand';
import type { UserResponse } from '../features/auth/api/authApi';

interface AuthState {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  setAuth: (user: UserResponse, accessToken: string, refreshToken: string) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
  checkAuth: () => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,

  setAuth: (user, accessToken, refreshToken) => {
    localStorage.setItem('pivota_access_token', accessToken);
    localStorage.setItem('pivota_refresh_token', refreshToken);
    set({ user, isAuthenticated: true, isLoading: false });
  },

  logout: () => {
    localStorage.removeItem('pivota_access_token');
    localStorage.removeItem('pivota_refresh_token');
    set({ user: null, isAuthenticated: false, isLoading: false });
  },

  setLoading: (loading) => set({ isLoading: loading }),

  checkAuth: () => {
    const token = localStorage.getItem('pivota_access_token');
    if (token) {
      return true;
    }
    set({ isLoading: false });
    return false;
  },
}));
