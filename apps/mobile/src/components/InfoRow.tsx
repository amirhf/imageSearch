import { StyleSheet, Text, View } from 'react-native';

import { colors, spacing, typography } from '@/theme/tokens';

interface InfoRowProps {
  label: string;
  value: string;
}

export function InfoRow({ label, value }: InfoRowProps) {
  return (
    <View style={styles.row}>
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    alignItems: 'flex-start',
    borderTopColor: colors.border,
    borderTopWidth: 1,
    flexDirection: 'row',
    gap: spacing.md,
    justifyContent: 'space-between',
    paddingTop: spacing.md,
  },
  label: {
    color: colors.muted,
    flex: 1,
    fontSize: typography.body,
  },
  value: {
    color: colors.text,
    flex: 1.2,
    fontSize: typography.body,
    fontWeight: '700',
    textAlign: 'right',
  },
});
