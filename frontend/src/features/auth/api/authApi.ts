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
  is_2fa_verified: boolean;
  is_iam?: boolean;
  iam_id?: string;
  permissions?: Record<string, boolean>;
  organization_id: string;
  organization_name: string | null;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserResponse;
}

export interface IAMLoginResponse {
  message: string;
  password_change_required: boolean;
  temp_token?: string;
  access_token?: string;
  refresh_token?: string;
  user?: UserResponse;
}

export interface IAMUser {
  id: string;
  iam_id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  status: string;
  policy_id: string;
  policy_name: string;
  created_at: string;
}

export interface IAMPolicy {
  id: string;
  name: string;
  description?: string;
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

  verify2FA: async (code: string): Promise<{ message: string }> => {
    const response = await apiClient.post('/auth/verify-2fa', { code });
    return response.data;
  },

  iamLogin: async (data: { email: string; iam_id: string; password: string }): Promise<IAMLoginResponse> => {
    const response = await apiClient.post('/auth/iam/login', data);
    return response.data;
  },

  iamResetPassword: async (
    data: { temp_password: string; new_password: string; confirm_password: string },
    tempToken: string
  ): Promise<TokenResponse> => {
    const response = await apiClient.post('/auth/iam/reset-password', data, {
      headers: { Authorization: `Bearer ${tempToken}` }
    });
    return response.data;
  },

  getIAMPolicies: async (): Promise<IAMPolicy[]> => {
    const response = await apiClient.get('/auth/iam/policies');
    return response.data;
  },

  getIAMUsers: async (): Promise<IAMUser[]> => {
    const response = await apiClient.get('/auth/iam/users');
    return response.data;
  },

  createIAMUser: async (data: { full_name: string; email: string; policy_id: string }): Promise<IAMUser> => {
    const response = await apiClient.post('/auth/iam/users', data);
    return response.data;
  },

  sendIAMUserDetails: async (userId: string): Promise<{ message: string }> => {
    const response = await apiClient.post(`/auth/iam/users/${userId}/send-details`);
    return response.data;
  },

  deleteIAMUser: async (userId: string): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/auth/iam/users/${userId}`);
    return response.data;
  },
};
