import { Ionicons } from '@expo/vector-icons';
import { Stack, useLocalSearchParams } from 'expo-router';
import { ActivityIndicator, Image, StyleSheet, Text, View } from 'react-native';

import { resolveMediaUrl } from '@/api/client';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { MetadataRow } from '@/components/MetadataRow';
import { Screen } from '@/components/Screen';
import { StatusBadge } from '@/components/StatusBadge';
import { useImage } from '@/features/images/useImage';
import { useApiBaseUrl } from '@/hooks/useApiBaseUrl';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { compactOrigin, formatBytes, formatDate, formatPercent } from '@/utils/format';

function normalizeParam(value: string | string[] | undefined) {
  if (Array.isArray(value)) {
    return value[0];
  }

  return value;
}

export default function ImageDetailScreen() {
  const params = useLocalSearchParams<{ id?: string | string[] }>();
  const imageId = normalizeParam(params.id);
  const { apiBaseUrl } = useApiBaseUrl();
  const imageQuery = useImage(imageId);
  const image = imageQuery.data;
  const imageUrl = resolveMediaUrl(image?.download_url ?? image?.thumbnail_url, apiBaseUrl);
  const origin = compactOrigin(image?.caption_origin ?? image?.origin);
  const confidence = formatPercent(image?.caption_confidence ?? image?.confidence);
  const dimensions =
    image?.width && image?.height ? `${image.width} x ${image.height}` : undefined;

  return (
    <Screen title="Image" subtitle={image?.caption ?? 'Inspect caption, visibility, and routing metadata.'}>
      <Stack.Screen options={{ title: image?.caption ? 'Image detail' : 'Image' }} />

      {!imageId ? (
        <EmptyState title="Missing image ID" copy="Open an image from search results to view details." />
      ) : null}

      {imageQuery.isLoading ? (
        <View style={styles.loadingPanel}>
          <ActivityIndicator color={colors.accent} />
          <Text style={styles.loadingText}>Loading image metadata...</Text>
        </View>
      ) : null}

      {imageQuery.isError ? (
        <ErrorState
          title="Image unavailable"
          message={
            imageQuery.error instanceof Error
              ? imageQuery.error.message
              : 'The backend did not return this image.'
          }
          onRetry={() => imageQuery.refetch()}
        />
      ) : null}

      {image ? (
        <>
          <View style={styles.imagePanel}>
            {imageUrl ? (
              <Image source={{ uri: imageUrl }} resizeMode="cover" style={styles.image} />
            ) : (
              <View style={styles.imageFallback}>
                <Ionicons name="image-outline" size={34} color={colors.muted} />
              </View>
            )}
          </View>

          <View style={styles.panel}>
            <Text style={styles.caption}>{image.caption ?? 'Untitled image'}</Text>
            <View style={styles.badges}>
              {image.visibility ? (
                <StatusBadge label={image.visibility.replace('_', ' ')} tone="accent" />
              ) : null}
              {origin ? <StatusBadge label={`${origin} caption`} /> : null}
              {confidence ? <StatusBadge label={`confidence ${confidence}`} /> : null}
            </View>
          </View>

          <View style={styles.panel}>
            <Text style={styles.sectionTitle}>Metadata</Text>
            <MetadataRow label="Image ID" value={image.id} />
            <MetadataRow label="Visibility" value={image.visibility?.replace('_', ' ')} />
            <MetadataRow label="Caption origin" value={origin} />
            <MetadataRow label="Confidence" value={confidence} />
            <MetadataRow label="Dimensions" value={dimensions} />
            <MetadataRow label="Format" value={image.format} />
            <MetadataRow label="Size" value={formatBytes(image.size_bytes)} />
            <MetadataRow label="Created" value={formatDate(image.created_at)} />
          </View>
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
  imagePanel: {
    aspectRatio: 1,
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: radii.lg,
    borderWidth: 1,
    overflow: 'hidden',
  },
  image: {
    height: '100%',
    width: '100%',
  },
  imageFallback: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
  },
  panel: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radii.lg,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  caption: {
    color: colors.text,
    fontSize: typography.subtitle,
    fontWeight: '900',
    lineHeight: 26,
  },
  badges: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
  },
  sectionTitle: {
    color: colors.text,
    fontSize: typography.subtitle,
    fontWeight: '900',
  },
});
