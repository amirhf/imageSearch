import { useQuery } from '@tanstack/react-query';

import { getImage } from '@/api/images';
import { useSession } from '@/auth/useSession';
import { useApiBaseUrl } from '@/hooks/useApiBaseUrl';

export function useImage(id: string | undefined) {
  const { accessToken, user } = useSession();
  const { apiBaseUrl, isLoading: isBaseUrlLoading } = useApiBaseUrl();

  return useQuery({
    queryKey: ['image', id, user?.id ?? 'anonymous', apiBaseUrl],
    queryFn: () =>
      getImage({
        id: id as string,
        token: accessToken,
        baseUrl: apiBaseUrl,
      }),
    enabled: !isBaseUrlLoading && Boolean(id),
    staleTime: 30_000,
  });
}
