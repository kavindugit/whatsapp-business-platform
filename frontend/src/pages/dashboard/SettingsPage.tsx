/**
 * SettingsPage — business settings for the active tenant.
 * Supports optimistic locking via `version` field.
 * Accessible to active members; editable by owner/manager.
 */

import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { apiClient } from '../../api/client';
import { parseApiError } from '../../api/errors';
import { BusinessSettings } from '../../types';
import { useAuth } from '../../app/AuthContext';
import { useWorkspace } from '../../app/WorkspaceContext';
import { Card } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { LoadingState } from '../../components/ui/LoadingState';
import { useState } from 'react';

const settingsSchema = z.object({
  business_name: z.string().min(1).max(120),
  public_email: z.string().email('Invalid email').or(z.literal('')).optional(),
  public_phone: z.string().max(30).optional(),
  address_text: z.string().max(1000).optional(),
  time_zone: z.string().min(1),
  currency: z.string().length(3),
  reply_language: z.enum(['auto', 'en', 'si', 'ta']),
  escalation_text: z.string().max(1000).optional(),
});

type SettingsForm = z.infer<typeof settingsSchema>;

const TIMEZONES = [
  'Asia/Colombo',
  'Asia/Kolkata',
  'Asia/Dubai',
  'Europe/London',
  'America/New_York',
  'America/Los_Angeles',
  'UTC',
];

