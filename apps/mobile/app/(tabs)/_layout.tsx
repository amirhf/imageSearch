import { Ionicons } from '@expo/vector-icons';
import { Tabs } from 'expo-router';

import { colors, radii, spacing } from '@/theme/tokens';

type IconName = keyof typeof Ionicons.glyphMap;

const TAB_ICONS: Record<string, IconName> = {
  search: 'search-outline',
  upload: 'cloud-upload-outline',
  library: 'images-outline',
  jobs: 'pulse-outline',
  settings: 'settings-outline',
};

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: colors.accent,
        tabBarInactiveTintColor: colors.muted,
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '700',
        },
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          height: 78,
          paddingBottom: spacing.md,
          paddingTop: spacing.xs,
        },
        tabBarItemStyle: {
          borderRadius: radii.md,
        },
        tabBarIcon: ({ color, size }) => (
          <Ionicons name={TAB_ICONS[route.name] ?? 'ellipse-outline'} size={size} color={color} />
        ),
      })}>
      <Tabs.Screen name="search" options={{ title: 'Search' }} />
      <Tabs.Screen name="upload" options={{ title: 'Upload' }} />
      <Tabs.Screen name="library" options={{ title: 'Library' }} />
      <Tabs.Screen name="jobs" options={{ title: 'Jobs' }} />
      <Tabs.Screen name="settings" options={{ title: 'Settings' }} />
    </Tabs>
  );
}
