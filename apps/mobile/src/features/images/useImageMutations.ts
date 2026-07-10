import { useMutation, useQueryClient } from '@tanstack/react-query';

import { deleteImage, updateImageVisibility } from '@/api/images';
import type { ImageVisibility } from '@/api/types';
import { useSession } from '@/auth/useSession';
import { useApiBaseUrl } from '@/hooks/useApiBaseUrl';

export function useUpdateImage() {
  const { accessToken } = useSession();
  const { apiBaseUrl } = useApiBaseUrl();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, visibility }: { id: string; visibility: ImageVisibility }) => {
      if (!accessToken) {
        throw new Error('Sign in before updating images.');
      }

      return updateImageVisibility({
        baseUrl: apiBaseUrl,
        id,
        token: accessToken,
        visibility,
      });
    },
    onSuccess: async (image) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['image', image.id] }),
        queryClient.invalidateQueries({ queryKey: ['images'] }),
        queryClient.invalidateQueries({ queryKey: ['search'] }),
      ]);
    },
  });
}

export function useDeleteImage() {
  const { accessToken } = useSession();
  const { apiBaseUrl } = useApiBaseUrl();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => {
      if (!accessToken) {
        throw new Error('Sign in before deleting images.');
      }

      return deleteImage({
        baseUrl: apiBaseUrl,
        id,
        token: accessToken,
      });
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['images'] }),
        queryClient.invalidateQueries({ queryKey: ['search'] }),
      ]);
    },
  });
}
