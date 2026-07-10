import { type Href, router, Stack, useLocalSearchParams } from 'expo-router';
import { useMemo } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import type { UploadAsset } from '@/api/uploads';
import { useSession } from '@/auth/useSession';
import { ActionButton } from '@/components/ActionButton';
import { AuthRequired } from '@/components/AuthRequired';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { JobStatusCard } from '@/components/JobStatusCard';
import { MetadataRow } from '@/components/MetadataRow';
import { Screen } from '@/components/Screen';
import { type LocalJobRecord } from '@/features/jobs/jobStore';
import { useJobPolling } from '@/features/jobs/useJobPolling';
import { useRecentJobs } from '@/features/jobs/useRecentJobs';
import { useUploadImage } from '@/features/upload/useUploadImage';
import { useNetworkState } from '@/hooks/useNetworkState';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { formatDate } from '@/utils/format';

function normalizeParam(value: string | string[] | undefined) {
  if (Array.isArray(value)) {
    return value[0];
  }

  return value;
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

export default function JobDetailScreen() {
  const { user } = useSession();
  const params = useLocalSearchParams<{ id?: string | string[] }>();
  const jobKey = normalizeParam(params.id);
  const { jobs, isLoading } = useRecentJobs();
  const { isOffline } = useNetworkState();
  const uploadMutation = useUploadImage();
  const job = useMemo(
    () => jobs.find((item) => item.localId === jobKey || item.jobId === jobKey),
    [jobKey, jobs],
  );
  const jobQuery = useJobPolling(job);
  const imageHref = job?.imageId ? (`/image/${encodeURIComponent(job.imageId)}` as Href) : null;

  if (!user) {
    return (
      <Screen title="Job" subtitle="Upload jobs are tied to the authenticated user.">
        <AuthRequired action="track upload jobs" />
      </Screen>
    );
  }

  function retryUpload() {
    if (!job || isOffline) {
      return;
    }

    const asset = assetFromJob(job);
    if (!asset) {
      return;
    }

    uploadMutation.mutate({
      asset,
      localId: job.localId,
      visibility: job.visibility,
    });
  }

  return (
    <Screen title="Job" subtitle={job?.caption ?? 'Async ingestion status and result metadata.'}>
      <Stack.Screen options={{ title: job?.jobId ? 'Job detail' : 'Upload job' }} />

      {isOffline ? (
        <ErrorState
          title="Offline"
          message="Job polling is paused until the device is back online."
        />
      ) : null}

      {isLoading ? (
        <View style={styles.loadingPanel}>
          <ActivityIndicator color={colors.accent} />
          <Text style={styles.loadingText}>Loading job...</Text>
        </View>
      ) : null}

      {!isLoading && !job ? (
        <EmptyState
          icon="pulse-outline"
          title="Job not found"
          copy="This job is not in the recent local history on this device."
        />
      ) : null}

      {job ? (
        <>
          <JobStatusCard
            job={job}
            onRetry={retryUpload}
            retryDisabled={isOffline || uploadMutation.isPending}
          />

          {jobQuery.isError ? (
            <ErrorState
              title="Polling failed"
              message={
                jobQuery.error instanceof Error
                  ? jobQuery.error.message
                  : 'The backend did not return job status.'
              }
              onRetry={() => jobQuery.refetch()}
            />
          ) : null}

          <View style={styles.panel}>
            <Text style={styles.sectionTitle}>Job metadata</Text>
            <MetadataRow label="Local ID" value={job.localId} />
            <MetadataRow label="Remote job ID" value={job.jobId} />
            <MetadataRow label="Status" value={job.status.replace('_', ' ')} />
            <MetadataRow label="Visibility" value={job.visibility} />
            <MetadataRow label="File" value={job.fileName} />
            <MetadataRow label="Image ID" value={job.imageId} />
            <MetadataRow label="Created" value={formatDate(job.createdAt)} />
            <MetadataRow label="Updated" value={formatDate(job.updatedAt)} />
          </View>

          {imageHref ? (
            <ActionButton label="Open completed image" onPress={() => router.push(imageHref)} />
          ) : null}
        </>
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
  panel: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radii.lg,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: typography.subtitle,
    fontWeight: '900',
  },
});
