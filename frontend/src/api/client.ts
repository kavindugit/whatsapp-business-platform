/**
 * Axios instance for the WhatsApp Platform API.
 *
 * SECURITY NOTES:
 *   - withCredentials=true sends the HttpOnly session cookie automatically.
 *   - CSRF token is NOT stored here; it lives in AuthContext (React memory only).
 *     AuthContext registers its own request interceptor that injects X-CSRF-Token.
 *   - 401 responses trigger a redirect to /login; the AuthContext handler does the
 *     state cleanup so the redirect happens only once.
 */

import axios from 'axios';

export const apiClient = axios.create({
  baseURL: '/api/v1',
  withCredentials: true, // send HttpOnly session cookie
  headers: {
    'Content-Type': 'application/json',
  },
});

// 401 redirect interceptor — do NOT clear CSRF here; AuthContext owns that.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      error.response?.status === 401 &&
      typeof window !== 'undefined' &&
      window.location.pathname !== '/login'
    ) {
      window.location.href = '/login';
    }
    return Promise.reject(error);
  },
);
