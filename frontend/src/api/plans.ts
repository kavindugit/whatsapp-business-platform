/** plans.ts — packages and subscription endpoints */

import { apiClient } from './client';

export interface PackageItem {
  code: string;
  name: string;
  release_status: string;
  description: string;
  versions: {
    id: string;
    version: number;
    currency: string;
    monthly_price: number;
    setup_price: number;
    staff_limit: number;
    number_limit: number;
    feature_permissions: Record<string, unknown>;
    metric_limits: Record<string, unknown>;
  }[];
}

export interface PackageListResponse {
  items: PackageItem[];
}

export interface SubscriptionResponse {
  subscription: {
    id: string;
    status: string;
    period_start: string;
    period_end: string;
    anchor_day: number;
  };
  package: { code: string; name: string; description: string };
  version: number;
  currency: string;
  monthly_price: number;
  setup_price: number;
  staff_limit: number;
  number_limit: number;
  feature_permissions: Record<string, unknown>;
  metric_limits: Record<string, unknown>;
  usage: string;
}

/** LKR minor-unit formatter — e.g. 69000 → "LKR 690.00" */
export const formatLKR = (minorUnits: number): string =>
  new Intl.NumberFormat('en-LK', { style: 'currency', currency: 'LKR' }).format(minorUnits / 100);

export const plansApi = {
  listPackages: () => apiClient.get<PackageListResponse>('/packages'),

  getSubscription: (tenantId: string) =>
    apiClient.get<SubscriptionResponse>(`/tenants/${tenantId}/subscription`),
};
