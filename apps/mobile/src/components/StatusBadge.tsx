import { StyleSheet, Text, View } from 'react-native';

import { colors, radii, spacing, typography } from '@/theme/tokens';

type BadgeTone = 'muted' | 'accent' | 'success' | 'danger';

interface StatusBadgeProps {
  label: string;
  tone?: BadgeTone;
}

const toneStyles = {
  muted: {
    backgroundColor: colors.surfaceMuted,
    color: colors.muted,
  },
  accent: {
    backgroundColor: colors.accentSoft,
    color: colors.accent,
  },
  success: {
    backgroundColor: colors.successSoft,
    color: colors.success,
  },
  danger: {
    backgroundColor: colors.dangerSoft,
    color: colors.danger,
  },
} as const;

export function StatusBadge({ label, tone = 'muted' }: StatusBadgeProps) {
  const toneStyle = toneStyles[tone];

  return (
    <View style={[styles.badge, { backgroundColor: toneStyle.backgroundColor }]}>
      <Text style={[styles.label, { color: toneStyle.color }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: 'flex-start',
    borderRadius: radii.sm,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
  },
  label: {
    fontSize: typography.caption,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
});
