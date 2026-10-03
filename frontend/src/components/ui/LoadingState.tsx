import { FC } from 'react';
import { Spinner } from './Spinner';

interface LoadingStateProps {
  message?: string;
}

export const LoadingState: FC<LoadingStateProps> = ({ message = 'Loading...' }) => (
  <div
    className="flex-col items-center justify-center"
    style={{
      padding: 'var(--space-16)',
      gap: 'var(--space-4)',
      textAlign: 'center',
    }}
  >
    <Spinner size={32} />
    <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--text-sm)' }}>{message}</p>
  </div>
);
