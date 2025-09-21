import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../lib/http";
import type { HealthResponse } from "../types/api";

export function useHealthQuery() {
  return useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: () => apiGet<HealthResponse>("/v1/healthz"),
    retry: false
  });
}
