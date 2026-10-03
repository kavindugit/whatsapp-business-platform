import { ReactNode } from 'react';

interface BadgeProps {
  status?: string;
  children: ReactNode;
}

/** Maps subscription/member/tenant status values to badge CSS classes. */
const STATUS_CLASS: Record<string, string> = {
  active: 'badge-active',
  archived: 'badge-archived',
  suspended: 'badge-suspended',
  trial: 'badge-trial',
  past_due: 'badge-warning',
  cancelled: 'badge-archived',
  inactive: 'badge-archived',
  planned: 'badge-archived',
  saleable: 'badge-active',
  pilot: 'badge-trial',
  internal: 'badge-trial',
};

export const Badge = ({ status = '', children }: BadgeProps) => {
  const cls = STATUS_CLASS[status.toLowerCase()] ?? `badge-${status.toLowerCase()}`;
  return <span className={`badge ${cls}`}>{children}</span>;
};
