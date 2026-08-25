/**
 * Auth Pivota API Client.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// Attach auth token to requests
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('auth_pivota_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  email: string;
  is_email_verified: boolean;
}

export interface MessageResponse {
  message: string;
  success: boolean;
}

export interface TOTPCodeResponse {
  code: string;
  remaining_seconds: number;
  total_seconds: number;
}

export const authServiceApi = {
  login: async (email: string, password: string): Promise<AuthTokenResponse> => {
    const res = await api.post('/auth/login', { email, password });
    return res.data;
  },

  sendOTP: async (email: string): Promise<MessageResponse> => {
    const res = await api.post('/auth/send-otp', { email });
    return res.data;
  },

  verifyOTP: async (email: string, otp_code: string): Promise<MessageResponse> => {
    const res = await api.post('/auth/verify-otp', { email, otp_code });
    return res.data;
  },

  getCurrentCode: async (): Promise<TOTPCodeResponse> => {
    const res = await api.get('/totp/current-code');
    return res.data;
  },
};

export default api;
