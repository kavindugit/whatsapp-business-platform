import { Outlet } from 'react-router-dom';

export const AuthLayout = () => {
  return (
    <div 
      className="flex items-center justify-center animate-fade-in" 
      style={{ 
        minHeight: '100vh', 
        background: 'var(--color-surface-0)',
        backgroundImage: 'radial-gradient(circle at top right, rgba(34, 197, 94, 0.05), transparent 40%), radial-gradient(circle at bottom left, rgba(59, 130, 246, 0.05), transparent 40%)'
      }}
    >
      <div style={{ width: '100%', maxWidth: '400px', padding: 'var(--space-4)' }}>
        <div className="flex-col items-center gap-4 mb-8 text-center">
          <div 
            style={{
              width: 64, height: 64, borderRadius: 16,
              background: 'linear-gradient(135deg, var(--color-brand-500), var(--color-brand-600))',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 32,
              boxShadow: 'var(--shadow-glow)'
            }}
          >
            💬
          </div>
          <h1 className="text-2xl font-semibold">WhatsApp Platform</h1>
          <p className="text-muted">Manage your business communication seamlessly.</p>
        </div>
        
        <Outlet />
      </div>
    </div>
  );
};
