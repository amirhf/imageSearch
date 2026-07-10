import { apiFetch } from '@/api/client';

import type { ImageDetail } from './types';

interface GetImageInput {
  id: string;
  token?: string | null;
  baseUrl?: string;
}

export function getImage({ id, token, baseUrl }: GetImageInput) {
  return apiFetch<ImageDetail>(`/images/${encodeURIComponent(id)}`, {
    baseUrl,
    method: 'GET',
    token,
  });
}
