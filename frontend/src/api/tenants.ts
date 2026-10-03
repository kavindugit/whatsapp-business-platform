/** tenants.ts — admin and tenant-scoped endpoints */

import { apiClient } from './client';

export interface TenantListItem {
  id: string;
  slug: string;
  display_name: string;
  legal_name?: string;
  industry_tag: string;
  status: string;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface TenantDetail extends TenantListItem {
  subscription?: {
    status: string;
    package_name: string;
    period_end: string;
  };
  owner?: {
    email: string;
    display_name: string;
  };
}

export interface TenantListResponse {
  items: TenantListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface CreateTenantPayload {
  slug: string;
  display_name: string;
  legal_name?: string;
  industry_tag: string;
  package_code: string;
  owner_email: string;
  owner_display_name: string;
  owner_password: string;
}

export interface MemberItem {
  id: string;
  user_id: string;
  email: string;
  display_name: string;
  role: string;
  status: string;
  created_at: string;
}

export const tenantsApi = {
  // Admin routes
  listAdmin: (page = 1, pageSize = 20) =>
    apiClient.get<TenantListResponse>('/admin/tenants', {
      params: { page, page_size: pageSize },
    }),

  getAdmin: (tenantId: string) =>
    apiClient.get<TenantDetail>(`/admin/tenants/${tenantId}`),

  create: (payload: CreateTenantPayload) =>
    apiClient.post<TenantDetail>('/admin/tenants', payload),

  updateStatus: (tenantId: string, status: 'active' | 'suspended', version: number) =>
    apiClient.patch(`/admin/tenants/${tenantId}/status`, { status, version }),

  // Member-scoped routes
  getMembers: (tenantId: string) =>
    apiClient.get<{ items: MemberItem[] }>(`/tenants/${tenantId}/members`),
};
