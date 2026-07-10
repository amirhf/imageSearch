# React Native Companion App Design and Implementation Plan

**Project:** `amirhf/imageSearch`  
**App path:** `apps/mobile`  
**Source spec:** `docs/react-native/image-search-react-native-spec.md`  
**Working title:** Image Search Mobile Companion  
**Status:** Planning document for implementation

---

## 1. Purpose

This document turns the React Native companion app spec into an implementation-ready plan.

The goal is to build a small but complete Expo + React Native mobile client for the existing AI Image Search platform. The app should feel like a natural mobile surface for the current system, not a detached demo. It should demonstrate native mobile workflows such as photo selection, camera capture, persistent auth, async upload tracking, offline-aware retry, and AI routing metadata display.

The app is intentionally thin: React Native owns the mobile experience, while the existing FastAPI gateway, async workers, search service, storage layer, and AI routing policy remain the source of truth.

---

## 2. Product Shape

### 2.1 Primary user value

Users can search public images, sign in, upload photos from a phone, track ingestion jobs, and inspect generated captions plus routing metadata.

### 2.2 Portfolio value

The mobile app should clearly show:

- React Native screen architecture.
- Expo Router navigation.
- Supabase auth persistence.
- Authenticated multipart upload from device image URIs.
- Async job polling.
- Offline-aware retry behavior.
- Mobile-friendly AI search UX.
- Integration with the existing distributed backend.

### 2.3 MVP boundaries

Build the first version as a vertical slice:

- Public search.
- Auth.
- Upload.
- Job tracking.
- Image detail.
- Private/public visibility.
- Basic library.
- Offline-aware retry.
- Settings and diagnostics.

Avoid these in the MVP:

- On-device ML.
- Push notifications.
- Background uploads.
- Native module development.
- App store release.
- Complex offline sync.
- Social sharing.

---

## 3. Technical Decisions

| Area | Decision | Reason |
|---|---|---|
| Framework | Expo + React Native + TypeScript | Fast iteration, Expo Go support, strong portfolio signal. |
| Routing | Expo Router | File-based routing matches the mental model of the existing Next.js app. |
| Auth | Supabase JS client | Backend already validates Supabase bearer tokens. |
| Session persistence | AsyncStorage through Supabase config | Standard native persistence without manually storing tokens. |
| Server state | TanStack Query | Consistent with modern React data fetching and the web app direction. |
| Media | `expo-image-picker` | Supports photo library and camera capture in Expo. |
| Network state | `@react-native-community/netinfo` | Reliable online/offline state for native apps. |
| Local queue | AsyncStorage | Enough for MVP retry metadata. |
| E2E later | Maestro first, Detox later if needed | Maestro is lighter for smoke flows. |
| Build path | Expo Go for MVP, development build later | Keeps native setup friction low at first. |

---

## 4. Local Tooling Baseline

The implementation should assume the following local baseline:

- Node LTS via nvm, preferably `v24.11.1`.
- npm available.
- Watchman installed.
- CocoaPods installed.
- Expo CLI runnable through `npx expo`.

Current limitation:

- iOS Simulator requires full Xcode.
- Android Emulator requires Android Studio, JDK, and Android SDK tooling.

Until those are installed, the first usable test target is Expo Go on a physical iOS or Android device.

---

## 5. App Architecture

### 5.1 Runtime boundaries

```text
React Native app
  |
  | Supabase session + bearer token
  v
FastAPI gateway
  |
  +--> /search, /images, /images/async, /jobs
  |
  +--> Redis ingestion queue
  |
  +--> Workers: caption, embedding, storage
  |
  +--> pgvector/Qdrant + object storage
  |
  +--> Go search service when SEARCH_BACKEND=go
```

### 5.2 Client layering

```text
app/
  Route files and screen shells

src/api/
  Typed backend clients and error normalization

src/auth/
  Supabase client, AuthProvider, session hooks

src/features/
  Feature-specific hooks and state machines

src/components/
  Reusable UI components

src/storage/
  AsyncStorage-backed queues and preferences

src/utils/
  Small helpers for files, network, FormData, formatting
```

The route files should stay mostly orchestration-focused. API details, queue logic, retry behavior, and polling should live in `src/`.

---

## 6. Proposed File Structure

