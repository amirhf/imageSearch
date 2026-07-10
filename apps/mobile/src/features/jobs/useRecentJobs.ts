import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';

import {
  getRecentJobs,
  subscribeRecentJobs,
} from '@/features/jobs/jobStore';

export function useRecentJobs() {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ['recent-jobs'],
    queryFn: getRecentJobs,
  });

  useEffect(() => {
    return subscribeRecentJobs(() => {
      void queryClient.invalidateQueries({ queryKey: ['recent-jobs'] });
    });
  }, [queryClient]);

  return {
    jobs: query.data ?? [],
    isLoading: query.isLoading,
    refresh: query.refetch,
  };
}
