import { apiFetch } from '@/api/client';

import type {
  DeleteImageResponse,
  ImageDetail,
  ImageListResponse,
  ImageVisibility,
} from './types';

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

interface ListImagesInput {
  limit?: number;
  offset?: number;
  visibility?: ImageVisibility | 'all';
  token?: string | null;
  baseUrl?: string;
}

export function listImages({
  limit = 100,
  offset = 0,
  visibility = 'all',
  token,
  baseUrl,
}: ListImagesInput = {}) {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });

  if (visibility !== 'all') {
    params.set('visibility', visibility);
  }

  return apiFetch<ImageListResponse>(`/images?${params.toString()}`, {
    baseUrl,
    method: 'GET',
    token,
  });
}

interface UpdateImageInput {
  id: string;
  visibility: ImageVisibility;
  token: string;
  baseUrl?: string;
}

export function updateImageVisibility({ id, visibility, token, baseUrl }: UpdateImageInput) {
  return apiFetch<ImageDetail>(`/images/${encodeURIComponent(id)}`, {
    baseUrl,
    body: JSON.stringify({ visibility }),
    headers: {
      'Content-Type': 'application/json',
    },
    method: 'PATCH',
    token,
  });
}

interface DeleteImageInput {
  id: string;
  token: string;
  baseUrl?: string;
}

export function deleteImage({ id, token, baseUrl }: DeleteImageInput) {
  return apiFetch<DeleteImageResponse>(`/images/${encodeURIComponent(id)}`, {
    baseUrl,
    method: 'DELETE',
    token,
  });
}