```text
apps/mobile/
  app/
    _layout.tsx
    index.tsx
    (auth)/
      sign-in.tsx
      sign-up.tsx
    (tabs)/
      _layout.tsx
      search.tsx
      upload.tsx
      library.tsx
      jobs.tsx
      settings.tsx
    image/
      [id].tsx
    job/
      [id].tsx
  src/
    api/
      client.ts
      auth.ts
      images.ts
      jobs.ts
      search.ts
      types.ts
    auth/
      supabase.ts
      AuthProvider.tsx
      useSession.ts
    components/
      AuthRequired.tsx
      EmptyState.tsx
      ErrorState.tsx
      ImageCard.tsx
      JobStatusCard.tsx
      RoutingBadge.tsx
      ScopeSelector.tsx
      SearchBar.tsx
      UploadPicker.tsx
    features/
      jobs/
        jobStore.ts
        useJobPolling.ts
        useRecentJobs.ts
      library/
        useImages.ts
      search/
        useSearchImages.ts
      upload/
        uploadQueue.ts
        useUploadImage.ts
        useUploadQueue.ts
    storage/
      asyncStorage.ts
      queueStore.ts
      settingsStore.ts
    theme/
      colors.ts
      spacing.ts
      typography.ts
    utils/
      fileName.ts
      formData.ts
      network.ts
      numbers.ts
  app.json
  babel.config.js
  eslint.config.js
  package.json
  tsconfig.json
  .env.example
  README.md
```

---

## 7. Navigation Design

### 7.1 Route model

Use Expo Router with tabs for primary flows:

- `/search`
- `/upload`
- `/library`
- `/jobs`
- `/settings`

Use stack routes for detail screens:

- `/image/[id]`
- `/job/[id]`
- `/sign-in`
- `/sign-up`

### 7.2 Anonymous access

Anonymous users can:

- Search public images.
- Open public image details.
- View settings.
- Sign in or sign up.

Anonymous users cannot:

- Upload.
- View private library.
- View job history.
- Search `mine` or `all`.
- Modify images.

For MVP, protected tab screens can show an in-screen auth-required state instead of redirecting. This is easier to demo and avoids navigation churn.

---

## 8. Screen Plans

### 8.1 Search

Purpose: Search public images anonymously or personal/public images when signed in.

Core behavior:

- Search input with submit action.
- Scope selector: `public`, `mine`, `all`.
- Anonymous users are pinned to `public`.
- Results render in a mobile-friendly grid or list.
- Result cards show thumbnail, caption, score, visibility, and caption origin.
- Tapping a card opens `/image/[id]`.
- Empty, loading, stale-cache, and error states are explicit.

Primary hooks:

- `useSearchImages(query, scope, k)`
- `useSession()`

### 8.2 Upload

Purpose: Pick or capture an image and submit it to async ingestion.

Core behavior:

- Request photo-library permission before selecting.
- Request camera permission before capture.
- Show selected image preview.
- Let user choose `private` or `public`.
- Disable submit while offline.
- Submit to `POST /images/async?priority=normal`.
- Add returned `job_id` to local recent jobs.
- Navigate to `/job/[id]` or show a queued state.
- On network/upload failure, store retry metadata.

Primary hooks:

- `useUploadImage()`
- `useUploadQueue()`
- `useNetworkState()`

### 8.3 Jobs

Purpose: Track recent async upload jobs.

Core behavior:

- Persist recent jobs locally.
- Poll active jobs while screen is focused and online.
- Show states: `queued`, `processing`, `completed`, `failed`, `retry_pending`.
- Completed jobs show caption and an Open Image action.
- Failed local uploads expose Retry.
- Polling pauses while offline.

Primary hooks:

- `useRecentJobs()`
- `useJobPolling(jobId)`

### 8.4 Library

Purpose: Browse the signed-in user's uploaded images.

Core behavior:

- Requires auth.
- Fetch images from `GET /images`.
- Visibility filter: all, private, public.
- Pull to refresh.
- Tapping opens `/image/[id]`.
- Empty state encourages upload.

Primary hooks:

- `useImages(visibility)`

### 8.5 Image Detail

Purpose: Inspect image and AI/search metadata.

Core behavior:

- Fetch `GET /images/{id}`.
- Render full image, caption, confidence, origin, visibility, created time, dimensions when available.
- Hide missing metadata rows instead of showing null-like values.
- Owner-only actions: change visibility and delete.
- Unauthorized/not found states are clear.

