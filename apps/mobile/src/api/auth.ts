import { apiFetch } from './client';
import type { AuthMeResponse } from './types';

interface GetCurrentUserInput {
  token?: string | null;
  baseUrl?: string;
}

export function getCurrentUser({ token, baseUrl }: GetCurrentUserInput = {}) {
  return apiFetch<AuthMeResponse>('/auth/me', {
    baseUrl,
    method: 'GET',
    token,
  });
}
