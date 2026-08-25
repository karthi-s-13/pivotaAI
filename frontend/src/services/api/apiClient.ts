/**
 * Pivota API Client.
 *
 * Centralized Axios instance with auth headers, token refresh,
 * and consistent error handling.
 */

import axios, { AxiosError } from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// --- Request Interceptor: Attach auth token ---
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('pivota_access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// --- Response Interceptor: Handle 401 / token refresh ---
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // If 401 and not already retried, attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('pivota_refresh_token');

      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const { access_token, refresh_token } = response.data;
          localStorage.setItem('pivota_access_token', access_token);
          localStorage.setItem('pivota_refresh_token', refresh_token);

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }
          return apiClient(originalRequest);
        } catch {
          // Refresh failed — clear tokens and redirect to login
          localStorage.removeItem('pivota_access_token');
          localStorage.removeItem('pivota_refresh_token');
          window.location.href = '/login';
          return Promise.reject(error);
        }
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
