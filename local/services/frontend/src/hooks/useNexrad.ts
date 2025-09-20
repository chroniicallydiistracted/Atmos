import { useCallback, useState } from "react";
import { apiPost } from "../lib/http";
import { NexradIngestionDetail, TriggerInvokeResponse } from "../types/api";

interface UseNexradOptions {
  site?: string;
  auto?: boolean;
}

export function useNexrad(options: UseNexradOptions = {}) {
  const { site = (import.meta.env.VITE_NEXRAD_SITE as string) || "KTLX" } = options;
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<NexradIngestionDetail | null>(null);

  const trigger = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiPost<TriggerInvokeResponse>("/v1/trigger/nexrad", {
        parameters: { site }
      });
      const typed = response.detail as NexradIngestionDetail;
      setDetail(typed);
      return typed;
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      throw e;
    } finally {
      setLoading(false);
    }
  }, [site]);

  return { loading, error, detail, trigger };
}

export type { NexradIngestionDetail };
