import { Pressable, StyleSheet, Text, View } from 'react-native';

import type { SearchScope } from '@/api/types';
import { colors, radii, spacing, typography } from '@/theme/tokens';

interface ScopeSelectorProps {
  value: SearchScope;
  onChange(value: SearchScope): void;
  isAuthenticated: boolean;
}

const scopes: { value: SearchScope; label: string; requiresAuth?: boolean }[] = [
  { value: 'public', label: 'Public' },
  { value: 'mine', label: 'Mine', requiresAuth: true },
  { value: 'all', label: 'All', requiresAuth: true },
];

export function ScopeSelector({ value, onChange, isAuthenticated }: ScopeSelectorProps) {
  return (
    <View style={styles.row}>
      {scopes.map((scope) => {
        const isDisabled = Boolean(scope.requiresAuth && !isAuthenticated);
        const isSelected = value === scope.value;

        return (
          <Pressable
            accessibilityRole="button"
            disabled={isDisabled}
            key={scope.value}
            onPress={() => onChange(scope.value)}
            style={({ pressed }) => [
              styles.pill,
              isSelected && styles.selected,
              isDisabled && styles.disabled,
              pressed && !isDisabled && styles.pressed,
            ]}>
            <Text
              style={[
                styles.label,
                isSelected && styles.selectedLabel,
                isDisabled && styles.disabledLabel,
              ]}>
              {scope.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  pill: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radii.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  selected: {
    backgroundColor: colors.accentSoft,
  },
  disabled: {
    opacity: 0.5,
  },
  pressed: {
    opacity: 0.75,
  },
  label: {
    color: colors.muted,
    fontSize: typography.caption,
    fontWeight: '900',
    textTransform: 'uppercase',
  },
  selectedLabel: {
    color: colors.accent,
  },
  disabledLabel: {
    color: colors.muted,
  },
});
