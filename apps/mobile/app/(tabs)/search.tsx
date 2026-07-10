import { Ionicons } from '@expo/vector-icons';
import { StyleSheet, Text, TextInput, View } from 'react-native';

import { ActionButton } from '@/components/ActionButton';
import { Screen } from '@/components/Screen';
import { StatusBadge } from '@/components/StatusBadge';
import { colors, radii, spacing, typography } from '@/theme/tokens';

export default function SearchScreen() {
  return (
    <Screen
      title="Search"
      subtitle="Public search lands in the next phase. The shell is ready for the typed API client and result cards.">
      <View style={styles.searchBox}>
        <Ionicons name="search-outline" size={20} color={colors.muted} />
        <TextInput
          editable={false}
          placeholder="Search public images"
          placeholderTextColor={colors.muted}
          style={styles.input}
        />
      </View>

      <View style={styles.scopeRow}>
        <StatusBadge label="public" tone="accent" />
        <StatusBadge label="mine" />
        <StatusBadge label="all" />
      </View>

      <View style={styles.emptyPanel}>
        <Text style={styles.emptyTitle}>Ready for semantic results</Text>
        <Text style={styles.emptyCopy}>
          Phase 1 wires navigation and providers. Phase 2 will connect this screen to
          GET /search with public, mine, and all scopes.
        </Text>
        <ActionButton label="API setup lives in Settings" variant="secondary" disabled />
      </View>
    </Screen>
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
  scopeRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  emptyPanel: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radii.lg,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  emptyTitle: {
    color: colors.text,
    fontSize: typography.subtitle,
    fontWeight: '800',
  },
  emptyCopy: {
    color: colors.muted,
    fontSize: typography.body,
    lineHeight: 22,
  },
});
