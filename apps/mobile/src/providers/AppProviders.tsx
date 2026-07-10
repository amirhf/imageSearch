import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PropsWithChildren, useState } from 'react';

import { AuthProvider } from '@/auth/AuthProvider';
import { OfflineBanner } from '@/components/OfflineBanner';
import { NetworkProvider } from '@/providers/NetworkProvider';

export function AppProviders({ children }: PropsWithChildren) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: 1,
            staleTime: 30_000,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <NetworkProvider>
        <OfflineBanner />
        <AuthProvider queryClient={queryClient}>{children}</AuthProvider>
      </NetworkProvider>
    </QueryClientProvider>
  );
}