Primary hooks:

- `useImage(id)`
- `useUpdateImage(id)`
- `useDeleteImage(id)`

### 8.6 Settings

Purpose: Account and diagnostics.

Core behavior:

- Show signed-in email or sign-in actions.
- Logout clears private query cache and user-tied local queues.
- API base URL override for local device testing.
- Backend health check.
- Current network state.
- Clear cache/queue actions.
- App version display.

Primary hooks:

- `useSession()`
- `useHealthCheck()`
- `useSettingsStore()`

---

## 9. API Design

### 9.1 Environment variables

```bash
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
EXPO_PUBLIC_SUPABASE_URL=https://example.supabase.co
EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your-publishable-or-anon-key
```

The mobile app must not include service role keys, database URLs, provider API keys, or storage secrets.

### 9.2 API client responsibilities

`src/api/client.ts` should:

- Resolve the active API base URL from env or settings override.
- Attach `Authorization: Bearer <token>` when a token is available.
- Avoid attaching auth for anonymous public requests unless needed.
- Parse JSON responses.
- Normalize errors into a consistent app shape.
- Preserve HTTP status codes for auth and permission decisions.

Suggested normalized error:

```ts
export interface ApiErrorShape {
  status: number
  code: string
  message: string
  details?: unknown
}
```

### 9.3 Endpoints

| Function | Endpoint | Auth |
|---|---|---|
| Health | `GET /health` | No |
| Current user | `GET /auth/me` | Yes |
| Search | `GET /search?q=&k=&scope=` | Optional, depends on scope |
| List images | `GET /images?limit=&offset=&visibility=` | Yes for private/user library |
| Image detail | `GET /images/{id}` | Optional for public, required for private |
| Thumbnail | `GET /images/{id}/thumbnail` | Optional for public, required for private |
| Download | `GET /images/{id}/download` | Optional for public, required for private |
| Async upload | `POST /images/async?priority=normal` | Yes |
| Job status | `GET /jobs/{job_id}` | Yes |
| Update image | `PATCH /images/{id}` | Yes |
| Delete image | `DELETE /images/{id}` | Yes |

### 9.4 Multipart upload

React Native `FormData` should be built from the selected Expo asset:

```ts
const form = new FormData()

form.append('file', {
  uri: asset.uri,
  name: asset.fileName ?? `upload-${Date.now()}.jpg`,
  type: asset.mimeType ?? 'image/jpeg',
} as any)

form.append('visibility', visibility)
```

Do not manually set the multipart boundary.

---

## 10. Auth Design

### 10.1 Supabase client

`src/auth/supabase.ts` should:

- Use `createClient`.
- Use only publishable/anon mobile-safe config.
- Persist sessions with AsyncStorage.
- Enable auto refresh.
- Enable persisted session.
- Disable URL session detection for native.

### 10.2 AuthProvider

The provider should expose:

```ts
interface AuthContextValue {
  session: Session | null
  user: User | null
  accessToken: string | null
  isLoading: boolean
  signIn(email: string, password: string): Promise<void>
  signUp(email: string, password: string): Promise<void>
  signOut(): Promise<void>
}
```

On logout:

- Clear private TanStack Query cache entries.
- Clear user-tied upload queues and job history.
- Preserve public settings such as API base URL.

---

## 11. State Management

### 11.1 TanStack Query keys

```ts
['health']
['search', query, scope, k, userId ?? 'anonymous']
['image', imageId, userId ?? 'anonymous']
['images', visibility, userId]
['job', jobId, userId]
```

### 11.2 Local persisted state

Persist:

- Recent upload jobs.
- Retry-pending upload metadata.
- Recent searches.
- API base URL override.
- Debug preference.

Do not persist:

- Raw bearer tokens outside Supabase.
- Large image binaries.
- Backend or cloud secrets.

### 11.3 Upload queue state

```ts
interface LocalUploadQueueItem {
  localId: string
  assetUri: string
  fileName: string
  mimeType: string
  visibility: 'private' | 'public'
  createdAt: string
  status: 'retry_pending' | 'uploading' | 'queued' | 'failed'
  remoteJobId?: string
  error?: string
}
```

If the local URI becomes unavailable, the item should move to a failed state that asks the user to select the image again.

---

