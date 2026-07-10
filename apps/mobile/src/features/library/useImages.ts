import { useQuery } from '@tanstack/react-query';

import { listImages } from '@/api/images';
import type { ImageListItem, ImageVisibility } from '@/api/types';
import { useSession } from '@/auth/useSession';
import { useApiBaseUrl } from '@/hooks/useApiBaseUrl';

export type LibraryVisibilityFilter = 'all' | 'private' | 'public';

function belongsToUser(image: ImageListItem, userId: string | undefined) {
  return Boolean(userId && image.owner_user_id === userId);
}

export function useImages(visibility: LibraryVisibilityFilter) {
  const { accessToken, user } = useSession();
  const { apiBaseUrl, isLoading: isBaseUrlLoading } = useApiBaseUrl();
  const apiVisibility: ImageVisibility | 'all' = visibility === 'public' ? 'public' : visibility;

  return useQuery({
    queryKey: ['images', visibility, user?.id, apiBaseUrl],
    queryFn: async () => {
      const response = await listImages({
        baseUrl: apiBaseUrl,
        limit: 100,
        token: accessToken,
        visibility: apiVisibility,
      });

      return {
        ...response,
        images: response.images.filter((image) => belongsToUser(image, user?.id)),
      };
    },
    enabled: !isBaseUrlLoading && Boolean(accessToken && user?.id),
  });
}
