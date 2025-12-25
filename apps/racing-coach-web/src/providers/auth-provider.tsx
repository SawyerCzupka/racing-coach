import {
  getGetCurrentUserQueryKey,
  useGetCurrentUser,
  useLogout,
} from '@/api/generated/auth/auth';
import type { UserResponse } from '@/api/generated/models';
import { useQueryClient } from '@tanstack/react-query';
import { createContext, useCallback, useContext } from 'react';
import { useNavigate } from 'react-router';

interface AuthContextType {
  user: UserResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  logout: () => Promise<void>;
  refetchUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const {
    data: user,
    isLoading,
    isError,
    refetch,
  } = useGetCurrentUser({
    query: {
      retry: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  });

  const logoutMutation = useLogout();

  const logout = useCallback(async () => {
    try {
      await logoutMutation.mutateAsync();
    } catch {
      // Ignore logout errors - clear state anyway
    }
    queryClient.setQueryData(getGetCurrentUserQueryKey(), null);
    queryClient.invalidateQueries({ queryKey: getGetCurrentUserQueryKey() });
    navigate('/login');
  }, [logoutMutation, queryClient, navigate]);

  const refetchUser = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const value: AuthContextType = {
    user: user ?? null,
    isLoading,
    isAuthenticated: !isError && !!user,
    isAdmin: !!user?.is_admin,
    logout,
    refetchUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}
