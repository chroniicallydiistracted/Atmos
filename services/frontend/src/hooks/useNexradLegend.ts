import { useState, useCallback } from "react";
import { apiGet } from "../lib/http";
import { NexradLegendResponse } from "../types/api";

export function useNexradLegend() {
  const [data, setData] = useState<NexradLegendResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLegend = useCallback(async (site: string, timestampKey: string) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await apiGet<NexradLegendResponse>(`/v1/legend/nexrad/${site}/${timestampKey}`);
      setData(resp);
      return resp;
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, fetchLegend };
}

export type { NexradLegendResponse };
