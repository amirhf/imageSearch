import { useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { ActionButton } from '@/components/ActionButton';
import { EmptyState } from '@/components/EmptyState';
import { ErrorState } from '@/components/ErrorState';
import { ImageCard } from '@/components/ImageCard';
import { Screen } from '@/components/Screen';
import { ScopeSelector } from '@/components/ScopeSelector';
import { SearchBar } from '@/components/SearchBar';
import type { SearchScope } from '@/api/types';
import { useSession } from '@/auth/useSession';
import { useSearchImages } from '@/features/search/useSearchImages';
import { useApiBaseUrl } from '@/hooks/useApiBaseUrl';
import { useNetworkState } from '@/hooks/useNetworkState';
import { colors, spacing, typography } from '@/theme/tokens';

export default function SearchScreen() {
  const { user } = useSession();
  const { apiBaseUrl } = useApiBaseUrl();
  const { isOffline } = useNetworkState();
  const [draftQuery, setDraftQuery] = useState('');
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [scope, setScope] = useState<SearchScope>('public');
  const activeScope: SearchScope = user ? scope : 'public';
  const searchQuery = useSearchImages({ query: submittedQuery, scope: activeScope });

  function handleSubmit() {
    setSubmittedQuery(draftQuery.trim());
  }

  const results = searchQuery.data?.results ?? [];
  const hasSubmittedQuery = submittedQuery.length > 0;
  const isShowingCachedResults = isOffline && Boolean(searchQuery.data) && hasSubmittedQuery;
  const isOfflineWithoutCache = isOffline && hasSubmittedQuery && !searchQuery.data;

  return (
    <Screen
      title="Search"
      subtitle="Search the public gallery now. Authenticated scopes are ready for the sign-in phase.">
      <SearchBar
        value={draftQuery}
        onChangeText={setDraftQuery}
        onSubmit={handleSubmit}
        isLoading={searchQuery.isFetching && !searchQuery.data}
      />

      <ScopeSelector value={activeScope} onChange={setScope} isAuthenticated={Boolean(user)} />

      <View style={styles.actionRow}>
        <ActionButton
          label={searchQuery.isFetching ? 'Searching...' : 'Search'}
          onPress={handleSubmit}
          disabled={!draftQuery.trim() || searchQuery.isFetching}
        />
        {hasSubmittedQuery ? (
          <Text style={styles.resultCount}>
            {searchQuery.isSuccess ? `${results.length} result${results.length === 1 ? '' : 's'}` : activeScope}
          </Text>
        ) : null}
      </View>

      {!hasSubmittedQuery ? (
        <EmptyState
          title="Start with a visual idea"
          copy="Try a plain-language query like beach sunset, red car, product photo, or city skyline."
        />
      ) : null}

      {searchQuery.isLoading ? (
        <View style={styles.loadingPanel}>
          <ActivityIndicator color={colors.accent} />
          <Text style={styles.loadingText}>Searching public embeddings...</Text>
        </View>
      ) : null}

      {isShowingCachedResults ? (
        <Text style={styles.offlineText}>Offline: showing cached results until you reconnect.</Text>
      ) : null}

      {isOfflineWithoutCache ? (
        <ErrorState
          title="Offline"
          message="Search needs a connection unless this query is already cached on this device."
        />
      ) : null}

      {searchQuery.isError && !isOffline ? (
        <ErrorState
          title="Search failed"
          message={
            searchQuery.error instanceof Error
              ? searchQuery.error.message
              : 'The backend did not return search results.'
          }
          onRetry={() => searchQuery.refetch()}
        />
      ) : null}

      {searchQuery.isSuccess && results.length === 0 ? (
        <EmptyState
          icon="albums-outline"
          title="No matching public images"
          copy="Try a broader description or check that the backend has public images with embeddings."
        />
      ) : null}

      {searchQuery.isSuccess && results.length > 0 ? (
        <View style={styles.results}>
          {searchQuery.isFetching ? <Text style={styles.refreshingText}>Refreshing results...</Text> : null}
          {results.map((result) => (
            <ImageCard key={result.id} result={result} apiBaseUrl={apiBaseUrl} />
          ))}
        </View>
      ) : null}
    </Screen>
  );
}

const styles = StyleSheet.create({
  actionRow: {
    alignItems: 'center',
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
  },
  resultCount: {
    color: colors.muted,
    fontSize: typography.body,
    fontWeight: '700',
  },
  loadingPanel: {
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.xl,
  },
  loadingText: {
    color: colors.muted,
    fontSize: typography.body,
    fontWeight: '700',
  },
  results: {
    gap: spacing.md,
  },
  refreshingText: {
    color: colors.muted,
    fontSize: typography.caption,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
  offlineText: {
    color: colors.danger,
    fontSize: typography.caption,
    fontWeight: '800',
    lineHeight: 18,
    textTransform: 'uppercase',
  },
});
