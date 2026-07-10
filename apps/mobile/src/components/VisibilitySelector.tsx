import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { UploadVisibility } from '@/api/types';
import { colors, radii, spacing, typography } from '@/theme/tokens';

interface VisibilitySelectorProps {
  value: UploadVisibility;
  onChange(value: UploadVisibility): void;
}

const options: { value: UploadVisibility; label: string; copy: string }[] = [
  { value: 'private', label: 'Private', copy: 'Only your account' },
  { value: 'public', label: 'Public', copy: 'Searchable by everyone' },
];

export function VisibilitySelector({ value, onChange }: VisibilitySelectorProps) {
  return (
    <View style={styles.row}>
      {options.map((option) => {
        const isSelected = value === option.value;

        return (
          <Pressable
            accessibilityRole="button"
            key={option.value}
            onPress={() => onChange(option.value)}
            style={({ pressed }) => [
              styles.option,
              isSelected && styles.selected,
              pressed && styles.pressed,
            ]}>
            <Text style={[styles.label, isSelected && styles.selectedLabel]}>{option.label}</Text>
            <Text style={styles.copy}>{option.copy}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  option: {
    backgroundColor: colors.surfaceMuted,
    borderColor: colors.border,
    borderRadius: radii.md,
    borderWidth: 1,
    flex: 1,
    gap: spacing.xs,
    minHeight: 72,
    padding: spacing.md,
  },
  selected: {
    backgroundColor: colors.accentSoft,
    borderColor: colors.accent,
  },
  pressed: {
    opacity: 0.78,
  },
  label: {
    color: colors.text,
    fontSize: typography.body,
    fontWeight: '900',
  },
  selectedLabel: {
    color: colors.accent,
  },
  copy: {
    color: colors.muted,
    fontSize: typography.caption,
    fontWeight: '700',
    lineHeight: 16,
  },
});
