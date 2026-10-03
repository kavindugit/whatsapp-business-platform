import { Link, Outlet, useParams, useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../app/AuthContext';
import { useWorkspace } from '../app/WorkspaceContext';
import { authApi } from '../api/auth';
import { Spinner } from '../components/ui/Spinner';

const NAV_ITEMS = [
  { label: '📊 Overview', key: 'overview' },
  { label: '👥 Contacts', key: 'contacts' },
  { label: '👤 Team', key: 'team' },
  { label: '⚙️ Settings', key: 'settings' },
  { label: '📦 Plan', key: 'plan' },
];

export const DashboardLayout = () => {
  const { tenantId } = useParams<{ tenantId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { setActiveTenant } = useWorkspace();

  const { data: me, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: () => authApi.me().then((r) => r.data),
  });

  const handleLogout = async () => {
    await logout();
    navigate('/login', { replace: true });
  };

  const handleSwitchWorkspace = () => {
    // clearActiveTenant is called implicitly by navigating away;
    // setActiveTenant will re-set when a workspace is selected.
    navigate('/workspaces');
  };

  const handleWorkspaceChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newTenantId = e.target.value;
    if (newTenantId && newTenantId !== tenantId) {
      setActiveTenant(newTenantId);
      navigate(`/app/${newTenantId}/overview`);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center" style={{ minHeight: '100vh' }}>
        <Spinner />
      </div>
    );
  }

  const currentWorkspace = me?.memberships?.find((m) => String(m.tenant_id) === tenantId);

  return (
    <div className="flex" style={{ minHeight: '100vh', background: 'var(--color-surface-0)' }}>
      {/* ── Sidebar ─────────────────────────────────────── */}
      <aside
        style={{
          width: '260px',
          background: 'var(--color-surface-1)',
          borderRight: '1px solid var(--color-border)',
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0,
        }}
      >
        {/* Logo */}
        <div style={{ padding: 'var(--space-5) var(--space-4)', borderBottom: '1px solid var(--color-border)' }}>
          <div className="flex items-center gap-2 mb-4">
            <div
              style={{
                width: 32, height: 32, borderRadius: 8,
                background: 'linear-gradient(135deg, var(--color-brand-500), var(--color-brand-600))',
                display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16,
                boxShadow: '0 0 8px rgba(34,197,94,0.3)',
              }}
            >
              💬
            </div>
            <h2 className="text-sm font-semibold">WhatsApp Platform</h2>
          </div>

          {/* Workspace selector */}
          {me && (me.memberships?.length ?? 0) > 1 ? (
            <select
              id="workspace-selector"
              value={tenantId}
              onChange={handleWorkspaceChange}
              style={{
                width: '100%',
                background: 'var(--color-surface-2)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-2) var(--space-3)',
                color: 'var(--color-text-primary)',
                fontSize: 'var(--text-sm)',
                cursor: 'pointer',
              }}
            >
              {me.memberships?.map((m) => (
                <option key={String(m.tenant_id)} value={String(m.tenant_id)}>
                  {m.display_name}
                </option>
              ))}
            </select>
          ) : (
            <div
              style={{
                background: 'var(--color-surface-2)',
                padding: 'var(--space-3)',
                borderRadius: 'var(--radius-md)',
              }}
            >
              <div className="text-xs text-muted mb-1">Workspace</div>
              <div className="text-sm font-semibold" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {currentWorkspace?.display_name ?? '—'}
              </div>
              <div className="text-xs text-muted mt-1" style={{ textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                {currentWorkspace?.role}
              </div>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav
          style={{
            padding: 'var(--space-4)',
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-1)',
          }}
        >
          {NAV_ITEMS.map((item) => {
            const path = `/app/${tenantId}/${item.key}`;
            const isActive = location.pathname.startsWith(path);
            return (
              <Link
                key={item.key}
                to={path}
                id={`nav-${item.key}`}
                style={{
                  padding: 'var(--space-2) var(--space-3)',
                  borderRadius: 'var(--radius-md)',
                  color: isActive ? 'var(--color-brand-400)' : 'var(--color-text-secondary)',
                  background: isActive ? 'rgba(34,197,94,0.1)' : 'transparent',
                  textDecoration: 'none',
                  fontSize: 'var(--text-sm)',
                  fontWeight: isActive ? 600 : 500,
                  transition: 'all var(--transition-fast)',
                  display: 'block',
                  borderLeft: isActive ? '2px solid var(--color-brand-500)' : '2px solid transparent',
                }}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div style={{ padding: 'var(--space-4)', borderTop: '1px solid var(--color-border)' }}>
          <button
            id="btn-switch-workspace"
            onClick={handleSwitchWorkspace}
            style={{
              background: 'transparent', border: 'none',
              color: 'var(--color-text-secondary)', cursor: 'pointer',
              fontSize: 'var(--text-sm)', fontWeight: 500, padding: 0,
              marginBottom: 'var(--space-3)', display: 'block', width: '100%', textAlign: 'left',
            }}
          >
            ← Switch Workspace
          </button>
          <button
            id="btn-logout"
            onClick={handleLogout}
            style={{
              background: 'transparent', border: 'none',
              color: 'var(--color-danger-400)', cursor: 'pointer',
              fontSize: 'var(--text-sm)', fontWeight: 500, padding: 0,
            }}
          >
            Logout
          </button>
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────── */}
      <main style={{ flex: 1, padding: 'var(--space-8)', overflowY: 'auto', minWidth: 0 }}>
        <Outlet />
      </main>
    </div>
  );
};
