import { useEffect, useRef } from "react";
import maplibregl, { MapLibreEvent, StyleSpecification, VectorSourceSpecification } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import { Protocol } from "pmtiles";

import styleJson from "../styles/cyclosm-style.json";
import { useMapState } from "../context/MapStateContext";

const DEFAULT_PMTILES = import.meta.env.VITE_BASEMAP_PM as string | undefined;
const FALLBACK_PM = "http://localhost:8082/pmtiles/planet.z15.pmtiles";

function buildStyle(pmtilesUrl: string) {
  const style = JSON.parse(JSON.stringify(styleJson)) as StyleSpecification;
  const normalized = normalizePmtilesUrl(pmtilesUrl, window.location.href);

  const osmSource = style.sources?.osm as VectorSourceSpecification | undefined;
  if (osmSource) {
    osmSource.url = normalized ?? osmSource.url;
  }

  if (style.sprite) {
    style.sprite = resolveAssetUrl(style.sprite as string, window.location.origin);
  }

  if (style.glyphs) {
    style.glyphs = resolveAssetUrl(style.glyphs as string, window.location.origin);
  }

  return style;
}

function BasemapView() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const { focusLocation } = useMapState();

  useEffect(() => {
    if (import.meta.env.MODE === "test") {
      return undefined;
    }

    if (!containerRef.current) {
      return undefined;
    }

    const pmtilesUrl = DEFAULT_PMTILES || FALLBACK_PM;
    const protocol = new Protocol();
    maplibregl.addProtocol("pmtiles", protocol.tile);

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: buildStyle(pmtilesUrl),
      center: [-96, 38],
      zoom: 3,
      attributionControl: true,
    });

    const handleLoad = () => {
      console.log("Map loaded successfully");
      if (import.meta.env.DEV) {
        (window as unknown as Record<string, unknown>).__atmosMap = map;
      }
    };

    const handleError = (event: MapLibreEvent & { error?: unknown }) => {
      const detail = event.error ?? event;
      const plain =
        detail && typeof detail === "object"
          ? {
              ...(detail as Record<string, unknown>),
              name: (detail as { name?: unknown }).name,
              message: (detail as { message?: unknown }).message,
              status: (detail as { status?: unknown }).status,
              url: (detail as { url?: unknown }).url,
            }
          : detail;
      console.error("Map error event", plain);
      if (import.meta.env.DEV) {
        const globals = window as unknown as { __atmosMapErrors?: unknown[] };
        globals.__atmosMapErrors = [...(globals.__atmosMapErrors ?? []), plain];
      }
    };

    map.on("load", handleLoad);
    map.on("error", handleError);

    mapRef.current = map;

    return () => {
      map.off("load", handleLoad);
      map.off("error", handleError);
      maplibregl.removeProtocol("pmtiles");
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!mapRef.current || import.meta.env.MODE === "test") {
      return;
    }
    mapRef.current.flyTo({
      center: [focusLocation.lon, focusLocation.lat],
      essential: true,
      zoom: Math.max(mapRef.current.getZoom(), 4.5),
    });
  }, [focusLocation.lat, focusLocation.lon]);

  return <div className="basemap-view" ref={containerRef} />;
}

export default BasemapView;

function resolveAssetUrl(path: string, base: string) {
  if (!path) {
    return path;
  }
  if (/^[a-z]+:\/\//i.test(path)) {
    return path;
  }
  try {
    return new URL(path, base).toString();
  } catch {
    return path;
  }
}

function normalizePmtilesUrl(raw: string | undefined, base: string): string | undefined {
  if (!raw) {
    return undefined;
  }

  const trimmed = raw.trim();
  if (!trimmed) {
    return undefined;
  }

  if (trimmed.startsWith("pmtiles://")) {
    return trimmed;
  }

  if (trimmed.includes("://")) {
    return `pmtiles://${trimmed}`;
  }

  try {
    const absolute = new URL(trimmed, base).toString();
    return `pmtiles://${absolute}`;
  } catch {
    return undefined;
  }
}
