/**
 * WorkspaceContext — stores the active tenant + provides cache invalidation.
 * When the user switches workspace:
 *   1. In-flight requests for the previous tenant are aborted.
 *   2. TanStack Query cache entries keyed by the previous tenantId are invalidated.
 *   3. All form states signal a reset via `switchGeneration`.
 * This implements T30 (workspace switch with late response guard).
 */

import {
  createContext,
  FC,
  ReactNode,
  useCallback,
  useContext,
  useRef,
  useState,
} from 'react';
import { useQueryClient } from '@tanstack/react-query';

interface WorkspaceContextValue {
  activeTenantId: string | null;
  switchGeneration: number; // increments on each switch — forms observe this
  setActiveTenant: (tenantId: string) => void;
  clearActiveTenant: () => void;
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export const WorkspaceProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [activeTenantId, setActiveTenantId] = useState<string | null>(null);
  const [switchGeneration, setSwitchGeneration] = useState(0);
  const abortControllerRef = useRef<AbortController | null>(null);
  const queryClient = useQueryClient();

  const setActiveTenant = useCallback(
    (tenantId: string) => {
      // Abort in-flight requests from the previous tenant context
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      // Invalidate all cache entries for the previous tenant
      setActiveTenantId((prev) => {
        if (prev && prev !== tenantId) {
          queryClient.invalidateQueries({ queryKey: [prev] });
        }
        return tenantId;
      });

      setSwitchGeneration((g) => g + 1);
    },
    [queryClient],
  );

  const clearActiveTenant = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setActiveTenantId(null);
    setSwitchGeneration((g) => g + 1);
  }, []);

  return (
    <WorkspaceContext.Provider
      value={{ activeTenantId, switchGeneration, setActiveTenant, clearActiveTenant }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useWorkspace = (): WorkspaceContextValue => {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) throw new Error('useWorkspace must be used inside WorkspaceProvider');
  return ctx;
};
