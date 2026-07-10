import { apiFetch } from './client';
import type { JobStatusResponse } from './types';

interface GetJobStatusInput {
  jobId: string;
  token?: string | null;
  baseUrl?: string;
}

export function getJobStatus({ jobId, token, baseUrl }: GetJobStatusInput) {
  return apiFetch<JobStatusResponse>(`/jobs/${encodeURIComponent(jobId)}`, {
    baseUrl,
    method: 'GET',
    token,
  });
}
