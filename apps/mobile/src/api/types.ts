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
