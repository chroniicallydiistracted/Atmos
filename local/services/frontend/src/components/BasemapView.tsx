import { useEffect, useRef } from "react";
import maplibregl, {
  MapLibreEvent,
  StyleSpecification,
  VectorSourceSpecification,
  RasterSourceSpecification,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import { Protocol } from "pmtiles";

import styleJson from "../styles/cyclosm-style.json";
import { useMapState } from "../context/MapStateContext";

const DEFAULT_PMTILES = import.meta.env.VITE_BASEMAP_PM as string | undefined;
const DEFAULT_BICYCLE_PM = import.meta.env.VITE_BASEMAP_BICYCLE_PM as string | undefined;
const DEFAULT_HILLSHADE_PM = import.meta.env.VITE_BASEMAP_HILLSHADE_PM as string | undefined;
const FALLBACK_PM = "http://localhost:8082/pmtiles/planet.z15.pmtiles";
const FALLBACK_BICYCLE_PM = "http://localhost:8082/pmtiles/cyclosm-bicycles.pmtiles";
const FALLBACK_HILLSHADE_PM = "http://localhost:8082/pmtiles/hillshade.pmtiles";

const BICYCLE_LAYER_IDS = [
  "bicycleroutes-lcn",
  "bicycleroutes-rcn",
  "bicycleroutes-ncn",
  "bicycleroutes-icn",
];

const BICYCLE_SOURCE_NAME = "cyclosm-bicycle";
const HILLSHADE_SOURCE_NAME = "cyclosm-hillshade";
const HILLSHADE_LAYER_ID = "cyclosm-hillshade";

type MutableLayer = NonNullable<StyleSpecification["layers"]>[number];

function buildStyle(pmtilesUrl: string, bicycleUrl: string, hillshadeUrl: string) {
  const style = JSON.parse(JSON.stringify(styleJson)) as StyleSpecification;
  const baseUrl = window.location.href;
  const normalizedBase = normalizeRequiredPmtilesUrl(pmtilesUrl, baseUrl, "base map");
  const normalizedBicycle = normalizeRequiredPmtilesUrl(bicycleUrl, baseUrl, "bicycle overlay");
  const normalizedHillshade = normalizeRequiredPmtilesUrl(hillshadeUrl, baseUrl, "hillshade overlay");

  style.sources = style.sources ?? {};

  const osmSource = style.sources.osm as VectorSourceSpecification | undefined;
  if (osmSource) {
    osmSource.url = normalizedBase;
  } else {
    style.sources.osm = {
      type: "vector",
      url: normalizedBase,
    } satisfies VectorSourceSpecification;
  }

  if (style.sprite) {
    style.sprite = resolveAssetUrl(style.sprite as string, window.location.origin);
  }

  if (style.glyphs) {
    style.glyphs = resolveAssetUrl(style.glyphs as string, window.location.origin);
  }

  applyBicycleOverlay(style, normalizedBicycle);
  applyHillshade(style, normalizedHillshade);

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
    const bicycleUrl = DEFAULT_BICYCLE_PM || FALLBACK_BICYCLE_PM;
    const hillshadeUrl = DEFAULT_HILLSHADE_PM || FALLBACK_HILLSHADE_PM;
    const protocol = new Protocol();
    maplibregl.addProtocol("pmtiles", protocol.tile);

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: buildStyle(pmtilesUrl, bicycleUrl, hillshadeUrl),
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

function applyBicycleOverlay(style: StyleSpecification, normalizedUrl: string) {
  style.sources = style.sources ?? {};
  style.sources[BICYCLE_SOURCE_NAME] = {
    type: "vector",
    url: normalizedUrl,
  } satisfies VectorSourceSpecification;

  if (style.layers) {
    style.layers = style.layers.map((layer) => {
      if (!layer || !BICYCLE_LAYER_IDS.includes(layer.id)) {
        return layer;
      }
      return {
        ...layer,
        source: BICYCLE_SOURCE_NAME,
        layout: layer.layout,
      } as MutableLayer;
    }) as MutableLayer[];
  }
}

function applyHillshade(style: StyleSpecification, normalizedUrl: string) {
  style.sources = style.sources ?? {};
  const layers: MutableLayer[] = [...(style.layers ?? [])] as MutableLayer[];
  const currentIndex = layers.findIndex((layer) => layer.id === HILLSHADE_LAYER_ID);

  style.sources[HILLSHADE_SOURCE_NAME] = {
    type: "raster",
    url: normalizedUrl,
    tileSize: 256,
    maxzoom: 15,
  } satisfies RasterSourceSpecification;

  if (currentIndex >= 0) {
    const layer = layers[currentIndex];
    layers[currentIndex] = {
      ...layer,
      source: HILLSHADE_SOURCE_NAME,
      layout: { ...(layer.layout ?? {}), visibility: "visible" },
    } as MutableLayer;
  } else {
    const backgroundIndex = layers.findIndex((layer) => layer.type === "background");
    const insertionIndex = backgroundIndex >= 0 ? backgroundIndex + 1 : 0;
    layers.splice(insertionIndex, 0, {
      id: HILLSHADE_LAYER_ID,
      type: "raster",
      source: HILLSHADE_SOURCE_NAME,
      paint: {
        "raster-opacity": 0.35,
        "raster-saturation": ["interpolate", ["exponential", 0.5], ["zoom"], 5, -0.2, 12, 0],
      },
      layout: { visibility: "visible" },
    } as MutableLayer);
  }

  style.layers = layers;
}

function normalizeRequiredPmtilesUrl(raw: string | undefined, base: string, label: string): string {
  const normalized = normalizePmtilesUrl(raw, base);
  if (!normalized) {
    throw new Error(`Basemap configuration missing ${label} PMTiles URL`);
  }
  return normalized;
}
