import { getStoredApiBaseUrl } from '@/storage/settingsStore';

import type { ApiErrorShape, HealthResponse } from './types';

export const DEFAULT_API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL?.trim() || 'http://localhost:8000';

export function normalizeBaseUrl(value: string) {
  return value.trim().replace(/\/+$/, '');
}

interface ApiFetchOptions extends RequestInit {
  baseUrl?: string;
  token?: string | null;
}

export class ApiError extends Error {
  status: number;
  code: string;
  details?: unknown;

  constructor(error: ApiErrorShape) {
    super(error.message);
    this.name = 'ApiError';
    this.status = error.status;
    this.code = error.code;
    this.details = error.details;
  }
}

export async function resolveApiBaseUrl() {
  return normalizeBaseUrl((await getStoredApiBaseUrl()) ?? DEFAULT_API_BASE_URL);
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const baseUrl = normalizeBaseUrl(options.baseUrl ?? (await resolveApiBaseUrl()));
  const url = `${baseUrl}${path.startsWith('/') ? path : `/${path}`}`;
  const headers = new Headers(options.headers);

  if (options.token) {
    headers.set('Authorization', `Bearer ${options.token}`);
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  const contentType = response.headers.get('content-type') ?? '';
  const body = contentType.includes('application/json') ? await response.json() : await response.text();

  if (!response.ok) {
    throw new ApiError({
      status: response.status,
      code: typeof body === 'object' && body && 'code' in body ? String(body.code) : 'api_error',
      message:
        typeof body === 'object' && body && 'detail' in body
          ? String(body.detail)
          : typeof body === 'object' && body && 'message' in body
            ? String(body.message)
            : `Request failed with status ${response.status}`,
      details: body,
    });
  }

  return body as T;
}

export function fetchHealth({ baseUrl }: { baseUrl?: string } = {}) {
  return apiFetch<HealthResponse>('/health', {
    baseUrl,
    method: 'GET',
  });
}
