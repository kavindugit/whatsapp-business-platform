/** auth.ts — typed wrappers for /auth/* endpoints */

import { apiClient } from './client';
import { User } from '../types';

export interface MeResponse {
  user: User;
  memberships: {
    tenant_id: string;
    display_name: string;
    role: string;
    status: string;
    created_at: string;
  }[];
  csrf_token: string;
}

export interface LoginResponse extends MeResponse {}

export const authApi = {
  login: (email: string, password: string) =>
    apiClient.post<LoginResponse>('/auth/login', { email, password }),

  logout: () => apiClient.post('/auth/logout'),

  me: () => apiClient.get<MeResponse>('/auth/me'),
};
