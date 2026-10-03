/**
 * Admin Tenants Page — platform_admin only.
 * Lists all tenants with status, lets admin suspend/reactivate and create new ones.
 */

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { tenantsApi, TenantListItem, CreateTenantPayload } from '../../api/tenants';
import { plansApi } from '../../api/plans';
import { parseApiError } from '../../api/errors';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { Table } from '../../components/ui/Table';
import { LoadingState } from '../../components/ui/LoadingState';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { Input } from '../../components/ui/Input';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

const createSchema = z.object({
  slug: z.string().regex(/^[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])?$/, 'Lowercase letters, numbers and hyphens only'),
  display_name: z.string().min(1).max(120),
  legal_name: z.string().max(200).optional(),
  industry_tag: z.string().min(1, 'Required'),
  package_code: z.string().min(1, 'Required'),
  owner_email: z.string().email(),
  owner_display_name: z.string().min(1),
  owner_password: z.string().min(8, 'Minimum 8 characters'),
});
type CreateForm = z.infer<typeof createSchema>;

export const AdminTenantsPage = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [confirmAction, setConfirmAction] = useState<{
    tenant: TenantListItem;
    action: 'suspend' | 'activate';
  } | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['admin-tenants'],
    queryFn: () => tenantsApi.listAdmin().then((r) => r.data),
  });

  const { data: packages } = useQuery({
    queryKey: ['packages'],
    queryFn: () => plansApi.listPackages().then((r) => r.data),
  });

  const statusMutation = useMutation({
    mutationFn: ({ tenant, action }: { tenant: TenantListItem; action: 'suspend' | 'activate' }) =>
      tenantsApi.updateStatus(tenant.id, action === 'suspend' ? 'suspended' : 'active', tenant.version),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-tenants'] });
      setConfirmAction(null);
      setSuccessMsg('Status updated successfully.');
      setTimeout(() => setSuccessMsg(null), 3000);
    },
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateForm>({ resolver: zodResolver(createSchema) });

  const createMutation = useMutation({
    mutationFn: (payload: CreateTenantPayload) => tenantsApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-tenants'] });
      setShowCreate(false);
      reset();
      setFormError(null);
      setSuccessMsg('Workspace created successfully.');
      setTimeout(() => setSuccessMsg(null), 4000);
    },
    onError: (err) => setFormError(parseApiError(err)),
  });

  const onCreateSubmit = (data: CreateForm) => {
    createMutation.mutate({
      ...data,
      legal_name: data.legal_name || undefined,
    });
  };

  if (isLoading) return <LoadingState message="Loading tenants…" />;

  const tenants = data?.items ?? [];

  return (
    <div className="animate-fade-in flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <button
              onClick={() => navigate('/workspaces')}
              style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', fontSize: 'var(--text-sm)' }}
            >
              ← Workspaces
            </button>
          </div>
          <h1 className="text-2xl font-semibold">Platform Administration</h1>
          <p className="text-muted">
            {tenants.length} workspace{tenants.length !== 1 ? 's' : ''}
          </p>
        </div>
        <Button id="btn-create-tenant" onClick={() => setShowCreate(!showCreate)}>
          + New Workspace
        </Button>
      </div>

      {/* Success banner */}
      {successMsg && (
        <div
          style={{
            padding: 'var(--space-3)',
            background: 'rgba(34,197,94,0.1)',
            border: '1px solid rgba(34,197,94,0.3)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-brand-400)',
            fontSize: 'var(--text-sm)',
          }}
        >
          ✓ {successMsg}
        </div>
      )}

      {/* Create form */}
      {showCreate && (
        <Card style={{ background: 'var(--color-surface-2)' }}>
          <h2 className="text-lg font-semibold mb-4">Create Workspace</h2>
          {formError && (
            <div style={{ marginBottom: 'var(--space-4)', color: 'var(--color-danger-400)', fontSize: 'var(--text-sm)' }}>
              {formError}
            </div>
          )}
          <form onSubmit={handleSubmit(onCreateSubmit)} className="flex-col gap-4">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
              <Input id="create-slug" label="Slug (URL-safe)" placeholder="acme-coffee" {...register('slug')} error={errors.slug?.message} />
              <Input id="create-display-name" label="Display name" placeholder="Acme Coffee" {...register('display_name')} error={errors.display_name?.message} />
              <Input id="create-legal-name" label="Legal name (optional)" placeholder="Acme Coffee Ltd." {...register('legal_name')} error={errors.legal_name?.message} />
              <Input id="create-industry" label="Industry tag" placeholder="restaurant" {...register('industry_tag')} error={errors.industry_tag?.message} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
              <div>
                <label style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: 'var(--space-1)' }}>
                  Package
                </label>
                <select
                  id="create-package"
                  {...register('package_code')}
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
                  <option value="">Select package…</option>
                  {packages?.items?.map((p) => (
                    <option key={p.code} value={p.code}>{p.name}</option>
                  ))}
                </select>
                {errors.package_code && <p style={{ color: 'var(--color-danger-400)', fontSize: 'var(--text-xs)', marginTop: 4 }}>{errors.package_code.message}</p>}
              </div>
              <Input id="create-owner-email" label="Owner email" type="email" placeholder="owner@company.com" {...register('owner_email')} error={errors.owner_email?.message} />
              <Input id="create-owner-name" label="Owner display name" placeholder="Jane Smith" {...register('owner_display_name')} error={errors.owner_display_name?.message} />
              <Input id="create-owner-password" label="Owner password" type="password" placeholder="min 8 chars" {...register('owner_password')} error={errors.owner_password?.message} />
            </div>
            <div className="flex gap-4 justify-end mt-2">
              <Button variant="secondary" type="button" onClick={() => { setShowCreate(false); reset(); setFormError(null); }}>
                Cancel
              </Button>
              <Button type="submit" isLoading={isSubmitting || createMutation.isPending}>
                Create Workspace
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Tenants table */}
      <Table
        columns={[
          {
            key: 'workspace',
            header: 'Workspace',
            render: (t) => (
              <div>
                <div className="font-semibold">{t.display_name}</div>
                <div className="text-xs text-muted">{t.slug}</div>
              </div>
            ),
          },
          {
            key: 'industry',
            header: 'Industry',
            render: (t) => <span className="text-muted">{t.industry_tag}</span>,
          },
          {
            key: 'status',
            header: 'Status',
            render: (t) => <Badge status={t.status}>{t.status}</Badge>,
            width: '100px',
          },
          {
            key: 'created',
            header: 'Created',
            render: (t) => (
              <span className="text-muted">{new Date(t.created_at).toLocaleDateString()}</span>
            ),
            width: '120px',
          },
          {
            key: 'actions',
            header: '',
            render: (t) => (
              <Button
                variant={t.status === 'active' ? 'danger' : 'secondary'}
                onClick={(e) => {
                  e.stopPropagation();
                  setConfirmAction({ tenant: t, action: t.status === 'active' ? 'suspend' : 'activate' });
                }}
                style={{ padding: '4px 12px', fontSize: 'var(--text-xs)' }}
              >
                {t.status === 'active' ? 'Suspend' : 'Reactivate'}
              </Button>
            ),
            width: '120px',
          },
        ]}
        rows={tenants}
        rowKey={(t) => t.id}
        emptyMessage="No workspaces yet. Create one above."
      />

      {/* Confirm dialog */}
      <ConfirmDialog
        open={!!confirmAction}
        title={confirmAction?.action === 'suspend' ? 'Suspend workspace?' : 'Reactivate workspace?'}
        message={
          confirmAction?.action === 'suspend'
            ? `Suspending "${confirmAction.tenant.display_name}" will immediately block all member access.`
            : `Reactivating "${confirmAction?.tenant.display_name}" will restore member access.`
        }
        confirmLabel={confirmAction?.action === 'suspend' ? 'Suspend' : 'Reactivate'}
        variant={confirmAction?.action === 'suspend' ? 'danger' : 'primary'}
        isLoading={statusMutation.isPending}
        onConfirm={() => confirmAction && statusMutation.mutate(confirmAction)}
        onCancel={() => setConfirmAction(null)}
      />
    </div>
  );
};
