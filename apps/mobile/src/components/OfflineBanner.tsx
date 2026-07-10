import { StyleSheet, Text, View } from 'react-native';

import { useNetworkState } from '@/hooks/useNetworkState';
import { colors, spacing, typography } from '@/theme/tokens';

export function OfflineBanner() {
  const { isOffline } = useNetworkState();

  if (!isOffline) {
    return null;
  }

  return (
    <View style={styles.banner}>
      <Text style={styles.text}>Offline mode: uploads and polling are paused.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    backgroundColor: colors.dangerSoft,
    borderBottomColor: '#F6B8B3',
    borderBottomWidth: 1,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
  },
  text: {
    color: colors.danger,
    fontSize: typography.caption,
    fontWeight: '900',
    lineHeight: 17,
    textAlign: 'center',
    textTransform: 'uppercase',
  },
});
