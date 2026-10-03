import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../api/client';
import { Card } from '../../components/ui/Card';
import { Spinner } from '../../components/ui/Spinner';
import { Badge } from '../../components/ui/Badge';

export const Overview = () => {
  const { tenantId } = useParams<{ tenantId: string }>();

  // Fetch tenant plan/subscription details
  const { data: plan, isLoading: isPlanLoading } = useQuery({
    queryKey: ['plan', tenantId],
    queryFn: async () => {
      const res = await apiClient.get(`/tenants/${tenantId}/subscription`);
      return res.data;
    }
  });

  if (isPlanLoading) {
    return <Spinner />;
  }

  return (
    <div className="animate-fade-in flex-col gap-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-semibold mb-2">Overview</h1>
          <p className="text-muted">Welcome to your workspace overview.</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 'var(--space-6)' }}>
        <Card className="flex-col gap-2">
          <div className="text-sm text-muted">Current Plan</div>
          <div className="flex items-center gap-2">
            <div className="text-2xl font-semibold">{plan?.package?.name ?? '—'}</div>
            <Badge status={plan?.subscription?.status}>{plan?.subscription?.status ?? '—'}</Badge>
          </div>
          <div className="text-sm mt-2 text-muted">
            {plan?.subscription?.period_end
              ? `Trial ends: ${new Date(plan.subscription.period_end).toLocaleDateString()}`
              : 'No active subscription'}
          </div>
        </Card>

        <Card className="flex-col gap-2">
          <div className="text-sm text-muted">Active Users</div>
          <div className="text-2xl font-semibold">1 <span className="text-sm text-muted font-normal">/ {plan?.staff_limit}</span></div>
          <div className="text-sm mt-2 text-info-400">
            Available
          </div>
        </Card>

        <Card className="flex-col gap-2">
          <div className="text-sm text-muted">Connected Numbers</div>
          <div className="text-2xl font-semibold">0 <span className="text-sm text-muted font-normal">/ {plan?.number_limit}</span></div>
          <div className="text-sm mt-2 text-warning-400">
            Pending setup
          </div>
        </Card>
      </div>
      
      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-4)' }}>
          <Card className="flex items-center gap-3 cursor-pointer" style={{ background: 'var(--color-surface-2)' }}>
            <span className="text-2xl">👥</span>
            <span className="font-semibold text-sm">Invite Team</span>
          </Card>
          <Card className="flex items-center gap-3 cursor-pointer" style={{ background: 'var(--color-surface-2)' }}>
            <span className="text-2xl">⚙️</span>
            <span className="font-semibold text-sm">Configure Settings</span>
          </Card>
        </div>
      </div>
    </div>
  );
};
