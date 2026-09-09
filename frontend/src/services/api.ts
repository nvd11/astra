import axios from 'axios';
import { storage } from '@/utils/storage';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/astra/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  config.headers = config.headers || {};
  const sessionId = storage.getSessionId();
  if (sessionId) {
    config.headers['X-Session-ID'] = sessionId;
  }
  const token = storage.getToken();
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      console.warn('[API 401] Session unauthorized or expired');
    }
    return Promise.reject(error);
  }
);

export default api;
