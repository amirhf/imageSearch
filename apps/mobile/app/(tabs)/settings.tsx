import { useQuery, useQueryClient } from '@tanstack/react-query';
import Constants from 'expo-constants';
import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { fetchHealth } from '@/api/client';
import { ActionButton } from '@/components/ActionButton';
import { InfoRow } from '@/components/InfoRow';
import { Screen } from '@/components/Screen';
import { StatusBadge } from '@/components/StatusBadge';
import { useSession } from '@/auth/useSession';
import { useBackendAuth } from '@/features/auth/useBackendAuth';
import { clearRecentJobs } from '@/features/jobs/jobStore';
import { useRecentJobs } from '@/features/jobs/useRecentJobs';
import { useApiBaseUrl } from '@/hooks/useApiBaseUrl';
import { useNetworkState } from '@/hooks/useNetworkState';
import { colors, radii, spacing, typography } from '@/theme/tokens';

export default function SettingsScreen() {
  const queryClient = useQueryClient();
  const { user, signOut, isConfigured, isLoading: isAuthLoading } = useSession();
  const { apiBaseUrl, defaultApiBaseUrl, isLoading, setApiBaseUrl, resetApiBaseUrl } =
    useApiBaseUrl();
  const network = useNetworkState();
  const { jobs } = useRecentJobs();
  const [draftBaseUrl, setDraftBaseUrl] = useState<string | null>(null);
  const [isClearingJobs, setIsClearingJobs] = useState(false);
  const [isSigningOut, setIsSigningOut] = useState(false);
  const visibleBaseUrl = draftBaseUrl ?? apiBaseUrl;
  const activeJobCount = jobs.filter(
    (job) => job.status === 'uploading' || job.status === 'queued' || job.status === 'processing',
  ).length;
  const retryPendingCount = jobs.filter((job) => job.status === 'retry_pending').length;

  const healthQuery = useQuery({
    queryKey: ['health', apiBaseUrl],
    queryFn: () => fetchHealth({ baseUrl: apiBaseUrl }),
    enabled: !isLoading && apiBaseUrl.length > 0,
    retry: false,
  });
  const backendAuthQuery = useBackendAuth();

  const healthTone = healthQuery.isSuccess ? 'success' : healthQuery.isError ? 'danger' : 'muted';
  const healthLabel = healthQuery.isSuccess
    ? 'healthy'
    : healthQuery.isError
      ? 'unreachable'
      : healthQuery.isFetching
        ? 'checking'
        : 'not checked';
  const backendAuthTone = backendAuthQuery.isSuccess
    ? backendAuthQuery.data.authenticated
      ? 'success'
      : 'danger'
    : backendAuthQuery.isError
      ? 'danger'
      : backendAuthQuery.isFetching
        ? 'muted'
        : 'muted';
  const backendAuthLabel = backendAuthQuery.isSuccess
    ? backendAuthQuery.data.authenticated
      ? 'accepted'
      : 'rejected'
    : backendAuthQuery.isError
      ? 'failed'
      : backendAuthQuery.isFetching
        ? 'checking'
        : user
          ? 'not checked'
          : 'anonymous';

  async function handleSignOut() {
    setIsSigningOut(true);
    try {
      await signOut();
    } finally {
      setIsSigningOut(false);
    }
  }

  async function handleClearRecentJobs() {
    setIsClearingJobs(true);
    try {
      await clearRecentJobs();
    } finally {
      setIsClearingJobs(false);
    }
  }

  function handleClearQueryCache() {
    queryClient.clear();
  }

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
        <View style={styles.panelHeader}>
          <Text style={styles.panelTitle}>Account</Text>
          <StatusBadge label={backendAuthLabel} tone={backendAuthTone} />
        </View>
        <InfoRow label="Supabase config" value={isConfigured ? 'configured' : 'missing env'} />
        <InfoRow
          label="Session"
          value={user ? 'signed in' : isAuthLoading ? 'loading' : 'anonymous'}
        />
        {user?.email ? <InfoRow label="Email" value={user.email} /> : null}
        {user?.id ? <InfoRow label="User ID" value={user.id} /> : null}
        {backendAuthQuery.data?.user?.role ? (
          <InfoRow label="Backend role" value={backendAuthQuery.data.user.role} />
        ) : null}
        {user ? (
          <>
            <View style={styles.actions}>
              <ActionButton
                label="Check auth"
                onPress={() => backendAuthQuery.refetch()}
                variant="secondary"
              />
              <ActionButton
                disabled={isSigningOut}
                label={isSigningOut ? 'Logging out...' : 'Log out'}
                onPress={handleSignOut}
                variant="secondary"
              />
            </View>
            {backendAuthQuery.isError ? (
              <Text style={styles.errorText}>
                {backendAuthQuery.error instanceof Error
                  ? backendAuthQuery.error.message
                  : 'Backend auth check failed.'}
              </Text>
            ) : null}
          </>
        ) : (
          <>
            <Text style={styles.helpText}>
              Sign in to unlock mine/all search scopes and private flows.
            </Text>
            <View style={styles.actions}>
              <ActionButton label="Sign in" onPress={() => router.push('/sign-in')} />
              <ActionButton
                label="Create account"
                onPress={() => router.push('/sign-up')}
                variant="secondary"
              />
            </View>
          </>
        )}
      </View>

      <View style={styles.panel}>
        <View style={styles.panelHeader}>
          <Text style={styles.panelTitle}>Network</Text>
          <StatusBadge
            label={network.label}
            tone={network.isOffline ? 'danger' : network.label === 'checking' ? 'muted' : 'success'}
          />
        </View>
        <InfoRow label="Connection" value={network.isOffline ? 'offline' : 'online'} />
        <InfoRow label="Transport" value={network.type} />
        <InfoRow
          label="Internet"
          value={
            network.isInternetReachable === null
              ? 'checking'
              : network.isInternetReachable
                ? 'reachable'
                : 'unreachable'
          }
        />
      </View>

      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Local data</Text>
        <InfoRow label="Recent jobs" value={String(jobs.length)} />
        <InfoRow label="Retry pending" value={String(retryPendingCount)} />
        <InfoRow label="Active jobs" value={String(activeJobCount)} />
        <View style={styles.actions}>
          <ActionButton
            label={isClearingJobs ? 'Clearing...' : 'Clear job queue'}
            onPress={handleClearRecentJobs}
            disabled={isClearingJobs}
            variant="danger"
          />
          <ActionButton
            label="Clear query cache"
            onPress={handleClearQueryCache}
            variant="secondary"
          />
        </View>
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
