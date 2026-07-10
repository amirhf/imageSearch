import { Ionicons } from '@expo/vector-icons';
import { type Href, router } from 'expo-router';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';

import { resolveMediaUrl } from '@/api/client';
import type { SearchResult } from '@/api/types';
import { StatusBadge } from '@/components/StatusBadge';
import { colors, radii, spacing, typography } from '@/theme/tokens';
import { compactOrigin, formatScore } from '@/utils/format';

interface ImageCardProps {
  result: SearchResult;
  apiBaseUrl: string;
}

export function ImageCard({ result, apiBaseUrl }: ImageCardProps) {
  const thumbnailUrl = resolveMediaUrl(result.thumbnail_url ?? result.download_url, apiBaseUrl);
  const origin = compactOrigin(result.caption_origin ?? result.origin);
  const score = formatScore(result.score);
  const detailHref = `/image/${encodeURIComponent(result.id)}` as Href;

  return (
    <Pressable
      accessibilityRole="button"
      onPress={() => router.push(detailHref)}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}>
      <View style={styles.thumbnailFrame}>
        {thumbnailUrl ? (
          <Image source={{ uri: thumbnailUrl }} resizeMode="cover" style={styles.thumbnail} />
        ) : (
          <View style={styles.thumbnailFallback}>
            <Ionicons name="image-outline" size={28} color={colors.muted} />
          </View>
        )}
      </View>

      <View style={styles.content}>
        <Text numberOfLines={3} style={styles.caption}>
          {result.caption || 'Untitled image'}
        </Text>
        <View style={styles.badges}>
          {score ? <StatusBadge label={`score ${score}`} tone="accent" /> : null}
          {result.visibility ? <StatusBadge label={result.visibility.replace('_', ' ')} /> : null}
          {origin ? <StatusBadge label={`${origin} caption`} /> : null}
        </View>
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
    overflow: 'hidden',
  },
  pressed: {
    opacity: 0.82,
  },
  thumbnailFrame: {
    aspectRatio: 16 / 10,
    backgroundColor: colors.surfaceMuted,
    width: '100%',
  },
  thumbnail: {
    height: '100%',
    width: '100%',
  },
  thumbnailFallback: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
  },
  content: {
    gap: spacing.md,
    padding: spacing.md,
  },
  caption: {
    color: colors.text,
    fontSize: typography.body,
    fontWeight: '800',
    lineHeight: 21,
  },
  badges: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.xs,
  },
});
