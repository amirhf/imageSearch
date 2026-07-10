import { apiFetch } from '@/api/client';

import type { SearchResponse, SearchScope } from './types';

interface SearchImagesInput {
  q: string;
  k?: number;
  scope?: SearchScope;
  token?: string | null;
  baseUrl?: string;
}

export function searchImages({
  q,
  k = 12,
  scope = 'public',
  token,
  baseUrl,
}: SearchImagesInput) {
  const params = new URLSearchParams({
    q,
    k: String(k),
    scope,
  });

  return apiFetch<SearchResponse>(`/search?${params.toString()}`, {
    baseUrl,
    method: 'GET',
    token,
  });
}
