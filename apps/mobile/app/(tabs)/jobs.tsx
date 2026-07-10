import { StyleSheet, Text, View } from 'react-native';

import { AuthRequired } from '@/components/AuthRequired';
import { Screen } from '@/components/Screen';
import { StatusBadge } from '@/components/StatusBadge';
import { useSession } from '@/auth/useSession';
import { colors, radii, spacing, typography } from '@/theme/tokens';

export default function JobsScreen() {
  const { user } = useSession();

  if (!user) {
    return (
      <Screen title="Jobs" subtitle="Upload jobs are tied to the authenticated user.">
        <AuthRequired action="track upload jobs" />
      </Screen>
    );
  }

  return (
    <Screen title="Jobs" subtitle="Async ingestion polling and local job history arrive in Phase 4.">
      <View style={styles.panel}>
        <Text style={styles.title}>No recent jobs yet</Text>
        <Text style={styles.copy}>
          This screen will persist queued uploads, poll /jobs/:id, and surface completed image
          details.
        </Text>
        <View style={styles.badges}>
          <StatusBadge label="queued" />
          <StatusBadge label="processing" tone="accent" />
          <StatusBadge label="completed" tone="success" />
          <StatusBadge label="failed" tone="danger" />
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
