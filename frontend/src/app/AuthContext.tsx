/**
 * AuthContext — current user + CSRF token stored in React memory only.
 * CSRF token is NEVER written to localStorage or sessionStorage.
 * Axios interceptor is registered here so the token is always fresh.
 */

import {
  createContext,
  FC,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import { apiClient } from '../api/client';
import { User } from '../types';

interface MeResponse {
  user: User;
  memberships: Membership[];
  csrf_token: string;
}

export interface Membership {
  tenant_id: string;
  display_name: string;
  role: string;
  status: string;
  created_at: string;
}

interface AuthState {
  user: User | null;
  memberships: Membership[];
  csrfToken: string | null;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (csrfToken: string, meData: MeResponse) => void;
  logout: () => Promise<void>;
  refreshMe: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export const AuthProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    user: null,
    memberships: [],
    csrfToken: null,
    isLoading: true,
  });

  // Register CSRF interceptor once. The interceptor reads from the ref so it
  // always gets the latest token without re-registering.
  const csrfRef = useRef<string | null>(null);
  csrfRef.current = state.csrfToken;

  useEffect(() => {
    const id = apiClient.interceptors.request.use((config) => {
      const token = csrfRef.current;
      const method = (config.method ?? '').toLowerCase();
      if (token && method !== 'get' && method !== 'head' && method !== 'options') {
        config.headers['X-CSRF-Token'] = token;
      }
      return config;
    });
    return () => {
      apiClient.interceptors.request.eject(id);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const applyMe = useCallback((data: MeResponse) => {
    setState({
      user: data.user,
      memberships: data.memberships,
      csrfToken: data.csrf_token,
      isLoading: false,
    });
  }, []);

  const refreshMe = useCallback(async () => {
    const res = await apiClient.get<MeResponse>('/auth/me');
    applyMe(res.data);
  }, [applyMe]);

  // On mount: call /auth/me. If 401, user is not logged in — clear state.
  useEffect(() => {
    apiClient
      .get<MeResponse>('/auth/me')
      .then((res) => applyMe(res.data))
      .catch(() => {
        setState({ user: null, memberships: [], csrfToken: null, isLoading: false });
      });
  }, [applyMe]);

  const login = useCallback(
    (csrfToken: string, meData: MeResponse) => {
      applyMe({ ...meData, csrf_token: csrfToken });
    },
    [applyMe],
  );

  const logout = useCallback(async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch {
      // ignore network errors on logout
    }
    setState({ user: null, memberships: [], csrfToken: null, isLoading: false });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, logout, refreshMe }}>
      {children}
    </AuthContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = (): AuthContextValue => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
};


