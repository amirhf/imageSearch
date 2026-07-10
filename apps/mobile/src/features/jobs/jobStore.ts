import AsyncStorage from '@react-native-async-storage/async-storage';

import type { JobStatus, JobStatusResult, UploadVisibility } from '@/api/types';

const RECENT_JOBS_KEY = 'image-search-mobile:recent-jobs:v1';
const MAX_RECENT_JOBS = 30;

export interface LocalJobRecord {
  localId: string;
  jobId?: string;
  status: JobStatus;
  assetUri?: string;
  fileName?: string;
  mimeType?: string;
  visibility: UploadVisibility;
  caption?: string;
  imageId?: string;
  thumbnailUrl?: string;
  downloadUrl?: string;
  error?: string;
  createdAt: string;
  updatedAt: string;
  pollUrl?: string;
}

type Listener = () => void;

const listeners = new Set<Listener>();

function notifyListeners() {
  listeners.forEach((listener) => listener());
}

function sortJobs(jobs: LocalJobRecord[]) {
  return [...jobs].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
  );
}

export function createLocalJobId() {
  return `local-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function subscribeRecentJobs(listener: Listener) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export async function getRecentJobs() {
  const rawJobs = await AsyncStorage.getItem(RECENT_JOBS_KEY);
  if (!rawJobs) {
    return [];
  }

  try {
    const jobs = JSON.parse(rawJobs);
    return Array.isArray(jobs) ? sortJobs(jobs as LocalJobRecord[]) : [];
  } catch {
    return [];
  }
}

async function saveRecentJobs(jobs: LocalJobRecord[]) {
  await AsyncStorage.setItem(
    RECENT_JOBS_KEY,
    JSON.stringify(sortJobs(jobs).slice(0, MAX_RECENT_JOBS)),
  );
  notifyListeners();
}

export async function upsertRecentJob(nextJob: LocalJobRecord) {
  const jobs = await getRecentJobs();
  const matchIndex = jobs.findIndex(
    (job) =>
      job.localId === nextJob.localId ||
      (job.jobId && nextJob.jobId && job.jobId === nextJob.jobId),
  );

  if (matchIndex >= 0) {
    jobs[matchIndex] = {
      ...jobs[matchIndex],
      ...nextJob,
      localId: jobs[matchIndex].localId,
      updatedAt: nextJob.updatedAt,
    };
  } else {
    jobs.unshift(nextJob);
  }

  await saveRecentJobs(jobs);
}

export async function patchRecentJob(localId: string, patch: Partial<LocalJobRecord>) {
  const jobs = await getRecentJobs();
  const match = jobs.find((job) => job.localId === localId || job.jobId === localId);

  if (!match) {
    return;
  }

  await upsertRecentJob({
    ...match,
    ...patch,
    updatedAt: patch.updatedAt ?? new Date().toISOString(),
  });
}

export async function updateJobFromRemote(
  localJob: LocalJobRecord,
  result: JobStatusResult | undefined,
  status: JobStatus,
) {
  const nextCaption = result?.caption ?? localJob.caption;
  const nextDownloadUrl = result?.download_url ?? localJob.downloadUrl;
  const nextImageId = result?.image_id ?? localJob.imageId;
  const nextThumbnailUrl = result?.thumbnail_url ?? localJob.thumbnailUrl;

  const hasChanges =
    localJob.caption !== nextCaption ||
    localJob.downloadUrl !== nextDownloadUrl ||
    localJob.error !== result?.error ||
    localJob.imageId !== nextImageId ||
    localJob.status !== status ||
    localJob.thumbnailUrl !== nextThumbnailUrl;

  if (!hasChanges) {
    return;
  }

  await patchRecentJob(localJob.localId, {
    caption: nextCaption,
    downloadUrl: nextDownloadUrl,
    error: result?.error,
    imageId: nextImageId,
    status,
    thumbnailUrl: nextThumbnailUrl,
  });
}

export async function clearRecentJobs() {
  await AsyncStorage.removeItem(RECENT_JOBS_KEY);
  notifyListeners();
}
