/** errors.ts — parse the platform's standard error envelope */

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    details: unknown[];
  };
  request_id: string;
}

export class ApiError extends Error {
  code: string;
  requestId: string;
  details: unknown[];
  statusCode: number;

  constructor(envelope: ApiErrorEnvelope, statusCode: number) {
    super(envelope.error.message);
    this.code = envelope.error.code;
    this.requestId = envelope.request_id;
    this.details = envelope.error.details ?? [];
    this.statusCode = statusCode;
    this.name = 'ApiError';
  }
}

/** Extracts a user-friendly message from an axios error */
export function parseApiError(err: unknown): string {
  if (err && typeof err === 'object' && 'response' in err) {
    const res = (err as { response?: { data?: ApiErrorEnvelope; status?: number } }).response;
    if (res?.data?.error?.message) return res.data.error.message;
    if (res?.status === 429) return 'Too many attempts. Please wait a moment.';
    if (res?.status === 503) return 'Service temporarily unavailable.';
  }
  return 'An unexpected error occurred. Please try again.';
}
