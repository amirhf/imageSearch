import { useQuery } from '@tanstack/react-query';
import Constants from 'expo-constants';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { fetchHealth } from '@/api/client';
import { ActionButton } from '@/components/ActionButton';
import { InfoRow } from '@/components/InfoRow';
import { Screen } from '@/components/Screen';
import { StatusBadge } from '@/components/StatusBadge';
import { useSession } from '@/auth/useSession';
import { useApiBaseUrl } from '@/hooks/useApiBaseUrl';
import { colors, radii, spacing, typography } from '@/theme/tokens';

export default function SettingsScreen() {
  const { user, signOut, isConfigured } = useSession();
  const { apiBaseUrl, defaultApiBaseUrl, isLoading, setApiBaseUrl, resetApiBaseUrl } =
    useApiBaseUrl();
  const [draftBaseUrl, setDraftBaseUrl] = useState<string | null>(null);
  const visibleBaseUrl = draftBaseUrl ?? apiBaseUrl;

  const healthQuery = useQuery({
    queryKey: ['health', apiBaseUrl],
    queryFn: () => fetchHealth({ baseUrl: apiBaseUrl }),
    enabled: !isLoading && apiBaseUrl.length > 0,
    retry: false,
  });

  const healthTone = healthQuery.isSuccess ? 'success' : healthQuery.isError ? 'danger' : 'muted';
  const healthLabel = healthQuery.isSuccess
    ? 'healthy'
    : healthQuery.isError
      ? 'unreachable'
      : healthQuery.isFetching
        ? 'checking'
        : 'not checked';

  return (
    <Screen title="Settings" subtitle="Local configuration, account state, and backend diagnostics.">
      <View style={styles.panel}>
        <View style={styles.panelHeader}>
          <Text style={styles.panelTitle}>Backend</Text>
          <StatusBadge label={healthLabel} tone={healthTone} />
        </View>

        <Text style={styles.label}>API base URL</Text>
        <TextInput
          autoCapitalize="none"
          autoCorrect={false}
          onChangeText={setDraftBaseUrl}
          placeholder={defaultApiBaseUrl}
          placeholderTextColor={colors.muted}
          style={styles.input}
          value={visibleBaseUrl}
        />

        <View style={styles.actions}>
          <ActionButton
            label="Save URL"
            onPress={() => {
              void setApiBaseUrl(visibleBaseUrl);
              setDraftBaseUrl(null);
            }}
            disabled={isLoading}
          />
          <ActionButton
            label="Use default"
            variant="secondary"
            onPress={() => {
              setDraftBaseUrl(null);
              void resetApiBaseUrl();
            }}
            disabled={isLoading}
          />
        </View>

        <Pressable style={styles.textButton} onPress={() => healthQuery.refetch()}>
          <Text style={styles.textButtonLabel}>Check backend health</Text>
        </Pressable>

        {healthQuery.isError && (
          <Text style={styles.errorText}>
            {healthQuery.error instanceof Error
              ? healthQuery.error.message
              : 'Backend health check failed.'}
          </Text>
        )}
      </View>

      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Account</Text>
        <InfoRow label="Supabase config" value={isConfigured ? 'configured' : 'missing env'} />
        <InfoRow label="Signed in as" value={user?.email ?? 'anonymous'} />
        {user ? (
          <ActionButton label="Log out" variant="secondary" onPress={signOut} />
        ) : (
          <Text style={styles.helpText}>Sign-in screens are wired for Phase 3 auth testing.</Text>
        )}
      </View>

      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Build</Text>
        <InfoRow label="App version" value={Constants.expoConfig?.version ?? 'development'} />
        <InfoRow label="Expo SDK" value={Constants.expoConfig?.sdkVersion ?? '57'} />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  panel: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: radii.lg,
    borderWidth: 1,
    gap: spacing.md,
    padding: spacing.lg,
  },
  panelHeader: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  panelTitle: {
    color: colors.text,
    fontSize: typography.subtitle,
    fontWeight: '800',
  },
  label: {
    color: colors.muted,
    fontSize: typography.caption,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  input: {
    backgroundColor: colors.canvas,
    borderColor: colors.border,
    borderRadius: radii.md,
    borderWidth: 1,
    color: colors.text,
    fontSize: 15,
    minHeight: 48,
    paddingHorizontal: spacing.md,
  },
  actions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  textButton: {
    alignSelf: 'flex-start',
  },
  textButtonLabel: {
    color: colors.accent,
    fontSize: typography.body,
    fontWeight: '800',
  },
  errorText: {
    color: colors.danger,
    fontSize: typography.caption,
    lineHeight: 18,
  },
  helpText: {
    color: colors.muted,
    fontSize: typography.body,
    lineHeight: 22,
  },
});
