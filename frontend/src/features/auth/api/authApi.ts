/**
 * Authentication API functions.
 */

import apiClient from '../../../services/api/apiClient';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignupRequest {
  email: string;
  full_name: string;
  password: string;
  organization_name: string;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  organization_id: string;
  organization_name: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserResponse;
}

export const authApi = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await apiClient.post('/auth/login', data);
    return response.data;
  },

  signup: async (data: SignupRequest): Promise<TokenResponse> => {
    const response = await apiClient.post('/auth/signup', data);
    return response.data;
  },

  getMe: async (): Promise<UserResponse> => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await apiClient.post('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },
};
