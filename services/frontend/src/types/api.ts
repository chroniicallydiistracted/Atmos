export interface HealthResponse {
  checks: Record<string, string>;
  ok: boolean;
  status?: string;
}

export interface TimelineResponse {
  layer: string;
  count: number;
  entries: string[];
}

export interface TriggerCatalogEntry {
  job: string;
  description?: string;
}

export interface TriggerCatalogResponse {
  jobs: TriggerCatalogEntry[];
}

export interface TriggerInvokeResponse {
  job: string;
  status: string;
  detail: unknown;
}

export interface NexradIngestionDetail {
  cog_key: string;
  meta_key: string;
  actual_timestamp: string;
  timestamp_key: string;
  site: string;
  requested_time: string;
  tile_template?: string; // /tiles/weather/nexrad-{site}/{timestamp}/{z}/{x}/{y}.png
  meta_url?: string;
}

export interface NexradLegendResponse {
  legend: {
    product: string;
    units: string;
    rescale: [number, number];
    palette: string;
    timestamp: string;
    site: string;
    extent_km: number;
    resolution_m: number;
  };
  raw: Record<string, unknown>;
}

