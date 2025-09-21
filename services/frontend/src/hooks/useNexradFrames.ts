import { useCallback, useEffect, useRef, useState } from "react";
import { apiPost, apiGet } from "../lib/http";

interface FrameEntry {
  timestamp_key: string;
  tile_template: string;
  cog_key?: string;
  meta_key?: string;
}

interface FramesResponse {
  site: string;
  frames: FrameEntry[];
}

interface UseNexradFramesOptions {
  site?: string;
  desired?: number;       // how many new frames to attempt per trigger
  lookbackMinutes?: number;
  pollMs?: number;        // how often to poll frames.json
  auto?: boolean;         // auto trigger ingestion on mount
}

export function useNexradFrames(options: UseNexradFramesOptions = {}) {
  const {
    site = (import.meta as any).env?.VITE_NEXRAD_SITE || "KTLX",
    desired = 4,
    lookbackMinutes = 60,
    pollMs = 30_000,
    auto = true
  } = options;

  const [frames, setFrames] = useState<FrameEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<number | null>(null);
  const pollRef = useRef<number | null>(null);

  const fetchFrames = useCallback(async () => {
    try {
      const data = await apiGet<FramesResponse>(`/v1/radar/nexrad/${site}/frames`);
      setFrames(data.frames);
      setLastUpdate(Date.now());
    } catch (e) {
      // silent while no frames yet
    }
  }, [site]);

  const trigger = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await apiPost(`/v1/trigger/nexrad-frames`, {
        parameters: { site, frames: desired, lookback_minutes: lookbackMinutes }
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [site, desired, lookbackMinutes]);

  const refresh = useCallback(async () => {
    await fetchFrames();
  }, [fetchFrames]);

  useEffect(() => {
    if (auto) {
      void trigger().then(fetchFrames);
    } else {
      void fetchFrames();
    }
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [trigger, fetchFrames, auto]);

  useEffect(() => {
    if (pollRef.current) window.clearInterval(pollRef.current);
    pollRef.current = window.setInterval(() => {
      void fetchFrames();
    }, pollMs);
  }, [fetchFrames, pollMs]);

  return { site, frames, loading, error, lastUpdate, trigger, refresh };
}

export type { FrameEntry };
