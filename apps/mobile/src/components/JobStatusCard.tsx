import { Ionicons } from '@expo/vector-icons';
import { type Href, router } from 'expo-router';
import { ActivityIndicator, Image, Pressable, StyleSheet, Text, View } from 'react-native';

import { resolveMediaUrl } from '@/api/client';
import type { JobStatus } from '@/api/types';
import { ActionButton } from '@/components/ActionButton';
import { StatusBadge } from '@/components/StatusBadge';
import { type LocalJobRecord } from '@/features/jobs/jobStore';
import { useApiBaseUrl } from '@/hooks/useApiBaseUrl';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { formatDate } from '@/utils/format';

interface JobStatusCardProps {
  job: LocalJobRecord;
  onRetry?: (job: LocalJobRecord) => void;
  compact?: boolean;
}

const statusLabels: Record<JobStatus, string> = {
  completed: 'completed',
  failed: 'failed',
  processing: 'processing',
  queued: 'queued',
  retry_pending: 'retry pending',
  uploading: 'uploading',
};

function statusTone(status: JobStatus) {
  if (status === 'completed') {
    return 'success';
  }
  if (status === 'failed' || status === 'retry_pending') {
    return 'danger';
  }
  if (status === 'processing' || status === 'uploading') {
    return 'accent';
  }
  return 'muted';
}

function isActive(status: JobStatus) {
  return status === 'uploading' || status === 'queued' || status === 'processing';
}

export function JobStatusCard({ job, onRetry, compact = false }: JobStatusCardProps) {
  const { apiBaseUrl } = useApiBaseUrl();
  const imageHref = job.imageId ? (`/image/${encodeURIComponent(job.imageId)}` as Href) : null;
  const jobHref = `/job/${encodeURIComponent(job.jobId ?? job.localId)}` as Href;
  const thumbnailUrl = resolveMediaUrl(job.thumbnailUrl ?? job.assetUri, apiBaseUrl);

  return (
    <Pressable
      accessibilityRole="button"
      onPress={() => router.push(jobHref)}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}>
      {thumbnailUrl ? (
        <Image source={{ uri: thumbnailUrl }} resizeMode="cover" style={styles.thumbnail} />
      ) : (
        <View style={styles.thumbnailFallback}>
          <Ionicons name="image-outline" size={24} color={colors.muted} />
        </View>
      )}

      <View style={styles.content}>
        <View style={styles.header}>
          <StatusBadge label={statusLabels[job.status]} tone={statusTone(job.status)} />
          {isActive(job.status) ? <ActivityIndicator color={colors.accent} size="small" /> : null}
        </View>

        <Text numberOfLines={compact ? 1 : 2} style={styles.title}>
          {job.caption ?? job.fileName ?? 'Image upload'}
        </Text>

        <View style={styles.metaRow}>
          <Text style={styles.meta}>{job.visibility}</Text>
          <Text style={styles.meta}>{formatDate(job.updatedAt)}</Text>
        </View>

        {job.error ? (
          <Text numberOfLines={compact ? 1 : 3} style={styles.errorText}>
            {job.error}
          </Text>
        ) : null}

        {!compact ? (
          <View style={styles.actions}>
            {imageHref ? (
              <ActionButton
                label="Open image"
                onPress={() => router.push(imageHref)}
                variant="secondary"
              />
            ) : null}
            {job.status === 'retry_pending' && onRetry ? (
              <ActionButton label="Retry" onPress={() => onRetry(job)} />
            ) : null}
          </View>
        ) : null}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radii.lg,
    borderWidth: 1,
    flexDirection: 'row',
    gap: spacing.md,
    overflow: 'hidden',
    padding: spacing.md,
  },
  pressed: {
    opacity: 0.82,
  },
  thumbnail: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radii.md,
    height: 86,
    width: 86,
  },
  thumbnailFallback: {
    alignItems: 'center',
    backgroundColor: colors.surfaceMuted,
    borderRadius: radii.md,
    height: 86,
    justifyContent: 'center',
    width: 86,
  },
  content: {
    flex: 1,
    gap: spacing.sm,
  },
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  title: {
    color: colors.text,
    fontSize: typography.body,
    fontWeight: '900',
    lineHeight: 21,
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  meta: {
    color: colors.muted,
    fontSize: typography.caption,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
  errorText: {
    color: colors.danger,
    fontSize: typography.caption,
    lineHeight: 17,
  },
  actions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
});
