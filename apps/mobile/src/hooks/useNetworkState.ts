import { useNetworkContext } from '@/providers/NetworkProvider';

export function useNetworkState() {
  return useNetworkContext();
}
