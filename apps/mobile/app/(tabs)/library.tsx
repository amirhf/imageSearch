import { type Href, router } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, Pressable, RefreshControl, StyleSheet, Text, View } from 'react-native';

import type { ImageListItem } from '@/api/types';
import { useSession } from '@/auth/useSession';
import { ActionButton } from '@/components/ActionButton';
import { AuthRequired } from '@/components/AuthRequired';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { ImageCard } from '@/components/ImageCard';
import { Screen } from '@/components/Screen';
import {
  type LibraryVisibilityFilter,
  useImages,
} from '@/features/library/useImages';
import { useApiBaseUrl } from '@/hooks/useApiBaseUrl';
import { colors, radii, spacing, typography } from '@/theme/tokens';

const filters: { value: LibraryVisibilityFilter; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'private', label: 'Private' },
  { value: 'public', label: 'Public' },
];

function FilterTabs({
  value,
  onChange,
}: {
  value: LibraryVisibilityFilter;
  onChange(value: LibraryVisibilityFilter): void;
}) {
  return (
    <View style={styles.filterRow}>
      {filters.map((filter) => {
        const isSelected = value === filter.value;

        return (
          <Pressable
            accessibilityRole="button"
            key={filter.value}
            onPress={() => onChange(filter.value)}
            style={({ pressed }) => [
              styles.filterPill,
              isSelected && styles.filterPillSelected,
              pressed && styles.pressed,
            ]}>
            <Text style={[styles.filterLabel, isSelected && styles.filterLabelSelected]}>
              {filter.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

function imageResult(image: ImageListItem) {
  return {
    ...image,
    score: undefined,
  };
}

export default function LibraryScreen() {
  const { user } = useSession();
  const { apiBaseUrl } = useApiBaseUrl();
  const [filter, setFilter] = useState<LibraryVisibilityFilter>('all');
  const imagesQuery = useImages(filter);
  const images = imagesQuery.data?.images ?? [];

  if (!user) {
    return (
      <Screen title="Library" subtitle="Your private image library is scoped to your account.">
        <AuthRequired action="view your library" />
      </Screen>
    );
  }

  return (
    <Screen
      title="Library"
      subtitle="Browse your uploaded images and manage their visibility."
      action={
        <ActionButton
          label="Upload"
          onPress={() => router.push('/upload' as Href)}
          variant="secondary"
        />
      }
      refreshControl={
        <RefreshControl
          refreshing={imagesQuery.isRefetching}
          onRefresh={() => {
            void imagesQuery.refetch();
          }}
          tintColor={colors.accent}
        />
      }>
      <FilterTabs value={filter} onChange={setFilter} />

      {imagesQuery.isLoading ? (
        <View style={styles.loadingPanel}>
          <ActivityIndicator color={colors.accent} />
          <Text style={styles.loadingText}>Loading your images...</Text>
        </View>
      ) : null}

      {imagesQuery.isError ? (
        <ErrorState
          title="Library unavailable"
          message={
            imagesQuery.error instanceof Error
              ? imagesQuery.error.message
              : 'The backend did not return your image library.'
          }
          onRetry={() => imagesQuery.refetch()}
        />
      ) : null}

      {imagesQuery.isSuccess && images.length === 0 ? (
        <EmptyState
          icon="images-outline"
          title={filter === 'all' ? 'No uploads yet' : `No ${filter} images`}
          copy="Upload a photo to build your searchable mobile library."
        />
      ) : null}

      {images.length > 0 ? (
        <View style={styles.grid}>
          {images.map((image) => (
            <ImageCard apiBaseUrl={apiBaseUrl} key={image.id} result={imageResult(image)} />
          ))}
        </View>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  filterRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  filterPill: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radii.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  filterPillSelected: {
    backgroundColor: colors.accentSoft,
  },
  pressed: {
    opacity: 0.75,
  },
  filterLabel: {
    color: colors.muted,
    fontSize: typography.caption,
    fontWeight: '900',
    textTransform: 'uppercase',
  },
  filterLabelSelected: {
    color: colors.accent,
  },
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
  grid: {
    gap: spacing.md,
  },
});
