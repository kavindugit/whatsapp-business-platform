import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';

export const NotFoundPage = () => {
  const navigate = useNavigate();
  return (
    <div
      className="flex-col items-center justify-center animate-fade-in"
      style={{ minHeight: '100vh', background: 'var(--color-surface-0)', textAlign: 'center', padding: 'var(--space-8)' }}
    >
      <div style={{ fontSize: '4rem', marginBottom: 'var(--space-4)' }}>🔍</div>
      <h1 className="text-3xl font-semibold mb-2">404 — Page Not Found</h1>
      <p className="text-muted mb-8">The page you're looking for doesn't exist.</p>
      <Button onClick={() => navigate('/workspaces')}>Go to Workspaces</Button>
    </div>
  );
};

export const ForbiddenPage = () => {
  const navigate = useNavigate();
  return (
    <div
      className="flex-col items-center justify-center animate-fade-in"
      style={{ minHeight: '100vh', background: 'var(--color-surface-0)', textAlign: 'center', padding: 'var(--space-8)' }}
    >
      <div style={{ fontSize: '4rem', marginBottom: 'var(--space-4)' }}>🚫</div>
      <h1 className="text-3xl font-semibold mb-2">403 — Access Denied</h1>
      <p className="text-muted mb-8">You don't have permission to view this page.</p>
      <Button onClick={() => navigate('/workspaces')}>Go to Workspaces</Button>
    </div>
  );
};

export const SuspendedPage = () => {
  const navigate = useNavigate();
  return (
    <div
      className="flex-col items-center justify-center animate-fade-in"
      style={{ minHeight: '100vh', background: 'var(--color-surface-0)', textAlign: 'center', padding: 'var(--space-8)' }}
    >
      <div style={{ fontSize: '4rem', marginBottom: 'var(--space-4)' }}>⚠️</div>
      <h1 className="text-3xl font-semibold mb-2">Workspace Suspended</h1>
      <p className="text-muted mb-8">
        This workspace has been suspended. Please contact your platform administrator.
      </p>
      <Button variant="secondary" onClick={() => navigate('/workspaces')}>
        Switch Workspace
      </Button>
    </div>
  );
};
