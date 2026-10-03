import { FC, ReactNode } from 'react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}

export const EmptyState: FC<EmptyStateProps> = ({ icon = '📭', title, description, action }) => (
  <div
    className="flex-col items-center animate-fade-in"
    style={{
      padding: 'var(--space-16) var(--space-8)',
      textAlign: 'center',
      gap: 'var(--space-4)',
    }}
  >
    <div style={{ fontSize: '3rem', marginBottom: 'var(--space-4)' }}>{icon}</div>
    <h3 style={{ fontSize: 'var(--text-lg)', fontWeight: 600, marginBottom: 'var(--space-2)' }}>
      {title}
    </h3>
    {description && (
      <p style={{ color: 'var(--color-text-muted)', maxWidth: '380px', lineHeight: 1.6 }}>
        {description}
      </p>
    )}
    {action && <div style={{ marginTop: 'var(--space-4)' }}>{action}</div>}
  </div>
);
