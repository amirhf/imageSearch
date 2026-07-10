import { useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';

import { getJobStatus } from '@/api/jobs';
import { useSession } from '@/auth/useSession';
import {
  type LocalJobRecord,
  updateJobFromRemote,
} from '@/features/jobs/jobStore';
import { useApiBaseUrl } from '@/hooks/useApiBaseUrl';
import { useNetworkState } from '@/hooks/useNetworkState';

function isPollingStatus(status: LocalJobRecord['status']) {
  return status === 'queued' || status === 'processing' || status === 'uploading';
}

export function useJobPolling(job: LocalJobRecord | undefined) {
  const { accessToken } = useSession();
  const { apiBaseUrl, isLoading: isBaseUrlLoading } = useApiBaseUrl();
  const { isOffline } = useNetworkState();
  const jobId = job?.jobId;
  const shouldPoll = Boolean(
    jobId &&
      accessToken &&
      !isBaseUrlLoading &&
      !isOffline &&
      job &&
      isPollingStatus(job.status),
  );

  const query = useQuery({
    queryKey: ['job', jobId, apiBaseUrl],
    queryFn: () =>
      getJobStatus({
        baseUrl: apiBaseUrl,
        jobId: jobId as string,
        token: accessToken,
      }),
    enabled: Boolean(jobId && accessToken && !isBaseUrlLoading && !isOffline),
    refetchInterval: shouldPoll ? 3000 : false,
    retry: false,
  });

  useEffect(() => {
    if (!job || !query.data) {
      return;
    }

    void updateJobFromRemote(job, query.data.result, query.data.status);
  }, [job, query.data]);

  return {
    ...query,
    isOffline,
  };
}
