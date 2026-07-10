export interface ApiErrorShape {
  status: number;
  code: string;
  message: string;
  details?: unknown;
}

export interface HealthResponse {
  status?: string;
  ok?: boolean;
  version?: string;
  service?: string;
  [key: string]: unknown;
}

export interface BackendAuthUser {
  id: string;
  email: string;
  role?: string;
}

export interface AuthMeResponse {
  authenticated: boolean;
  user: BackendAuthUser | null;
}

export type SearchScope = 'public' | 'mine' | 'all';

export type ImageVisibility = 'private' | 'public' | 'public_admin';

export type UploadVisibility = 'private' | 'public';

export type CaptionOrigin = 'edge' | 'cache' | 'local' | 'cloud' | string;

export type JobStatus = 'uploading' | 'queued' | 'processing' | 'completed' | 'failed' | 'retry_pending';

export interface UploadJobResponse {
  job_id: string;
  status: 'queued';
  poll_url: string;
}

export interface JobStatusResult {
  image_id?: string;
  caption?: string;
  error?: string;
  visibility?: ImageVisibility;
  download_url?: string;
  thumbnail_url?: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: Extract<JobStatus, 'queued' | 'processing' | 'completed' | 'failed'>;
  result?: JobStatusResult;
  submitted_at?: number;
  visibility?: ImageVisibility;
}

export interface SearchResult {
  id: string;
  score: number;
  vec_score?: number;
  text_score?: number;
  caption?: string;
  caption_confidence?: number;
  confidence?: number;
  caption_origin?: CaptionOrigin;
  origin?: CaptionOrigin;
  visibility?: ImageVisibility;
  download_url?: string;
  thumbnail_url?: string;
  created_at?: string;
  width?: number;
  height?: number;
  format?: string;
  size_bytes?: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
}

export interface ImageDetail {
  id: string;
  caption?: string;
  caption_confidence?: number;
  confidence?: number;
  caption_origin?: CaptionOrigin;
  origin?: CaptionOrigin;
  visibility?: ImageVisibility;
  download_url?: string;
  thumbnail_url?: string;
  width?: number;
  height?: number;
  format?: string;
  size_bytes?: number;
  created_at?: string;
  updated_at?: string;
  owner_user_id?: string | null;
  payload?: Record<string, unknown>;
  score?: number;
  vec_score?: number;
  text_score?: number;
  [key: string]: unknown;
}
