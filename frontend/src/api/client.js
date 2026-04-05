import axios from 'axios';
import { getCurrentLanguage, t, translateBackendDetail } from '../i18n';

const baseURL =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  'http://localhost:8001';

let accessToken = null;
let refreshPromise = null;
let unauthorizedHandler = () => {};

function debugApiError(event, error) {
  if (typeof window === 'undefined') {
    return;
  }

  console.warn(event, {
    code: error?.code || null,
    status: error?.response?.status || null,
    method: error?.config?.method || null,
    url: error?.config?.url || null,
    baseURL,
  });
}

export function setAccessToken(token) {
  accessToken = token || null;
}

export function getAccessToken() {
  return accessToken;
}

export function clearAccessToken() {
  accessToken = null;
}

export function configureApiClient({ onUnauthorized } = {}) {
  unauthorizedHandler = onUnauthorized || (() => {});
}

export function getApiBaseUrl() {
  return baseURL;
}

export function getAuthErrorMessage(error, fallbackMessage = 'auth.login.error.fallback') {
  const status = error?.response?.status;

  if (status === 401) {
    return t('auth.login.error.invalid');
  }

  if (status === 429) {
    return t('auth.login.error.rateLimit');
  }

  if (status === 503) {
    return t('auth.login.error.serviceUnavailable');
  }

  if (!error?.response) {
    debugApiError('isafe_auth_network_error', error);
    if (error?.code === 'ECONNABORTED') {
      return t('auth.login.error.serviceUnavailable');
    }
    return t('auth.login.error.network');
  }

  debugApiError('isafe_auth_http_error', error);
  return fallbackMessage ? t(fallbackMessage) : t('auth.login.error.fallback');
}

const apiClient = axios.create({
  baseURL,
  timeout: 10000,
  withCredentials: true,
});

apiClient.interceptors.request.use((config) => {
  config.headers = config.headers || {};
  config.headers['Accept-Language'] = getCurrentLanguage();
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { response, config } = error;
    const originalRequest = config || {};

    if (!response) {
      return Promise.reject(error);
    }

    const isUnauthorized = response.status === 401;
    const isAuthRoute = originalRequest.url?.startsWith('/api/v1/auth/');
    const canRetry = !originalRequest._retry && !isAuthRoute;

    if (isUnauthorized && canRetry) {
      originalRequest._retry = true;

      if (!refreshPromise) {
        refreshPromise = apiClient
          .post('/api/v1/auth/refresh')
          .then((refreshResponse) => {
            const newAccessToken = refreshResponse.data?.access_token || null;
            setAccessToken(newAccessToken);
            return newAccessToken;
          })
          .catch((refreshError) => {
            debugApiError('isafe_auth_refresh_failed', refreshError);
            clearAccessToken();
            unauthorizedHandler();
            throw refreshError;
          })
          .finally(() => {
            refreshPromise = null;
          });
      }

      try {
        const newToken = await refreshPromise;
        if (newToken) {
          originalRequest.headers = originalRequest.headers || {};
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
        }
        return apiClient(originalRequest);
      } catch (refreshError) {
        return Promise.reject(refreshError);
      }
    }

    if (isUnauthorized && isAuthRoute && !originalRequest.url?.endsWith('/login')) {
      clearAccessToken();
      unauthorizedHandler();
    }

    return Promise.reject(error);
  },
);

export function getApiErrorMessage(error, fallbackMessage) {
  const status = error?.response?.status;
  const detail = error?.response?.data?.detail;
  const errorCode = error?.code;

  if (status === 401) {
    return t('auth.session.expired');
  }

  if (status === 429) {
    return t('common.error.rateLimit');
  }

  if (status === 503) {
    return t('common.error.serviceUnavailable');
  }

  if (status === 400 && typeof detail === 'string') {
    return translateBackendDetail(detail);
  }

  if (!error?.response) {
    if (errorCode === 'ECONNABORTED') {
      debugApiError('isafe_api_timeout', error);
      return t('common.error.timeout');
    }

    debugApiError('isafe_api_unreachable', error);

    return t('common.error.backendUnavailable');
  }

  debugApiError('isafe_api_http_error', error);
  return fallbackMessage ? t(fallbackMessage) : t('common.error.serviceUnavailable');
}

export default apiClient;
