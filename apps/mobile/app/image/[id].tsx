import { Ionicons } from '@expo/vector-icons';
import { router, Stack, useLocalSearchParams } from 'expo-router';
import { ActivityIndicator, Alert, Image, StyleSheet, Text, View } from 'react-native';

import { resolveMediaUrl } from '@/api/client';
import type { ImageVisibility } from '@/api/types';
import { useSession } from '@/auth/useSession';
import { ActionButton } from '@/components/ActionButton';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { MetadataRow } from '@/components/MetadataRow';
import { Screen } from '@/components/Screen';
import { StatusBadge } from '@/components/StatusBadge';
import { useImage } from '@/features/images/useImage';
import { useDeleteImage, useUpdateImage } from '@/features/images/useImageMutations';
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
  const { user } = useSession();
  const { apiBaseUrl } = useApiBaseUrl();
  const imageQuery = useImage(imageId);
  const updateImage = useUpdateImage();
  const deleteImage = useDeleteImage();
  const image = imageQuery.data;
  const imageUrl = resolveMediaUrl(image?.download_url ?? image?.thumbnail_url, apiBaseUrl);
  const origin = compactOrigin(image?.caption_origin ?? image?.origin);
  const confidence = formatPercent(image?.caption_confidence ?? image?.confidence);
  const dimensions =
    image?.width && image?.height ? `${image.width} x ${image.height}` : undefined;
  const canManage = Boolean(user?.id && image?.owner_user_id === user.id);
  const nextVisibility: ImageVisibility =
    image?.visibility === 'private' ? 'public' : 'private';

  function updateVisibility() {
    if (!image) {
      return;
    }

    updateImage.mutate({
      id: image.id,
      visibility: nextVisibility,
    });
  }

  function confirmDelete() {
    if (!image) {
      return;
    }

    Alert.alert('Delete image?', 'This removes the image from your searchable library.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: () => {
          deleteImage.mutate(image.id, {
            onSuccess: () => router.replace('/library'),
          });
        },
      },
    ]);
  }

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

          {canManage ? (
            <View style={styles.panel}>
              <Text style={styles.sectionTitle}>Owner actions</Text>
              <Text style={styles.ownerCopy}>
                Change whether this image appears in public search, or remove it from your
                library.
              </Text>
              <View style={styles.actions}>
                <ActionButton
                  disabled={updateImage.isPending}
                  label={
                    updateImage.isPending
                      ? 'Updating...'
                      : nextVisibility === 'public'
                        ? 'Make public'
                        : 'Make private'
                  }
                  onPress={updateVisibility}
                  variant="secondary"
                />
                <ActionButton
                  disabled={deleteImage.isPending}
                  label={deleteImage.isPending ? 'Deleting...' : 'Delete'}
                  onPress={confirmDelete}
                  variant="danger"
                />
              </View>
              {updateImage.isError ? (
                <Text style={styles.errorText}>
                  {updateImage.error instanceof Error
                    ? updateImage.error.message
                    : 'Visibility update failed.'}
                </Text>
              ) : null}
              {deleteImage.isError ? (
                <Text style={styles.errorText}>
                  {deleteImage.error instanceof Error
                    ? deleteImage.error.message
                    : 'Delete failed.'}
                </Text>
              ) : null}
            </View>
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
  ownerCopy: {
    color: colors.muted,
    fontSize: typography.body,
    lineHeight: 22,
  },
  actions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  errorText: {
    color: colors.danger,
    fontSize: typography.caption,
    lineHeight: 18,
  },
});
