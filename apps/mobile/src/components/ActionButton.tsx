import { Pressable, StyleSheet, Text } from 'react-native';

import { colors, radii, spacing, typography } from '@/theme/tokens';

interface ActionButtonProps {
  label: string;
  onPress?: () => void;
  disabled?: boolean;
  variant?: 'primary' | 'secondary';
}

export function ActionButton({
  label,
  onPress,
  disabled = false,
  variant = 'primary',
}: ActionButtonProps) {
  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        variant === 'secondary' && styles.secondary,
        disabled && styles.disabled,
        pressed && !disabled && styles.pressed,
      ]}>
      <Text style={[styles.label, variant === 'secondary' && styles.secondaryLabel]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    alignItems: 'center',
    backgroundColor: colors.accent,
    borderRadius: radii.md,
    justifyContent: 'center',
    minHeight: 46,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  secondary: {
    backgroundColor: colors.accentSoft,
  },
  disabled: {
    opacity: 0.45,
  },
  pressed: {
    backgroundColor: colors.accentPressed,
  },
  label: {
    color: colors.surface,
    fontSize: typography.body,
    fontWeight: '800',
  },
  secondaryLabel: {
    color: colors.accent,
  },
});
