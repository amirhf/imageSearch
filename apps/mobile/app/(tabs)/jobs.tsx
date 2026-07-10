import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import type { UploadAsset } from '@/api/uploads';
import { useSession } from '@/auth/useSession';
import { AuthRequired } from '@/components/AuthRequired';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { JobStatusCard } from '@/components/JobStatusCard';
import { Screen } from '@/components/Screen';
import { type LocalJobRecord } from '@/features/jobs/jobStore';
import { useJobPolling } from '@/features/jobs/useJobPolling';
import { useRecentJobs } from '@/features/jobs/useRecentJobs';
import { useUploadImage } from '@/features/upload/useUploadImage';
import { useNetworkState } from '@/hooks/useNetworkState';
import { colors, spacing, typography } from '@/theme/tokens';

function PollingJobCard({
  job,
  onRetry,
  retryDisabled,
}: {
  job: LocalJobRecord;
  onRetry(job: LocalJobRecord): void;
  retryDisabled: boolean;
}) {
  useJobPolling(job);
  return <JobStatusCard job={job} onRetry={onRetry} retryDisabled={retryDisabled} />;
}

function assetFromJob(job: LocalJobRecord): UploadAsset | null {
  if (!job.assetUri) {
    return null;
  }

  return {
    fileName: job.fileName,
    mimeType: job.mimeType,
    uri: job.assetUri,
  };
}

export default function JobsScreen() {
  const { user } = useSession();
  const { jobs, isLoading } = useRecentJobs();
  const { isOffline } = useNetworkState();
  const uploadMutation = useUploadImage();

  if (!user) {
    return (
      <Screen title="Jobs" subtitle="Upload jobs are tied to the authenticated user.">
        <AuthRequired action="track upload jobs" />
      </Screen>
    );
  }

  function retryUpload(job: LocalJobRecord) {
    const asset = assetFromJob(job);
    if (!asset || isOffline) {
      return;
    }

    uploadMutation.mutate({
      asset,
      localId: job.localId,
      visibility: job.visibility,
    });
  }

  return (
    <Screen title="Jobs" subtitle="Recent async ingestion jobs, persisted locally on this device.">
      {isOffline ? (
        <ErrorState
          title="Offline"
          message="Job polling is paused until the device is back online."
        />
      ) : null}

      {isLoading ? (
        <View style={styles.loadingPanel}>
          <ActivityIndicator color={colors.accent} />
          <Text style={styles.loadingText}>Loading recent jobs...</Text>
        </View>
      ) : null}

      {!isLoading && jobs.length === 0 ? (
        <EmptyState
          icon="cloud-upload-outline"
          title="No upload jobs yet"
          copy="Upload an image to start an async ingestion job and watch its captioning progress."
        />
      ) : null}

      {jobs.length > 0 ? (
        <View style={styles.jobs}>
          {jobs.map((job) => (
            <PollingJobCard
              job={job}
              key={job.localId}
              onRetry={retryUpload}
              retryDisabled={isOffline || uploadMutation.isPending}
            />
          ))}
        </View>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  loadingPanel: {
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.xl,
  },
  loadingText: {
    color: colors.muted,
    fontSize: typography.body,
    fontWeight: '700',
  },
  jobs: {
    gap: spacing.md,
  },
});
