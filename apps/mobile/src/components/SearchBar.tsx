import { Ionicons } from '@expo/vector-icons';
import { StyleSheet, TextInput, View } from 'react-native';

import { colors, radii, spacing } from '@/theme/tokens';

interface SearchBarProps {
  value: string;
  onChangeText(value: string): void;
  onSubmit(): void;
  isLoading?: boolean;
}

export function SearchBar({ value, onChangeText, onSubmit, isLoading = false }: SearchBarProps) {
  return (
    <View style={styles.searchBox}>
      <Ionicons name={isLoading ? 'sync-outline' : 'search-outline'} size={20} color={colors.muted} />
      <TextInput
        autoCapitalize="none"
        autoCorrect={false}
        blurOnSubmit
        editable={!isLoading}
        onChangeText={onChangeText}
        onSubmitEditing={onSubmit}
        placeholder="Search public images"
        placeholderTextColor={colors.muted}
        returnKeyType="search"
        style={styles.input}
        value={value}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  searchBox: {
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radii.lg,
    borderWidth: 1,
    flexDirection: 'row',
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  input: {
    color: colors.text,
    flex: 1,
    fontSize: 16,
    minHeight: 40,
  },
});
