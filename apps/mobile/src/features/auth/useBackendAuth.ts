import { useQuery } from '@tanstack/react-query';

import { getCurrentUser } from '@/api/auth';
import { useSession } from '@/auth/useSession';
import { useApiBaseUrl } from '@/hooks/useApiBaseUrl';

export function useBackendAuth() {
  const { accessToken, user } = useSession();
  const { apiBaseUrl, isLoading: isBaseUrlLoading } = useApiBaseUrl();

  return useQuery({
    queryKey: ['auth-me', user?.id ?? 'anonymous', apiBaseUrl],
    queryFn: () => getCurrentUser({ token: accessToken, baseUrl: apiBaseUrl }),
    enabled: !isBaseUrlLoading && Boolean(accessToken),
    retry: false,
    staleTime: 20_000,
  });
}
