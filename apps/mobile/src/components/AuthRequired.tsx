import { router } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { ActionButton } from '@/components/ActionButton';
import { colors, radii, spacing, typography } from '@/theme/tokens';

interface AuthRequiredProps {
  action: string;
}

export function AuthRequired({ action }: AuthRequiredProps) {
  return (
    <View style={styles.panel}>
      <Text style={styles.title}>Sign in required</Text>
      <Text style={styles.copy}>You need an authenticated Supabase session to {action}.</Text>
      <View style={styles.actions}>
        <ActionButton label="Sign in" onPress={() => router.push('/sign-in')} />
        <ActionButton
          label="Create account"
          onPress={() => router.push('/sign-up')}
          variant="secondary"
        />
      </View>
    </View>
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
  actions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
});
