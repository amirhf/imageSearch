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
      <ActionButton label="Sign in" onPress={() => router.push('/sign-in')} />
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
});