## 12. Offline and Retry Plan

The MVP is offline-aware, not fully offline-first.

Required behavior:

- Detect offline state globally.
- Disable new uploads while offline.
- Pause job polling while offline.
- Keep selected upload metadata as retry-pending when an upload fails due to network.
- Retry only when the user taps Retry.
- Allow search screens to show cached data as stale when offline.

Implementation notes:

- Use NetInfo for network state.
- Keep retry logic explicit and visible.
- Avoid background upload in MVP.
- Avoid storing image blobs in AsyncStorage.

---

## 13. UI Design Direction

The visual style should be mobile-product oriented rather than marketing-heavy:

- Dense enough to feel useful.
- Calm, high-contrast surfaces.
- Clear image-first cards.
- Badges for technical metadata.
- Minimal explanatory copy.
- Fast access to search, upload, jobs, and detail.

### 13.1 Metadata badges

Use compact badges for:

- `public`
- `private`
- `local caption`
- `cloud caption`
- `edge caption`
- `score 0.82`

### 13.2 Empty states

Empty states should be short and action-oriented:

- No query yet.
- No public results.
- No uploads yet.
- No jobs yet.
- Sign in required.
- Offline.

### 13.3 Error states

Handle:

- Backend unavailable.
- Unauthorized.
- Forbidden/private image.
- Upload too large.
- Permission denied.
- Job failed.
- Network offline.
- Expired session.

---

## 14. Backend Alignment Tasks

Before or during mobile implementation, verify these backend details:

1. `POST /images/async` accepts React Native multipart uploads.
2. `visibility` is included in the Redis async job payload.
3. Worker reads `visibility` from the job payload.
4. `GET /jobs/{job_id}` is auth-scoped to the job owner.
5. Completed job response includes enough detail to open the image.
6. Image detail responses include thumbnail/download URLs or enough information to derive them.
7. Error responses are mobile-friendly JSON.

Required patch from the spec:

```py
{
    "job_id": job_id,
    "image_b64": ...,
    "user_id": user.id,
    "priority": priority,
    "filename": file.filename,
    "content_type": file.content_type,
    "visibility": visibility,
    "text_hint": x_client_caption,
    "client_confidence": x_client_confidence,
    "submitted_at": time.time(),
}
```

---

## 15. Implementation Phases

### Phase 0: Backend and tooling readiness

Deliverables:

- Confirm Expo CLI can start locally.
- Confirm backend can run locally.
- Patch async upload visibility if missing.
- Document physical-device API base URL requirements.

Done when:

- `npx expo start` works once the app exists.
- Backend health endpoint is reachable from a phone or simulator.
- Async upload payload includes visibility.

### Phase 1: App bootstrap

Deliverables:

- Create `apps/mobile`.
- Add Expo + TypeScript.
- Add Expo Router.
- Add tab layout.
- Add TanStack Query provider.
- Add Supabase provider shell.
- Add `.env.example`.
- Add mobile README.

Done when:

- App starts.
- Tabs render.
- Settings can show API base URL and health state.

### Phase 2: Public search and image detail

Deliverables:

- Typed search client.
- Search screen with public scope.
- Result cards.
- Image detail screen.
- Loading, empty, and error states.

Done when:

- Anonymous user can search public images and open a public detail screen.

### Phase 3: Auth

Deliverables:

- Sign in screen.
- Sign up screen.
- Persistent Supabase session.
- Logout.
- Auth-required states.
- Authenticated search scopes.

Done when:

- User can sign in, restart app, remain signed in, search `mine`/`all`, and logout cleanly.

### Phase 4: Upload and jobs

Deliverables:

- Photo library picker.
- Camera capture.
- Visibility selector.
- Async upload client.
- Local job store.
- Job polling.
- Job detail screen.

Done when:

- User can select or capture an image, upload it, see job progress, and open completed image detail.

### Phase 5: Library and mutations

Deliverables:

- Library screen.
- Visibility filter.
- Pull to refresh.
- Update visibility.
- Delete image.

Done when:

- User can browse and manage their own images.

### Phase 6: Offline/retry polish

Deliverables:

- Network state provider.
- Retry-pending upload queue.
- Pause polling offline.
- Stale cached search indication.
- Clear queue/cache actions.

Done when:

- Offline and failed upload flows are understandable and recoverable.

