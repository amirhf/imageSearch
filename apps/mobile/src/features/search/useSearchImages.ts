import { useQuery } from '@tanstack/react-query';

import { searchImages } from '@/api/search';
import type { SearchScope } from '@/api/types';
import { useSession } from '@/auth/useSession';
import { useApiBaseUrl } from '@/hooks/useApiBaseUrl';

interface UseSearchImagesInput {
  query: string;
  scope: SearchScope;
  k?: number;
}

export function useSearchImages({ query, scope, k = 12 }: UseSearchImagesInput) {
  const { accessToken, user } = useSession();
  const { apiBaseUrl, isLoading: isBaseUrlLoading } = useApiBaseUrl();
  const trimmedQuery = query.trim();

  return useQuery({
    queryKey: ['search', trimmedQuery, scope, k, user?.id ?? 'anonymous', apiBaseUrl],
    queryFn: () =>
      searchImages({
        q: trimmedQuery,
        k,
        scope,
        token: accessToken,
        baseUrl: apiBaseUrl,
      }),
    enabled: !isBaseUrlLoading && trimmedQuery.length > 0,
    staleTime: 20_000,
  });
}
