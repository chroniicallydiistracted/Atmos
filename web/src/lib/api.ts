// API client with retries and error handling

const API_BASE = import.meta.env.VITE_API_BASE || 'https://weather.westfam.media';

interface ApiOptions {
  timeout?: number;
  retries?: number;
  retryDelay?: number;
}

const defaultOptions: Required<ApiOptions> = {
  timeout: 10000,
  retries: 2,
  retryDelay: 1000
};

class ApiError extends Error {
  constructor(public status: number, message: string, public response?: Response) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchWithTimeout(url: string, options: RequestInit, timeout: number): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
}

async function apiCall<T>(endpoint: string, options: RequestInit & ApiOptions = {}): Promise<T> {
  const { timeout, retries, retryDelay, ...fetchOptions } = { ...defaultOptions, ...options };
  const url = `${API_BASE}${endpoint}`;
  
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetchWithTimeout(url, fetchOptions, timeout);
      
      if (!response.ok) {
        throw new ApiError(response.status, `HTTP ${response.status}: ${response.statusText}`, response);
      }
      
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return await response.text() as T;
      }
    } catch (error) {
      lastError = error as Error;
      
      // Don't retry on 4xx errors (client errors)
      if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
        break;
      }
      
      // Don't retry on the last attempt
      if (attempt === retries) {
        break;
      }
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, retryDelay * Math.pow(2, attempt)));
    }
  }
  
  throw lastError;
}

// API endpoints
export interface TimelineResponse {
  timestamps: string[];
  latest: string;
  cadence_minutes: number;
}

export interface MetadataResponse {
  units: string;
  legend: string;
  timestamp: string;
  provenance: string;
  update_cadence: string;
  caveats?: string[];
}

export interface HealthResponse {
  ok: boolean;
  version: string;
  timestamp: string;
  probes: {
    s3_read: boolean;
    s3_write: boolean;
    tiler_latency_ms: number;
    indices: Record<string, {
      newest_age_s: number;
      ok: boolean;
    }>;
  };
}

export interface AlertDetail {
  id: string;
  headline: string;
  description: string;
  instruction: string;
  event: string;
  severity: string;
  urgency: string;
  certainty: string;
  status: string;
  sent: string;
  ends: string | null;
  areas: string[];
}

// API methods
export const api = {
  // Health check
  health: (): Promise<HealthResponse> => 
    apiCall('/healthz'),
  
  // GOES timeline
  goesTimeline: (band: number = 13, sector: string = 'CONUS', limit: number = 12): Promise<TimelineResponse> =>
    apiCall(`/goes/timeline?band=${band}&sector=${sector}&limit=${limit}`),
  
  // MRMS/Radar mosaic timeline  
  mosaicTimeline: (product: string = 'reflq', limit: number = 12): Promise<TimelineResponse> =>
    apiCall(`/mosaic/timeline?product=${product}&limit=${limit}`),
  
  // Alerts latest timestamp
  alertsLatest: (): Promise<{ latest: string; history: string[] }> =>
    apiCall('/indices/alerts/index.json'),
  
  // Alert details
  alertDetail: (id: string): Promise<AlertDetail> =>
    apiCall(`/alerts/detail/${id}`),
  
  // Metadata endpoints
  radarMeta: (site: string, time: string): Promise<MetadataResponse> =>
    apiCall(`/radar/meta/${site}/${time}.json`),
  
  goesMeta: (band: number, sector: string, time: string): Promise<MetadataResponse> =>
    apiCall(`/goes/meta/${band}/${sector}/${time}.json`),
  
  // Prepare endpoints (trigger data processing)
  prepareRadar: (site: string, time: string): Promise<{ status: string; message: string }> =>
    apiCall(`/radar/prepare?site=${site}&time=${time}`, { method: 'POST' }),
  
  prepareGoes: (band: number, sector: string, time: string = 'latest'): Promise<{ status: string; message: string }> =>
    apiCall(`/goes/prepare?band=${band}&sector=${sector}&time=${time}`, { method: 'POST' }),
  
  prepareMosaic: (product: string = 'reflq', time: string = 'latest'): Promise<{ status: string; message: string }> =>
    apiCall(`/mosaic/prepare?product=${product}&time=${time}`, { method: 'POST' })
};