### Phase 7: Portfolio polish

Deliverables:

- Root README mobile section.
- Mobile README setup instructions.
- Screenshots or demo GIF.
- Architecture diagram.
- Demo script.
- Manual QA checklist.

Done when:

- A reviewer can understand and run the mobile companion app without reading the full backend codebase.

---

## 16. Testing Plan

### 16.1 Unit tests

Cover:

- API URL construction.
- Auth header injection.
- Error normalization.
- Search scope rules.
- FormData asset normalization.
- Queue serialization.
- Job state transitions.

### 16.2 Component tests

Cover:

- Search empty/loading/error/results states.
- Upload permission-denied state.
- Upload selected-image preview.
- Job status card states.
- Auth-required state.
- Image metadata rows.

### 16.3 Manual smoke tests

Run:

1. Start backend.
2. Start Expo app.
3. Open on physical device or simulator.
4. Search public images.
5. Sign in.
6. Pick image.
7. Upload private image.
8. Watch job complete.
9. Open completed image detail.
10. Search `mine`.

### 16.4 Later E2E

Use Maestro for:

- Anonymous public search.
- Sign in.
- Upload start.
- Job status screen.
- Navigation to image detail.

Detox can wait until the app needs deeper native automation.

---

## 17. Device Testing Notes

### 17.1 Localhost differences

Mobile devices cannot use `localhost` to reach the Mac backend.

Use:

- Physical device: Mac LAN IP, for example `http://192.168.x.x:8000`.
- iOS Simulator: `http://localhost:8000`.
- Android Emulator: `http://10.0.2.2:8000`.

The Settings screen should make the API base URL easy to override.

### 17.2 Expo Go first

Use Expo Go for MVP validation because the initial dependency set stays within Expo-supported modules.

Move to a development build if:

- A custom native module becomes necessary.
- Expo Go limitations block a required library.
- Native build configuration needs to be tested.

---

## 18. Security Checklist

- No service-role Supabase key in mobile env files.
- No backend database URLs.
- No cloud provider API keys.
- No S3/R2/MinIO secret keys.
- Bearer tokens come only from Supabase session.
- Protected calls include auth headers.
- Logout clears private cached state.
- Private images are never shown from anonymous cache.
- API base URL override is treated as public configuration.

---

## 19. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| React Native multipart differs from browser upload | Upload fails on device | Test upload early with real device URI. |
| Async route drops visibility | Private/public toggle does not work | Patch backend payload before upload UI is considered done. |
| Device cannot reach local backend | App appears broken during demo | Add Settings base URL override and README LAN instructions. |
| Supabase token expires mid-request | Authenticated calls fail unexpectedly | Use Supabase auto-refresh and retry after refresh where practical. |
| Local asset URI expires | Retry cannot find file | Detect missing URI and ask user to reselect. |
| Scope rules leak private cached data | Security issue | Include `userId` in query keys and clear private cache on logout. |
| App scope grows too large | MVP stalls | Keep phases strict and defer non-MVP features. |

---

## 20. Acceptance Criteria

The mobile app is implementation-complete for the MVP when:

1. `apps/mobile` starts with `npx expo start`.
2. Anonymous users can search public images.
3. Anonymous users can open public image details.
4. Users can sign up and sign in with Supabase.
5. Sessions persist across app restart.
6. Users can select a photo from the library.
7. Users can take a photo with the camera.
8. Users can upload through `/images/async`.
9. Users can choose private or public visibility before upload.
10. Jobs show queued, processing, completed, and failed states.
11. Completed jobs can open image detail.
12. Users can search their own images.
13. Library shows user-owned images.
14. Offline upload attempts become understandable retry states.
15. Caption origin/confidence/score metadata is shown when present.
16. Logout clears private cached state.
17. Mobile README documents setup, env vars, and local-device backend URLs.
18. Root README links to the React Native companion app.

---

## 21. First Implementation Task

Start with a minimal app foundation:

```text
Create apps/mobile as an Expo + TypeScript + Expo Router app.

Implement:
- app shell and tabs
- Supabase AuthProvider
- TanStack Query provider
- API client shell
- Settings screen with API base URL and health check
- Search screen that can query public results

Do not implement upload until public search and auth plumbing are stable.
```

This gives a useful running app quickly and creates the architecture needed for upload, jobs, and offline retry.
