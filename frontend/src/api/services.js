import apiClient, { clearAccessToken, getApiErrorMessage, setAccessToken } from './client';

export async function login({ email, password }) {
  const response = await apiClient.post('/api/v1/auth/login', { email, password });
  const token = response.data?.access_token || null;
  setAccessToken(token);
  return response.data;
}

export async function refreshSession() {
  const response = await apiClient.post('/api/v1/auth/refresh');
  const token = response.data?.access_token || null;
  setAccessToken(token);
  return response.data;
}

export async function logout() {
  try {
    await apiClient.post('/api/v1/auth/logout');
  } finally {
    clearAccessToken();
  }
}

export async function fetchCurrentUser() {
  const response = await apiClient.get('/api/v1/auth/me');
  return response.data;
}

export async function checkEmailExposure(email) {
  const response = await apiClient.post('/api/v1/osint/check', { email });
  return response.data;
}

export async function checkPhoneExposure(phone) {
  const response = await apiClient.post('/api/v1/osint/phone/check', { phone });
  return response.data;
}

export async function uploadPrivacyImage(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/api/v1/privacy/upload', formData);

  return response.data;
}

export { getApiErrorMessage };
