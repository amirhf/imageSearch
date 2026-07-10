import { useMutation, useQueryClient } from '@tanstack/react-query';

import { getUploadFileName, getUploadMimeType, uploadImageAsync, type UploadAsset } from '@/api/uploads';
import type { UploadVisibility } from '@/api/types';
import { useSession } from '@/auth/useSession';
import {
  type LocalJobRecord,
  upsertRecentJob,
} from '@/features/jobs/jobStore';
import { useApiBaseUrl } from '@/hooks/useApiBaseUrl';

interface UploadImageInput {
  asset: UploadAsset;
  visibility: UploadVisibility;
  localId: string;
}

function baseJobFromInput(input: UploadImageInput, status: LocalJobRecord['status']): LocalJobRecord {
  const now = new Date().toISOString();

  return {
    localId: input.localId,
    status,
    assetUri: input.asset.uri,
    createdAt: now,
    fileName: getUploadFileName(input.asset),
    mimeType: getUploadMimeType(input.asset),
    updatedAt: now,
    visibility: input.visibility,
  };
}

export function useUploadImage() {
  const { accessToken } = useSession();
  const { apiBaseUrl } = useApiBaseUrl();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: UploadImageInput) => {
      if (!accessToken) {
        throw new Error('Sign in before uploading images.');
      }

      await upsertRecentJob(baseJobFromInput(input, 'uploading'));

      return uploadImageAsync({
        asset: input.asset,
        baseUrl: apiBaseUrl,
        token: accessToken,
        visibility: input.visibility,
      });
    },
    onError: async (error, input) => {
      await upsertRecentJob({
        ...baseJobFromInput(input, 'retry_pending'),
        error: error instanceof Error ? error.message : 'Upload failed.',
      });
    },
    onSuccess: async (response, input) => {
      const now = new Date().toISOString();
      await upsertRecentJob({
        ...baseJobFromInput(input, response.status),
        jobId: response.job_id,
        pollUrl: response.poll_url,
        updatedAt: now,
      });
      await queryClient.invalidateQueries({ queryKey: ['job', response.job_id] });
    },
  });
}
