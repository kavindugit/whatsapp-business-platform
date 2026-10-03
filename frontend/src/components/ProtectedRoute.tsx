/**
 * ProtectedRoute — enforces authentication and optional role gating.
 *
 * Usage:
 *   <ProtectedRoute>                     — requires any logged-in user
 *   <ProtectedRoute role="platform_admin"> — requires system_role == 'platform_admin'
 */

import { FC, ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../app/AuthContext';
import { LoadingState } from './ui/LoadingState';

interface ProtectedRouteProps {
  children: ReactNode;
  role?: 'platform_admin';
}

export const ProtectedRoute: FC<ProtectedRouteProps> = ({ children, role }) => {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return <LoadingState />;

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (role && user.system_role !== role) {
    return <Navigate to="/403" replace />;
  }

  return <>{children}</>;
};
