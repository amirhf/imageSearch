import { useEffect, useState } from 'react';

import { DEFAULT_API_BASE_URL, normalizeBaseUrl } from '@/api/client';
import {
  clearStoredApiBaseUrl,
  getStoredApiBaseUrl,
  setStoredApiBaseUrl,
} from '@/storage/settingsStore';

export function useApiBaseUrl() {
  const defaultApiBaseUrl = normalizeBaseUrl(DEFAULT_API_BASE_URL);
  const [apiBaseUrl, setApiBaseUrlState] = useState(defaultApiBaseUrl);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    getStoredApiBaseUrl()
      .then((stored) => {
        if (!isMounted) {
          return;
        }
        setApiBaseUrlState(normalizeBaseUrl(stored ?? defaultApiBaseUrl));
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [defaultApiBaseUrl]);

  async function setApiBaseUrl(value: string) {
    const normalized = normalizeBaseUrl(value || defaultApiBaseUrl);
    await setStoredApiBaseUrl(normalized);
    setApiBaseUrlState(normalized);
  }

  async function resetApiBaseUrl() {
    await clearStoredApiBaseUrl();
    setApiBaseUrlState(defaultApiBaseUrl);
  }

  return {
    apiBaseUrl,
    defaultApiBaseUrl,
    isLoading,
    setApiBaseUrl,
    resetApiBaseUrl,
  };
}