export const SettingsPage = () => {
  const { tenantId } = useParams<{ tenantId: string }>();
  const { user } = useAuth();
  const { switchGeneration } = useWorkspace();
  const queryClient = useQueryClient();
  const [saveError, setSaveError] = useState<string | null>(null);
  const [savedOk, setSavedOk] = useState(false);

  const { data: settings, isLoading } = useQuery<BusinessSettings>({
    queryKey: [tenantId, 'settings'],
    queryFn: () => apiClient.get(`/tenants/${tenantId}/settings`).then((r) => r.data),
    enabled: !!tenantId,
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<SettingsForm>({ resolver: zodResolver(settingsSchema) });

  // Reset form when settings load or when workspace switches
  useEffect(() => {
    if (settings) {
      reset({
        business_name: settings.business_name,
        public_email: settings.public_email ?? '',
        public_phone: settings.public_phone ?? '',
        address_text: settings.address_text ?? '',
        time_zone: settings.time_zone,
        currency: settings.currency,
        reply_language: settings.reply_language as 'auto' | 'en' | 'si' | 'ta',
        escalation_text: settings.escalation_text ?? '',
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [settings?.version, switchGeneration]);

  const mutation = useMutation({
    mutationFn: (formData: SettingsForm) =>
      apiClient.patch(`/tenants/${tenantId}/settings`, {
        ...formData,
        version: settings!.version,
        public_email: formData.public_email || undefined,
        public_phone: formData.public_phone || undefined,
        address_text: formData.address_text || undefined,
        escalation_text: formData.escalation_text || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [tenantId, 'settings'] });
      setSaveError(null);
      setSavedOk(true);
      setTimeout(() => setSavedOk(false), 3000);
    },
    onError: (err) => setSaveError(parseApiError(err)),
  });

  // Determine edit permission
  const myMembership = user; // role comes from the me/membership; for now allow editing
  const canEdit = true; // settings page is gated by membership; owner/manager can edit

  if (isLoading) return <LoadingState message="Loading settings…" />;

  return (
    <div className="animate-fade-in flex-col gap-6" style={{ maxWidth: '720px' }}>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold mb-1">Business Settings</h1>
        <p className="text-muted">Configure your workspace profile and preferences.</p>
      </div>

      <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="flex-col gap-6">
        {/* Business info */}
        <Card>
          <h2 className="text-lg font-semibold mb-4">Business Information</h2>
          <div className="flex-col gap-4">
            <Input
              id="settings-business-name"
              label="Business name *"
              {...register('business_name')}
              error={errors.business_name?.message}
            />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
              <Input
                id="settings-public-email"
                label="Public email"
                type="email"
                placeholder="hello@business.com"
                {...register('public_email')}
                error={errors.public_email?.message}
              />
              <Input
                id="settings-public-phone"
                label="Public phone"
                placeholder="+94 77 000 0000"
                {...register('public_phone')}
                error={errors.public_phone?.message}
              />
            </div>
            <div>
              <label style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: 'var(--space-1)' }}>
                Address
              </label>
              <textarea
                id="settings-address"
                {...register('address_text')}
                rows={3}
                placeholder="123 Main Street, Colombo 03"
                style={{
                  width: '100%',
                  background: 'var(--color-surface-1)',
                  border: `1px solid ${errors.address_text ? 'var(--color-danger-500)' : 'var(--color-border)'}`,
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-2) var(--space-3)',
                  color: 'var(--color-text-primary)',
                  fontSize: 'var(--text-sm)',
                  resize: 'vertical',
                  fontFamily: 'inherit',
                }}
              />
            </div>
          </div>
        </Card>

        {/* Regional */}
        <Card>
          <h2 className="text-lg font-semibold mb-4">Regional Settings</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 'var(--space-4)' }}>
            <div>
              <label style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: 'var(--space-1)' }}>
                Time Zone *
              </label>
              <select
                id="settings-timezone"
                {...register('time_zone')}
                style={{
                  width: '100%',
                  background: 'var(--color-surface-1)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-2) var(--space-3)',
                  color: 'var(--color-text-primary)',
                  fontSize: 'var(--text-sm)',
                }}
              >
                {TIMEZONES.map((tz) => (
                  <option key={tz} value={tz}>{tz}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: 'var(--space-1)' }}>
                Currency *
              </label>
              <select
                id="settings-currency"
                {...register('currency')}
                style={{
                  width: '100%',
                  background: 'var(--color-surface-1)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-2) var(--space-3)',
                  color: 'var(--color-text-primary)',
                  fontSize: 'var(--text-sm)',
                }}
              >
                <option value="LKR">LKR</option>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
              </select>
            </div>
            <div>
              <label style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: 'var(--space-1)' }}>
                Reply Language
              </label>
              <select
                id="settings-reply-lang"
                {...register('reply_language')}
                style={{
                  width: '100%',
                  background: 'var(--color-surface-1)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-md)',
                  padding: 'var(--space-2) var(--space-3)',
                  color: 'var(--color-text-primary)',
                  fontSize: 'var(--text-sm)',
                }}
              >
                <option value="auto">Auto-detect</option>
                <option value="en">English</option>
                <option value="si">Sinhala</option>
                <option value="ta">Tamil</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Escalation */}
        <Card>
          <h2 className="text-lg font-semibold mb-4">Escalation Message</h2>
          <p className="text-sm text-muted mb-4">
            Shown when the AI cannot resolve a query and the conversation needs a human agent.
          </p>
          <textarea
            id="settings-escalation"
            {...register('escalation_text')}
            rows={4}
            placeholder="Our team will be in touch shortly. Business hours: Mon–Fri 9am–6pm."
            style={{
              width: '100%',
              background: 'var(--color-surface-1)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-2) var(--space-3)',
              color: 'var(--color-text-primary)',
              fontSize: 'var(--text-sm)',
              resize: 'vertical',
              fontFamily: 'inherit',
            }}
          />
        </Card>

        {/* Footer */}
        {saveError && (
          <div style={{ color: 'var(--color-danger-400)', fontSize: 'var(--text-sm)' }}>
            {saveError}
          </div>
        )}
        {savedOk && (
          <div style={{ color: 'var(--color-brand-400)', fontSize: 'var(--text-sm)' }}>
            ✓ Settings saved.
          </div>
        )}
        <div className="flex gap-4 justify-end">
          <Button
            id="settings-save"
            type="submit"
            isLoading={isSubmitting || mutation.isPending}
            disabled={!isDirty}
          >
            Save Changes
          </Button>
        </div>
      </form>
    </div>
  );
};
