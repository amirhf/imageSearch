import { apiFetch } from './client';
import type { UploadJobResponse, UploadVisibility } from './types';

export interface UploadAsset {
  uri: string;
  fileName?: string | null;
  mimeType?: string | null;
  width?: number | null;
  height?: number | null;
}

interface UploadImageAsyncInput {
  asset: UploadAsset;
  visibility: UploadVisibility;
  token: string;
  baseUrl?: string;
}

function fallbackFileName(asset: UploadAsset) {
  const rawName = asset.fileName ?? asset.uri.split('/').pop();
  const cleanName = rawName?.split('?')[0]?.trim();

  return cleanName && cleanName.includes('.') ? cleanName : `upload-${Date.now()}.jpg`;
}

function fallbackMimeType(asset: UploadAsset) {
  if (asset.mimeType) {
    return asset.mimeType;
  }

  const fileName = fallbackFileName(asset).toLowerCase();
  if (fileName.endsWith('.png')) {
    return 'image/png';
  }
  if (fileName.endsWith('.webp')) {
    return 'image/webp';
  }
  if (fileName.endsWith('.heic') || fileName.endsWith('.heif')) {
    return 'image/heic';
  }

  return 'image/jpeg';
}

export function getUploadFileName(asset: UploadAsset) {
  return fallbackFileName(asset);
}

export function getUploadMimeType(asset: UploadAsset) {
  return fallbackMimeType(asset);
}

export function uploadImageAsync({ asset, visibility, token, baseUrl }: UploadImageAsyncInput) {
  const form = new FormData();

  form.append('file', {
    uri: asset.uri,
    name: fallbackFileName(asset),
    type: fallbackMimeType(asset),
  } as unknown as Blob);
  form.append('visibility', visibility);

  return apiFetch<UploadJobResponse>('/images/async?priority=normal', {
    baseUrl,
    body: form,
    method: 'POST',
    token,
  });
}
