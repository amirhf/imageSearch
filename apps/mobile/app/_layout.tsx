import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

import { AppProviders } from '@/providers/AppProviders';
import { colors } from '@/theme/tokens';

export default function RootLayout() {
  return (
    <AppProviders>
      <StatusBar style="dark" />
      <Stack
        screenOptions={{
          contentStyle: { backgroundColor: colors.canvas },
          headerShadowVisible: false,
          headerStyle: { backgroundColor: colors.canvas },
          headerTitleStyle: { color: colors.text, fontSize: 17, fontWeight: '700' },
        }}>
        <Stack.Screen name="index" options={{ headerShown: false }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen
          name="(auth)/sign-in"
          options={{ presentation: 'modal', title: 'Sign in' }}
        />
        <Stack.Screen
          name="(auth)/sign-up"
          options={{ presentation: 'modal', title: 'Create account' }}
        />
        <Stack.Screen name="image/[id]" options={{ title: 'Image detail' }} />
        <Stack.Screen name="job/[id]" options={{ title: 'Job detail' }} />
      </Stack>
    </AppProviders>
  );
}
