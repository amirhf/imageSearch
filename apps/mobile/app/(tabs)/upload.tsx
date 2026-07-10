import { StyleSheet, Text, View } from 'react-native';

import { AuthRequired } from '@/components/AuthRequired';
import { Screen } from '@/components/Screen';
import { StatusBadge } from '@/components/StatusBadge';
import { useSession } from '@/auth/useSession';
import { colors, radii, spacing, typography } from '@/theme/tokens';

export default function UploadScreen() {
  const { user } = useSession();

  if (!user) {
    return (
      <Screen title="Upload" subtitle="Sign in before sending private images to ingestion.">
        <AuthRequired action="upload images" />
      </Screen>
    );
  }

  return (
    <Screen title="Upload" subtitle="Native image picking and async ingestion arrive in Phase 4.">
      <View style={styles.panel}>
        <Text style={styles.title}>Upload pipeline placeholder</Text>
        <Text style={styles.copy}>
          This tab is reserved for expo-image-picker, visibility selection, multipart upload, and
          local retry queue work.
        </Text>
        <View style={styles.badges}>
          <StatusBadge label="photo library" />
          <StatusBadge label="camera" />
          <StatusBadge label="async job" tone="accent" />
        </View>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  panel: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radii.lg,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  title: {
    color: colors.text,
    fontSize: typography.subtitle,
    fontWeight: '800',
  },
  copy: {
    color: colors.muted,
    fontSize: typography.body,
    lineHeight: 22,
  },
  badges: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
});
