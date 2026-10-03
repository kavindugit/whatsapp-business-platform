export interface User {
  id: string;
  email: string;
  display_name: string;
  system_role: string | null;
}

export interface Tenant {
  id: string;
  slug: string;
  display_name: string;
  legal_name?: string;
  industry_tag: string;
  status: string;
  version: number;
}

export interface TenantMembership {
  id: string;
  email: string;
  display_name: string;
  role: string;
  status: string;
  created_at: string;
}

export interface BusinessSettings {
  tenant_id: string;
  business_name: string;
  public_email?: string;
  public_phone?: string;
  address_text?: string;
  time_zone: string;
  currency: string;
  reply_language: string;
  opening_hours: Record<string, any>;
  escalation_text?: string;
  version: number;
}

export interface Contact {
  id: string;
  tenant_id: string;
  display_name: string;
  phone_e164?: string;
  email?: string;
  preferred_lang?: string;
  notes?: string;
  status: string;
  version: number;
}

export interface Package {
  code: string;
  name: string;
  release_status: string;
  description: string;
}

export interface SubscriptionDetail {
  subscription: any;
  package: Package;
  version: number;
  monthly_price: number;
  setup_price: number;
  staff_limit: number;
  number_limit: number;
  feature_permissions: Record<string, any>;
  metric_limits: Record<string, any>;
  usage: string;
}
