/**
 * TeamPage — view and manage workspace members.
 * Visible to owner/manager. Shows member list; no password hashes exposed.
 */

import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { tenantsApi, MemberItem } from '../../api/tenants';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { Table } from '../../components/ui/Table';
import { LoadingState } from '../../components/ui/LoadingState';
import { EmptyState } from '../../components/ui/EmptyState';

const ROLE_LABEL: Record<string, string> = {
  owner: '👑 Owner',
  manager: '🔧 Manager',
  agent: '💬 Agent',
};

export const TeamPage = () => {
  const { tenantId } = useParams<{ tenantId: string }>();

  const { data, isLoading } = useQuery({
    queryKey: [tenantId, 'members'],
    queryFn: () => tenantsApi.getMembers(tenantId!).then((r) => r.data),
    enabled: !!tenantId,
  });

  const members = data?.items ?? [];
  const active = members.filter((m) => m.status === 'active');

  if (isLoading) return <LoadingState message="Loading team…" />;

  return (
    <div className="animate-fade-in flex-col gap-6" style={{ maxWidth: '800px' }}>
      <div className="mb-4">
        <h1 className="text-2xl font-semibold mb-1">Team</h1>
        <p className="text-muted">
          {active.length} active member{active.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Seat usage card */}
      <Card style={{ background: 'var(--color-surface-2)' }}>
        <div className="flex items-center gap-4">
          <div style={{ fontSize: '2rem' }}>👥</div>
          <div>
            <div className="text-sm text-muted">Active staff seats</div>
            <div className="text-2xl font-semibold">{active.length}</div>
          </div>
        </div>
      </Card>

      {/* Info note */}
      <div
        style={{
          padding: 'var(--space-3) var(--space-4)',
          background: 'rgba(59,130,246,0.08)',
          border: '1px solid rgba(59,130,246,0.2)',
          borderRadius: 'var(--radius-md)',
          fontSize: 'var(--text-sm)',
          color: 'var(--color-info-400)',
        }}
      >
        To invite new members or change roles, use the CLI command:{' '}
        <code style={{ background: 'rgba(59,130,246,0.15)' }}>
          python -m app.cli assign-membership
        </code>
      </div>

      {/* Members table */}
      {!members.length ? (
        <EmptyState
          icon="👤"
          title="No members found"
          description="Members can be added via the platform CLI."
        />
      ) : (
        <Table<MemberItem>
          columns={[
            {
              key: 'member',
              header: 'Member',
              render: (m) => (
                <div>
                  <div className="font-semibold">{m.display_name}</div>
                  <div className="text-xs text-muted">{m.email}</div>
                </div>
              ),
            },
            {
              key: 'role',
              header: 'Role',
              render: (m) => (
                <span style={{ fontSize: 'var(--text-sm)' }}>{ROLE_LABEL[m.role] ?? m.role}</span>
              ),
              width: '140px',
            },
            {
              key: 'status',
              header: 'Status',
              render: (m) => <Badge status={m.status}>{m.status}</Badge>,
              width: '90px',
            },
            {
              key: 'joined',
              header: 'Joined',
              render: (m) => (
                <span className="text-muted">
                  {new Date(m.created_at).toLocaleDateString()}
                </span>
              ),
              width: '120px',
            },
          ]}
          rows={members}
          rowKey={(m) => m.id}
        />
      )}
    </div>
  );
};
