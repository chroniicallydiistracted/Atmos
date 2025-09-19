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
