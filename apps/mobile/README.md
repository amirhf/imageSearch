# Image Search Mobile

Expo + React Native companion app for the AI Image Search platform.

This app is a thin mobile client for the existing FastAPI backend. It currently includes the app shell, Expo Router tabs, persistent Supabase auth, TanStack Query, API base URL settings, backend health and auth checks, public/authenticated search scopes, native image upload, async job polling, offline-aware retry handling, library browsing, image mutations, and image detail.

Reviewer shortcut: [Mobile Companion Reviewer Guide](./docs/reviewer-guide.md).

<p>
  <img src="./docs/assets/search-empty.png" width="220" alt="Mobile search screen" />
  <img src="./docs/assets/upload-empty.png" width="220" alt="Mobile upload screen" />
</p>

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

For Android Emulator, use `http://10.0.2.2:8000` as the backend base URL.

## Run

```bash
source ~/.nvm/nvm.sh
nvm use 24.11.1
npm install
npx expo start
```

Scan the QR code with Expo Go.

For iOS Simulator smoke testing:

```bash
source ~/.nvm/nvm.sh
nvm use 24.11.1
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer \
REACT_NATIVE_PACKAGER_HOSTNAME=$(ipconfig getifaddr en0) \
npx expo start --ios --host lan
```

## Scripts

```bash
npm run typecheck
npm run lint
npm run web
```

## Reviewer Flow

1. Start the FastAPI backend and confirm `GET /health`.
2. Start this Expo app.
3. Search public images anonymously.
4. Sign in with Supabase.
5. Upload from photo library or camera with private/public visibility.
6. Track the async job to completion.
7. Open the completed image detail screen.
8. Search `mine` for generated caption terms.
9. Toggle offline mode to verify retry-pending and stale-cache states.

See [docs/reviewer-guide.md](./docs/reviewer-guide.md) for the architecture diagram, demo script, and manual QA checklist.

## Current Scope

- App shell and tabs.
- Supabase AuthProvider with AsyncStorage-backed session persistence.
- Sign-in and sign-up screens using the same Supabase project as the web app.
- Logout with private query cache cleanup.
- Settings account panel with `GET /auth/me` backend token verification.
- TanStack Query provider.
- API client shell with normalized errors.
- Settings screen with API base URL override and `GET /health` check.
- Auth-required placeholders for Upload, Library, and Jobs.
- Public and authenticated `GET /search` flows for `public`, `mine`, and `all` scopes.
- Result cards with thumbnails, scores, visibility, and caption origin when returned.
- Read-only `/image/[id]` detail screen with image metadata.
- Photo library and camera selection through `expo-image-picker`.
- Private/public visibility selection for async uploads.
- Authenticated multipart upload to `POST /images/async?priority=normal`.
- Local recent job history with retry-pending upload records.
- `GET /jobs/{job_id}` polling and `/job/[id]` detail screen.
- Owner library view backed by `GET /images`, with all/private/public filters.
- Pull-to-refresh for the mobile library.
- Owner-only visibility updates through `PATCH /images/{id}`.
- Owner-only soft delete through `DELETE /images/{id}`.
- Network state provider with an app-level offline banner.
- Offline upload attempts saved as retry-pending local jobs.
- Job polling and retries paused while offline.
- Cached search results marked as stale while offline.
- Settings actions to clear the local job queue and query cache.

This phase is portfolio-ready for reviewer setup and manual QA.
