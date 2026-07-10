import AsyncStorage from '@react-native-async-storage/async-storage';

const API_BASE_URL_KEY = 'image-search-mobile:api-base-url';

export async function getStoredApiBaseUrl() {
  return AsyncStorage.getItem(API_BASE_URL_KEY);
}

export async function setStoredApiBaseUrl(value: string) {
  const trimmed = value.trim();
  if (!trimmed) {
    await AsyncStorage.removeItem(API_BASE_URL_KEY);
    return null;
  }

  await AsyncStorage.setItem(API_BASE_URL_KEY, trimmed);
  return trimmed;
}

export async function clearStoredApiBaseUrl() {
  await AsyncStorage.removeItem(API_BASE_URL_KEY);
}
