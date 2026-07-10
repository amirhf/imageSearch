import type { QueryClient } from '@tanstack/react-query';
import type { Session, User } from '@supabase/supabase-js';
import { createContext, PropsWithChildren, useEffect, useMemo, useState } from 'react';

import { isSupabaseConfigured, supabase } from '@/auth/supabase';

interface AuthContextValue {
  session: Session | null;
  user: User | null;
  accessToken: string | null;
  isConfigured: boolean;
  isLoading: boolean;
  signIn(email: string, password: string): Promise<void>;
  signUp(email: string, password: string): Promise<void>;
  signOut(): Promise<void>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

interface AuthProviderProps extends PropsWithChildren {
  queryClient: QueryClient;
}

export function AuthProvider({ children, queryClient }: AuthProviderProps) {
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(Boolean(supabase));

  useEffect(() => {
    if (!supabase) {
      return;
    }

    let isMounted = true;

    supabase.auth.getSession().then(({ data }) => {
      if (!isMounted) {
        return;
      }
      setSession(data.session ?? null);
      setIsLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
    });

    return () => {
      isMounted = false;
      subscription.unsubscribe();
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      user: session?.user ?? null,
      accessToken: session?.access_token ?? null,
      isConfigured: isSupabaseConfigured,
      isLoading,
      async signIn(email: string, password: string) {
        if (!supabase) {
          throw new Error('Supabase is not configured for the mobile app.');
        }
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) {
          throw error;
        }
      },
      async signUp(email: string, password: string) {
        if (!supabase) {
          throw new Error('Supabase is not configured for the mobile app.');
        }
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) {
          throw error;
        }
      },
      async signOut() {
        if (supabase) {
          await supabase.auth.signOut();
        }
        setSession(null);
        queryClient.clear();
      },
    }),
    [isLoading, queryClient, session],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
