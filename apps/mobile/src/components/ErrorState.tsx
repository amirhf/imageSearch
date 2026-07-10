import { StyleSheet, Text, View } from 'react-native';

import { ActionButton } from '@/components/ActionButton';
import { colors, radii, spacing, typography } from '@/theme/tokens';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ title = 'Something went wrong', message, onRetry }: ErrorStateProps) {
  return (
    <View style={styles.panel}>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.copy}>{message}</Text>
      {onRetry ? <ActionButton label="Try again" variant="secondary" onPress={onRetry} /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  panel: {
    backgroundColor: colors.dangerSoft,
    borderColor: '#F6B8B3',
    borderRadius: radii.lg,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  title: {
    color: colors.danger,
    fontSize: typography.subtitle,
    fontWeight: '800',
  },
  copy: {
    color: colors.danger,
    fontSize: typography.body,
    lineHeight: 22,
  },
});
