import { type NetInfoStateType, useNetInfo } from '@react-native-community/netinfo';
import { onlineManager } from '@tanstack/react-query';
import { createContext, PropsWithChildren, useContext, useEffect, useMemo } from 'react';

interface NetworkContextValue {
  isOffline: boolean;
  isConnected: boolean;
  isInternetReachable: boolean | null;
  type: NetInfoStateType;
  label: string;
}

const NetworkContext = createContext<NetworkContextValue | null>(null);

function networkLabel(value: NetworkContextValue) {
  if (value.isOffline) {
    return 'offline';
  }
  if (value.type === 'unknown') {
    return 'checking';
  }

  return value.type;
}

export function NetworkProvider({ children }: PropsWithChildren) {
  const netInfo = useNetInfo();
  const isOffline = netInfo.isConnected === false || netInfo.isInternetReachable === false;
  const isConnected = !isOffline;

  useEffect(() => {
    onlineManager.setOnline(isConnected);
  }, [isConnected]);

  const value = useMemo<NetworkContextValue>(() => {
    const nextValue = {
      isConnected,
      isInternetReachable: netInfo.isInternetReachable,
      isOffline,
      label: 'checking',
      type: netInfo.type,
    };

    return {
      ...nextValue,
      label: networkLabel(nextValue),
    };
  }, [isConnected, isOffline, netInfo.isInternetReachable, netInfo.type]);

  return <NetworkContext.Provider value={value}>{children}</NetworkContext.Provider>;
}

export function useNetworkContext() {
  const context = useContext(NetworkContext);

  if (!context) {
    throw new Error('useNetworkContext must be used within NetworkProvider.');
  }

  return context;
}
