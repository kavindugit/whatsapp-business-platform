/** contacts.ts — contact CRUD endpoints */

import { apiClient } from './client';
import { Contact } from '../types';

export interface ContactListResponse {
  items: Contact[];
  total: number;
  page: number;
  page_size: number;
}

export interface ContactCreatePayload {
  display_name: string;
  phone_e164?: string;
  email?: string;
  preferred_lang?: string;
  notes?: string;
}

export interface ContactUpdatePayload extends ContactCreatePayload {
  version: number;
}

export const contactsApi = {
  list: (
    tenantId: string,
    params: { page?: number; page_size?: number; search?: string; status?: string } = {},
  ) =>
    apiClient.get<ContactListResponse>(`/tenants/${tenantId}/contacts`, { params }),

  get: (tenantId: string, contactId: string) =>
    apiClient.get<Contact>(`/tenants/${tenantId}/contacts/${contactId}`),

  create: (tenantId: string, payload: ContactCreatePayload) =>
    apiClient.post<Contact>(`/tenants/${tenantId}/contacts`, payload),

  update: (tenantId: string, contactId: string, payload: ContactUpdatePayload) =>
    apiClient.patch<Contact>(`/tenants/${tenantId}/contacts/${contactId}`, payload),

  archive: (tenantId: string, contactId: string, version: number) =>
    apiClient.post(`/tenants/${tenantId}/contacts/${contactId}/archive`, { version }),

  restore: (tenantId: string, contactId: string, version: number) =>
    apiClient.post(`/tenants/${tenantId}/contacts/${contactId}/restore`, { version }),
};
