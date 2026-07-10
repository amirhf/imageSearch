import { useNetInfo } from '@react-native-community/netinfo';

export function useNetworkState() {
  const netInfo = useNetInfo();
  const isOffline = netInfo.isConnected === false || netInfo.isInternetReachable === false;

  return {
    isOffline,
    isConnected: !isOffline,
    type: netInfo.type,
  };
}
