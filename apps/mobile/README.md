# Image Search Mobile

Expo + React Native companion app for the AI Image Search platform.

This app is a thin mobile client for the existing FastAPI backend. Phase 1 sets up the app shell, Expo Router tabs, Supabase auth provider, TanStack Query, API base URL settings, and a backend health check.

## Requirements

- Node LTS through nvm. This repo has been verified with `v24.11.1`.
- Watchman.
- Expo Go on a physical iOS or Android device for the current local setup.

Full iOS Simulator testing requires Xcode. Android Emulator testing requires Android Studio, JDK, and Android SDK tooling.

## Environment

```bash
cp .env.example .env
```

Set:

```bash
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your-supabase-publishable-or-anon-key
```

For a physical phone, `localhost` points to the phone, not this Mac. Use the Mac LAN IP instead, for example:

```bash
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.25:8000
```

You can also override the API base URL from the Settings tab.

## Run

```bash
source ~/.nvm/nvm.sh
nvm use 24.11.1
npm install
npx expo start
```

Scan the QR code with Expo Go.

## Scripts

```bash
npm run typecheck
npm run lint
npm run web
```

## Phase 1 Scope

- App shell and tabs.
- Supabase AuthProvider with AsyncStorage-backed session persistence.
- TanStack Query provider.
- API client shell with normalized errors.
- Settings screen with API base URL override and `GET /health` check.
- Auth-required placeholders for Upload, Library, and Jobs.

Next phases add public search, authenticated auth flows, upload, job polling, library browsing, and offline retry.
