import { FC } from 'react';
import { RouterProvider, createBrowserRouter, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

import { AuthProvider } from './AuthContext';
import { WorkspaceProvider } from './WorkspaceContext';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { ErrorBoundary } from '../components/ErrorBoundary';

import { AuthLayout } from '../layouts/AuthLayout';
import { DashboardLayout } from '../layouts/DashboardLayout';

import { Login } from '../pages/Login';
import { Workspaces } from '../pages/Workspaces';
import { NotFoundPage, ForbiddenPage, SuspendedPage } from '../pages/ErrorPages';
import { AdminTenantsPage } from '../pages/admin/AdminTenantsPage';
import { Overview } from '../pages/dashboard/Overview';
import { SettingsPage } from '../pages/dashboard/SettingsPage';
import { ContactsPage } from '../pages/dashboard/ContactsPage';
import { TeamPage } from '../pages/dashboard/TeamPage';
import { PlanPage } from '../pages/dashboard/PlanPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
});

const router = createBrowserRouter([
  // Root redirect
  { path: '/', element: <Navigate to="/login" replace /> },

  // Public auth routes
  {
    element: <AuthLayout />,
    children: [
      { path: '/login', element: <Login /> },
    ],
  },

  // Workspace selector (session required)
  {
    path: '/workspaces',
    element: (
      <ProtectedRoute>
        <Workspaces />
      </ProtectedRoute>
    ),
  },

  // Platform admin routes
  {
    path: '/admin/tenants',
    element: (
      <ProtectedRoute role="platform_admin">
        <AdminTenantsPage />
      </ProtectedRoute>
    ),
  },

  // Tenant-scoped dashboard
  {
    path: '/app/:tenantId',
    element: (
      <ProtectedRoute>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="overview" replace /> },
      { path: 'overview', element: <Overview /> },
      { path: 'contacts', element: <ContactsPage /> },
      { path: 'team', element: <TeamPage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: 'plan', element: <PlanPage /> },
    ],
  },

  // Error pages
  { path: '/403', element: <ForbiddenPage /> },
  { path: '/suspended', element: <SuspendedPage /> },
  { path: '*', element: <NotFoundPage /> },
]);

const App: FC = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <WorkspaceProvider>
        <ErrorBoundary>
          <RouterProvider router={router} />
        </ErrorBoundary>
        {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
      </WorkspaceProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;
