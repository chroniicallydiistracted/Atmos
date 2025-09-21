import { useCallback, useState } from "react";
import { apiPost, apiGet } from "../lib/http";
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
  const [framesFetchedAt, setFramesFetchedAt] = useState<string | null>(null);

  // Optional: fetch existing frames so we can show radar without forcing ingestion if already present.
  const fetchExistingFrames = useCallback(async () => {
    try {
      const resp = await apiGet<{ site: string; frames: any[] }>(`/v1/radar/nexrad/${site}/frames?limit=12`);
      const frames = resp.frames || [];
      if (frames.length > 0) {
        const latest = frames[frames.length - 1];
        const transformedDetail: NexradIngestionDetail = {
          cog_key: latest.cog_key || "",
            meta_key: latest.meta_key || "",
            actual_timestamp: latest.timestamp_key || "",
            timestamp_key: latest.timestamp_key || "",
            site: resp.site || site,
            requested_time: new Date().toISOString(),
            tile_template: latest.tile_template,
            meta_url: latest.meta_url
        };
        setDetail(transformedDetail);
      }
      setFramesFetchedAt(new Date().toISOString());
    } catch (e) {
      // Swallow 404 (no frames yet), raise others
      if (e instanceof Error && /404/.test(e.message)) return;
      console.warn("Failed to load existing radar frames", e);
    }
  }, [site]);

  const trigger = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Invoke multi-frame ingestion trigger via API proxy.
      const response = await apiPost<TriggerInvokeResponse>("/v1/trigger/nexrad-frames", {
        parameters: { site, frames: 6, lookback_minutes: 60 }
      });

      // Expected shape: { job: 'nexrad-frames', status: 'ok', detail: { site, added, total_frames, frames: [ { timestamp_key, cog_key, meta_key, tile_template? }, ... ] } }
      const detailObj: any = response.detail || {};
      const frames: any[] = Array.isArray(detailObj.frames) ? detailObj.frames : [];

      // Choose newest (last) frame if available.
      const latest = frames.length > 0 ? frames[frames.length - 1] : null;
      if (!latest) {
        throw new Error("Radar trigger succeeded but no frames available yet");
      }

      const transformedDetail: NexradIngestionDetail = {
        cog_key: latest.cog_key || "",
        meta_key: latest.meta_key || "",
        actual_timestamp: latest.timestamp_key || "", // we don't store separate actual vs key yet
        timestamp_key: latest.timestamp_key || "",
        site: detailObj.site || site,
        requested_time: new Date().toISOString(),
        tile_template: latest.tile_template,
        meta_url: latest.meta_url
      };

      setDetail(transformedDetail);
      return transformedDetail;
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      throw e;
    } finally {
      setLoading(false);
    }
  }, [site]);

  return { loading, error, detail, trigger, fetchExistingFrames, framesFetchedAt };
}

export type { NexradIngestionDetail };
