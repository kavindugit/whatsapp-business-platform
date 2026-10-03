/**
 * PlanPage — shows the current subscription and package details.
 * Displays unavailable/future features as greyed-out cards (no fake data).
 */

import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { plansApi, formatLKR, SubscriptionResponse } from '../../api/plans';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { LoadingState } from '../../components/ui/LoadingState';

interface FeatureItem {
  key: string;
  label: string;
  availableFrom?: string;
}

const ALL_FEATURES: FeatureItem[] = [
  { key: 'core_inbox', label: '📥 Inbox' },
  { key: 'contact_directory', label: '👥 Contact Directory' },
  { key: 'business_settings', label: '⚙️ Business Settings' },
  { key: 'fixed_faq', label: '🤖 Fixed FAQ Replies' },
  { key: 'notification_triggers', label: '🔔 Notification Triggers' },
  { key: 'ai_answers', label: '✨ AI Answers', availableFrom: 'Week 6' },
  { key: 'knowledge_base', label: '📚 Knowledge Base', availableFrom: 'Week 6' },
  { key: 'catalogue', label: '🛒 Product Catalogue', availableFrom: 'Week 8' },
  { key: 'order_capture', label: '📦 Order Capture', availableFrom: 'Week 8' },
  { key: 'calendar_booking', label: '📅 Calendar Booking', availableFrom: 'Week 7' },
  { key: 'lead_qualification', label: '🎯 Lead Qualification', availableFrom: 'Week 5' },
  { key: 'ticketing', label: '🎫 Ticketing', availableFrom: 'Week 9' },
  { key: 'store_connector', label: '🏪 Store Connector', availableFrom: 'Week 10' },
  { key: 'campaign_segments', label: '📣 Campaign Segments', availableFrom: 'Week 11' },
  { key: 'branch_routing', label: '🔀 Branch Routing', availableFrom: 'Week 12' },
];

export const PlanPage = () => {
  const { tenantId } = useParams<{ tenantId: string }>();

  const { data: sub, isLoading } = useQuery<SubscriptionResponse>({
    queryKey: [tenantId, 'subscription'],
    queryFn: () => plansApi.getSubscription(tenantId!).then((r) => r.data),
    enabled: !!tenantId,
  });

  if (isLoading) return <LoadingState message="Loading plan…" />;

  const grantedFeatures: Record<string, unknown> = (sub?.feature_permissions as Record<string, unknown>) ?? {};
  const metricLimits: Record<string, number> = (sub?.metric_limits as Record<string, number>) ?? {};

  return (
    <div className="animate-fade-in flex-col gap-6" style={{ maxWidth: '860px' }}>
      <div className="mb-4">
        <h1 className="text-2xl font-semibold mb-1">Plan & Subscription</h1>
        <p className="text-muted">Your current package and included features.</p>
      </div>

      {/* Subscription summary */}
      <Card style={{ background: 'linear-gradient(135deg, rgba(34,197,94,0.08), rgba(34,197,94,0.02))' }}>
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="text-sm text-muted mb-1">Current plan</div>
            <h2 className="text-2xl font-semibold">{sub?.package.name}</h2>
            {sub?.package.description && (
              <p className="text-sm text-muted mt-1">{sub.package.description}</p>
            )}
          </div>
          <Badge status={sub?.subscription.status ?? 'trial'}>
            {sub?.subscription.status ?? '—'}
          </Badge>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 'var(--space-4)', marginTop: 'var(--space-4)' }}>
          <div style={{ background: 'var(--color-surface-2)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)' }}>
            <div className="text-xs text-muted mb-1">Monthly price</div>
            <div className="font-semibold">{sub ? formatLKR(sub.monthly_price) : '—'}</div>
          </div>
          <div style={{ background: 'var(--color-surface-2)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)' }}>
            <div className="text-xs text-muted mb-1">Staff seats</div>
            <div className="font-semibold">{sub?.staff_limit ?? '—'}</div>
          </div>
          <div style={{ background: 'var(--color-surface-2)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)' }}>
            <div className="text-xs text-muted mb-1">WhatsApp numbers</div>
            <div className="font-semibold">{sub?.number_limit ?? '—'}</div>
          </div>
          <div style={{ background: 'var(--color-surface-2)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)' }}>
            <div className="text-xs text-muted mb-1">Period ends</div>
            <div className="font-semibold">
              {sub?.subscription.period_end
                ? new Date(sub.subscription.period_end).toLocaleDateString()
                : '—'}
            </div>
          </div>
        </div>

        {/* Usage disclaimer */}
        <p className="text-xs text-muted mt-4">
          Usage metrics: {sub?.usage ?? 'N/A'} — real-time usage tracking is available from Week 3.
        </p>
      </Card>

      {/* Metric limits */}
      {Object.keys(metricLimits).length > 0 && (
        <Card>
          <h2 className="text-lg font-semibold mb-4">Usage Limits</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-3)' }}>
            {Object.entries(metricLimits).map(([key, value]) => (
              <div
                key={key}
                style={{
                  background: 'var(--color-surface-2)',
                  padding: 'var(--space-3)',
                  borderRadius: 'var(--radius-md)',
                }}
              >
                <div className="text-xs text-muted mb-1" style={{ textTransform: 'capitalize' }}>
                  {key.replace(/_/g, ' ')}
                </div>
                <div className="font-semibold">{value.toLocaleString()}</div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Features */}
      <Card>
        <h2 className="text-lg font-semibold mb-4">Included Features</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 'var(--space-3)' }}>
          {ALL_FEATURES.map((feature) => {
            const isGranted = !!grantedFeatures[feature.key];
            return (
              <div
                key={feature.key}
                style={{
                  padding: 'var(--space-3) var(--space-4)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--color-border)',
                  background: isGranted ? 'rgba(34,197,94,0.06)' : 'var(--color-surface-2)',
                  opacity: isGranted ? 1 : 0.55,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-3)',
                }}
              >
                <span style={{ fontSize: '1.125rem' }}>{isGranted ? '✅' : '🔒'}</span>
                <div>
                  <div
                    className="text-sm font-semibold"
                    style={{ color: isGranted ? 'var(--color-text-primary)' : 'var(--color-text-muted)' }}
                  >
                    {feature.label}
                  </div>
                  {!isGranted && feature.availableFrom && (
                    <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                      Available from {feature.availableFrom}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
};
