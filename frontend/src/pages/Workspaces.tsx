import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../app/AuthContext';
import { useWorkspace } from '../app/WorkspaceContext';
import { authApi } from '../api/auth';
import { Card } from '../components/ui/Card';
import { Spinner } from '../components/ui/Spinner';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { EmptyState } from '../components/ui/EmptyState';

export const Workspaces = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { setActiveTenant } = useWorkspace();

  const { data: me, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: () => authApi.me().then((r) => r.data),
  });

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  const handleEnterWorkspace = (tenantId: string) => {
    setActiveTenant(tenantId);
    navigate(`/app/${tenantId}/overview`);
  };

  if (isLoading) {
    return (
      <div
        className="flex items-center justify-center animate-fade-in"
        style={{ minHeight: '100vh', background: 'var(--color-surface-0)' }}
      >
        <Spinner />
      </div>
    );
  }

  return (
    <div
      className="animate-fade-in"
      style={{ minHeight: '100vh', background: 'var(--color-surface-0)', padding: 'var(--space-10) var(--space-4)' }}
    >
      <div style={{ maxWidth: '860px', margin: '0 auto' }}>
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-semibold mb-2">
              Welcome back, {me?.user.display_name ?? user?.display_name}
            </h1>
            <p className="text-muted">Select a workspace to continue.</p>
          </div>
          <Button id="workspaces-logout" variant="secondary" onClick={handleLogout}>
            Logout
          </Button>
        </div>

        {me?.user.system_role === 'platform_admin' && (
          <div className="mb-8">
            <Card
              onClick={() => navigate('/admin/tenants')}
              className="flex items-center justify-between"
              style={{
                background: 'linear-gradient(135deg, rgba(59,130,246,0.12), rgba(59,130,246,0.04))',
                borderColor: 'rgba(59,130,246,0.3)',
                cursor: 'pointer',
              }}
            >
              <div>
                <h3 className="text-lg font-semibold">Platform Administration</h3>
                <p className="text-sm text-muted">Manage tenants, packages, and platform settings.</p>
              </div>
              <div style={{ fontSize: '2rem' }}>🛡️</div>
            </Card>
          </div>
        )}

        <h2 className="text-xl font-semibold mb-4">Your Workspaces</h2>

        {!me?.memberships?.length ? (
          <EmptyState
            icon="🏢"
            title="No workspaces yet"
            description="You don't have access to any workspaces. Ask a workspace owner to invite you."
          />
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
              gap: 'var(--space-4)',
            }}
          >
            {me.memberships.map((m) => {
              const tid = String(m.tenant_id);
              return (
                <Card
                  key={tid}
                  onClick={() => handleEnterWorkspace(tid)}
                  style={{ cursor: 'pointer' }}
                >
                  <div className="flex items-center justify-between mb-4">
                    <div
                      style={{
                        width: 42, height: 42, borderRadius: 10,
                        background: 'var(--color-surface-2)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22,
                      }}
                    >
                      🏢
                    </div>
                    <Badge status={m.status}>{m.status}</Badge>
                  </div>
                  <h3 className="text-lg font-semibold mb-1">{m.display_name}</h3>
                  <div className="flex items-center gap-2 text-sm text-muted">
                    <span className="uppercase" style={{ fontSize: 'var(--text-xs)', fontWeight: 600 }}>
                      {m.role}
                    </span>
                    <span>•</span>
                    <span>Joined {new Date(m.created_at).toLocaleDateString()}</span>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
