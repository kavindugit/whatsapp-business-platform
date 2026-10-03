/**
 * ContactsPage — paginated, searchable contact list with inline create/edit.
 * Implements T24 (CRUD), T25 (phone uniqueness), T26 (optimistic locking), T28 (search).
 */

import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { contactsApi, ContactCreatePayload } from '../../api/contacts';
import { parseApiError } from '../../api/errors';
import { Contact } from '../../types';
import { useWorkspace } from '../../app/WorkspaceContext';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Table } from '../../components/ui/Table';
import { LoadingState } from '../../components/ui/LoadingState';
import { EmptyState } from '../../components/ui/EmptyState';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';

const contactSchema = z.object({
  display_name: z.string().min(1, 'Name is required').max(120),
  phone_e164: z
    .string()
    .regex(/^\+[1-9]\d{6,14}$/, 'Must be E.164 format, e.g. +94771234567')
    .or(z.literal('')),
  email: z.string().email('Invalid email').or(z.literal('')).optional(),
  preferred_lang: z.enum(['auto', 'en', 'si', 'ta']).optional(),
  notes: z.string().max(1000).optional(),
});
type ContactForm = z.infer<typeof contactSchema>;

const PAGE_SIZE = 20;

export const ContactsPage = () => {
  const { tenantId } = useParams<{ tenantId: string }>();
  const queryClient = useQueryClient();
  const { switchGeneration } = useWorkspace();

  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'active' | 'archived' | ''>('active');
  const [page, setPage] = useState(1);
  const [showCreate, setShowCreate] = useState(false);
  const [editContact, setEditContact] = useState<Contact | null>(null);
  const [archiveTarget, setArchiveTarget] = useState<Contact | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  // Debounce search
  useEffect(() => {
    const t = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 300);
    return () => clearTimeout(t);
  }, [search]);

  // Reset on workspace switch
  useEffect(() => {
    setSearch('');
    setDebouncedSearch('');
    setPage(1);
    setShowCreate(false);
    setEditContact(null);
  }, [switchGeneration]);

  const queryKey = [tenantId, 'contacts', page, debouncedSearch, statusFilter];

  const { data, isLoading } = useQuery({
    queryKey,
    queryFn: () =>
      contactsApi
        .list(tenantId!, { page, page_size: PAGE_SIZE, search: debouncedSearch || undefined, status: statusFilter || undefined })
        .then((r) => r.data),
    enabled: !!tenantId,
  });

  const {
    register,
    handleSubmit,
    reset: resetForm,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<ContactForm>({ resolver: zodResolver(contactSchema) });

  const openEdit = (c: Contact) => {
    setEditContact(c);
    setShowCreate(false);
    setFormError(null);
    setValue('display_name', c.display_name);
    setValue('phone_e164', c.phone_e164 ?? '');
    setValue('email', c.email ?? '');
    setValue('preferred_lang', (c.preferred_lang as ContactForm['preferred_lang']) ?? 'auto');
    setValue('notes', c.notes ?? '');
  };

  const closeForm = () => {
    setShowCreate(false);
    setEditContact(null);
    resetForm();
    setFormError(null);
  };

  const createMutation = useMutation({
    mutationFn: (d: ContactCreatePayload) => contactsApi.create(tenantId!, d),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [tenantId, 'contacts'] });
      closeForm();
    },
    onError: (err) => setFormError(parseApiError(err)),
  });

  const updateMutation = useMutation({
    mutationFn: (d: ContactCreatePayload & { version: number }) =>
      contactsApi.update(tenantId!, editContact!.id, d),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [tenantId, 'contacts'] });
      closeForm();
    },
    onError: (err) => setFormError(parseApiError(err)),
  });

  const archiveMutation = useMutation({
    mutationFn: (c: Contact) => contactsApi.archive(tenantId!, c.id, c.version),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [tenantId, 'contacts'] });
      setArchiveTarget(null);
    },
  });

  const restoreMutation = useMutation({
    mutationFn: (c: Contact) => contactsApi.restore(tenantId!, c.id, c.version),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [tenantId, 'contacts'] });
    },
  });

  const onSubmit = (formData: ContactForm) => {
    const payload: ContactCreatePayload = {
      display_name: formData.display_name,
      phone_e164: formData.phone_e164 || undefined,
      email: formData.email || undefined,
      preferred_lang: formData.preferred_lang,
      notes: formData.notes || undefined,
    };
    if (editContact) {
      updateMutation.mutate({ ...payload, version: editContact.version });
    } else {
      createMutation.mutate(payload);
    }
  };

  const totalPages = Math.ceil((data?.total ?? 0) / PAGE_SIZE);

  return (
    <div className="animate-fade-in flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-semibold mb-1">Contacts</h1>
          <p className="text-muted">{data?.total ?? '—'} total contacts</p>
        </div>
        <Button
          id="btn-create-contact"
          onClick={() => { setShowCreate(true); setEditContact(null); resetForm(); setFormError(null); }}
        >
          + Add Contact
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-2">
        <input
          id="contact-search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name, phone, email…"
          style={{
            flex: 1,
            maxWidth: '360px',
            background: 'var(--color-surface-1)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-2) var(--space-3)',
            color: 'var(--color-text-primary)',
            fontSize: 'var(--text-sm)',
          }}
        />
        <select
          id="contact-status-filter"
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value as typeof statusFilter); setPage(1); }}
          style={{
            background: 'var(--color-surface-1)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-2) var(--space-3)',
            color: 'var(--color-text-primary)',
            fontSize: 'var(--text-sm)',
          }}
        >
          <option value="active">Active</option>
          <option value="archived">Archived</option>
          <option value="">All</option>
        </select>
      </div>

      {/* Create / Edit form */}
      {(showCreate || editContact) && (
        <Card style={{ background: 'var(--color-surface-2)' }}>
          <h2 className="text-lg font-semibold mb-4">{editContact ? 'Edit Contact' : 'New Contact'}</h2>
          {formError && (
            <div style={{ marginBottom: 'var(--space-3)', color: 'var(--color-danger-400)', fontSize: 'var(--text-sm)' }}>
              {formError}
            </div>
          )}
          <form onSubmit={handleSubmit(onSubmit)} className="flex-col gap-4">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
              <Input id="contact-name" label="Display name *" {...register('display_name')} error={errors.display_name?.message} />
              <Input id="contact-phone" label="Phone (E.164)" placeholder="+94771234567" {...register('phone_e164')} error={errors.phone_e164?.message} />
              <Input id="contact-email" label="Email" type="email" {...register('email')} error={errors.email?.message} />
              <div>
                <label style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: 'var(--space-1)' }}>
                  Preferred language
                </label>
                <select
                  id="contact-lang"
                  {...register('preferred_lang')}
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
            <div>
              <label style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: 'var(--space-1)' }}>
                Notes
              </label>
              <textarea
                id="contact-notes"
                {...register('notes')}
                rows={3}
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
            </div>
            <div className="flex gap-4 justify-end">
              <Button variant="secondary" type="button" onClick={closeForm}>Cancel</Button>
              <Button
                id="contact-save"
                type="submit"
                isLoading={isSubmitting || createMutation.isPending || updateMutation.isPending}
              >
                {editContact ? 'Save Changes' : 'Create Contact'}
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* Table */}
      {isLoading ? (
        <LoadingState message="Loading contacts…" />
      ) : !data?.items?.length && !debouncedSearch ? (
        <EmptyState
          icon="👥"
          title="No contacts yet"
          description="Add your first contact to get started."
          action={
            <Button onClick={() => setShowCreate(true)}>Add Contact</Button>
          }
        />
      ) : (
        <>
          <Table
            columns={[
              {
                key: 'name',
                header: 'Name',
                render: (c) => (
                  <div>
                    <div className="font-semibold">{c.display_name}</div>
                    {c.phone_e164 && <div className="text-xs text-muted">{c.phone_e164}</div>}
                  </div>
                ),
              },
              {
                key: 'email',
                header: 'Email',
                render: (c) => <span className="text-muted">{c.email ?? '—'}</span>,
              },
              {
                key: 'lang',
                header: 'Language',
                render: (c) => <span className="text-muted">{c.preferred_lang ?? 'auto'}</span>,
                width: '100px',
              },
              {
                key: 'status',
                header: 'Status',
                render: (c) => <Badge status={c.status}>{c.status}</Badge>,
                width: '90px',
              },
              {
                key: 'actions',
                header: '',
                render: (c) => (
                  <div className="flex gap-2 justify-end">
                    {c.status === 'active' ? (
                      <>
                        <Button
                          variant="secondary"
                          onClick={() => openEdit(c)}
                          style={{ padding: '4px 10px', fontSize: 'var(--text-xs)' }}
                        >
                          Edit
                        </Button>
                        <Button
                          variant="danger"
                          onClick={() => setArchiveTarget(c)}
                          style={{ padding: '4px 10px', fontSize: 'var(--text-xs)' }}
                        >
                          Archive
                        </Button>
                      </>
                    ) : (
                      <Button
                        variant="secondary"
                        onClick={() => restoreMutation.mutate(c)}
                        style={{ padding: '4px 10px', fontSize: 'var(--text-xs)' }}
                      >
                        Restore
                      </Button>
                    )}
                  </div>
                ),
                width: '160px',
              },
            ]}
            rows={data?.items ?? []}
            rowKey={(c) => c.id}
            emptyMessage={debouncedSearch ? 'No contacts match your search.' : 'No contacts.'}
          />

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <span className="text-sm text-muted">
                Page {page} of {totalPages}
              </span>
              <div className="flex gap-2">
                <Button variant="secondary" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} style={{ padding: '4px 12px' }}>
                  ← Prev
                </Button>
                <Button variant="secondary" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} style={{ padding: '4px 12px' }}>
                  Next →
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Archive confirm */}
      <ConfirmDialog
        open={!!archiveTarget}
        title="Archive contact?"
        message={`"${archiveTarget?.display_name}" will be archived. You can restore them later.`}
        confirmLabel="Archive"
        variant="danger"
        isLoading={archiveMutation.isPending}
        onConfirm={() => archiveTarget && archiveMutation.mutate(archiveTarget)}
        onCancel={() => setArchiveTarget(null)}
      />
    </div>
  );
};
