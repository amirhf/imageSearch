import { StyleSheet, Text, View } from 'react-native';

import { AuthRequired } from '@/components/AuthRequired';
import { Screen } from '@/components/Screen';
import { StatusBadge } from '@/components/StatusBadge';
import { useSession } from '@/auth/useSession';
import { colors, radii, spacing, typography } from '@/theme/tokens';

export default function LibraryScreen() {
  const { user } = useSession();

  if (!user) {
    return (
      <Screen title="Library" subtitle="Your private image library is scoped to your account.">
        <AuthRequired action="view your library" />
      </Screen>
    );
  }

  return (
    <Screen title="Library" subtitle="User-owned image browsing will build on the API client.">
      <View style={styles.panel}>
        <Text style={styles.title}>Library foundation</Text>
        <Text style={styles.copy}>
          Phase 5 will connect this screen to GET /images with visibility filters and pull to
          refresh.
        </Text>
        <View style={styles.badges}>
          <StatusBadge label="all" tone="accent" />
          <StatusBadge label="private" />
          <StatusBadge label="public" />
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
