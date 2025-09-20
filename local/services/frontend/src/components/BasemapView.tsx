import { useEffect, useRef, useState } from "react";
import maplibregl, {
  MapLibreEvent,
  RasterSourceSpecification,
  StyleSpecification,
  VectorSourceSpecification,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import { Protocol } from "pmtiles";
import { useNexrad } from "../hooks/useNexrad";

import styleJson from "../styles/cyclosm-style.json";
import { useMapState } from "../context/MapStateContext";

const DEFAULT_PMTILES = import.meta.env.VITE_BASEMAP_PM as string | undefined;
const FALLBACK_PM = "http://localhost:8082/pmtiles/planet.z15.pmtiles";
const BICYCLE_PMTILES = import.meta.env.VITE_BICYCLE_PM as string | undefined;
const BICYCLE_FILENAME = "cyclosm-bicycle.pmtiles";
const FALLBACK_BICYCLE_PM = `http://localhost:8082/pmtiles/${BICYCLE_FILENAME}`;
const CYCLOSM_TILE_TEMPLATE = (import.meta.env.VITE_CYCLOSM_TILE_TEMPLATE as string | undefined)?.trim();
const RAW_CYCLOSM_SUBDOMAINS = (import.meta.env.VITE_CYCLOSM_TILE_SUBDOMAINS as string | undefined)?.trim();
const DEFAULT_CYCLOSM_SUBDOMAINS = RAW_CYCLOSM_SUBDOMAINS
  ? RAW_CYCLOSM_SUBDOMAINS.split(",").map((value) => value.trim()).filter(Boolean)
  : ["a", "b", "c"];

type BuildStyleOptions = {
  baseNormalized?: string;
  bicycleUrl?: string;
};

function BasemapView() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const { focusLocation } = useMapState();
  const { detail: nexradDetail, trigger: triggerNexrad, loading: radarLoading, error: radarError } = useNexrad();
  const [nexradVisible, setNexradVisible] = useState(false);
  const nexradSite = nexradDetail?.site || (import.meta.env.VITE_NEXRAD_SITE as string | undefined) || "KTLX";
  const nexradTimestamp = nexradDetail?.timestamp_key || (import.meta.env.VITE_NEXRAD_TIMESTAMP as string | undefined);

  useEffect(() => {
    if (import.meta.env.MODE === "test") {
      return undefined;
    }

    const container = containerRef.current;
    if (!container) {
      return undefined;
    }

    let disposed = false;
    let mapInstance: maplibregl.Map | null = null;
    let protocolAdded = false;
    let cleanupHandlers: (() => void) | undefined;

    (async () => {
      const usingHostedTiles = Boolean(CYCLOSM_TILE_TEMPLATE);
      let mapStyle: StyleSpecification;
      let protocol: Protocol | null = null;

      if (usingHostedTiles) {
        mapStyle = buildCyclosmRasterStyle(
          CYCLOSM_TILE_TEMPLATE!,
          DEFAULT_CYCLOSM_SUBDOMAINS,
        );
      } else {
        const pmtilesUrl = DEFAULT_PMTILES || FALLBACK_PM;
        const baseNormalized = normalizePmtilesUrl(pmtilesUrl, window.location.href);
        const baseHttp = extractHttpUrl(baseNormalized);
        const derivedBicycle = baseHttp ? siblingUrl(baseHttp, BICYCLE_FILENAME) : undefined;
        const bicycleCandidate = BICYCLE_PMTILES || derivedBicycle || FALLBACK_BICYCLE_PM;
        let bicycleNormalized = normalizePmtilesUrl(bicycleCandidate, window.location.href);

        if (bicycleNormalized) {
          const httpTarget = extractHttpUrl(bicycleNormalized);
          if (!httpTarget || !(await pmtilesExists(httpTarget))) {
            console.warn(
              "CyclOSM bicycle overlay not reachable; falling back to osm source",
              httpTarget,
            );
            bicycleNormalized = undefined;
          }
        }

        if (disposed) {
          return;
        }

        protocol = new Protocol();
        maplibregl.addProtocol("pmtiles", protocol.tile);
        protocolAdded = true;

        mapStyle = buildPmtilesStyle(pmtilesUrl, {
          baseNormalized,
          bicycleUrl: bicycleNormalized,
        });

        if (disposed) {
          if (protocolAdded) {
            maplibregl.removeProtocol("pmtiles");
            protocolAdded = false;
          }
          return;
        }
      }

      mapInstance = new maplibregl.Map({
        container,
        style: mapStyle,
        center: [-96, 38],
        zoom: 3,
        attributionControl: false,
      });

      const handleLoad = () => {
        console.log("Map loaded successfully");
        if (import.meta.env.DEV) {
          (window as unknown as Record<string, unknown>).__atmosMap = mapInstance;
        }

        // Layer is added lazily after user triggers or auto-loads radar.
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

      mapInstance.on("load", handleLoad);
      mapInstance.on("error", handleError);

      mapInstance.addControl(
        new maplibregl.AttributionControl({
          compact: false,
          customAttribution: [
            '<a href="https://www.openstreetmap.org/copyright" rel="noopener noreferrer" target="_blank">© OpenStreetMap contributors</a>',
            '<a href="https://github.com/cyclosm/cyclosm-cartocss-style" rel="noopener noreferrer" target="_blank">CyclOSM</a>',
          ],
        }),
      );

      cleanupHandlers = () => {
        mapInstance?.off("load", handleLoad);
        mapInstance?.off("error", handleError);
      };

      mapRef.current = mapInstance;
    })().catch((error) => {
      console.error("Failed to initialise basemap", error);
    });

    return () => {
      disposed = true;
      cleanupHandlers?.();
      if (mapInstance) {
        mapInstance.remove();
        mapInstance = null;
        mapRef.current = null;
      }
      if (protocolAdded) {
        maplibregl.removeProtocol("pmtiles");
        protocolAdded = false;
      }
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

  // Side effect: when we have new NEXRAD detail and visibility is on, add/update source.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !nexradDetail || !nexradTimestamp) return;
    const sourceId = `nexrad-${nexradSite}`;
    const layerId = `${sourceId}-layer`;
    const baseTile = (import.meta.env.VITE_TILE_BASE || "http://localhost:8083").replace(/\/$/, "");
    const template = nexradDetail.tile_template
      ? `${baseTile}${nexradDetail.tile_template}`
      : `${baseTile}/tiles/weather/nexrad-${nexradSite}/${nexradTimestamp}/{z}/{x}/{y}.png`;

    if (nexradVisible) {
      if (!map.getSource(sourceId)) {
        map.addSource(sourceId, {
          type: "raster",
          tiles: [template],
          tileSize: 256,
          attribution: "NOAA / NEXRAD"
        });
      }
      if (!map.getLayer(layerId)) {
        map.addLayer({
          id: layerId,
          type: "raster",
          source: sourceId,
          paint: { "raster-opacity": 0.75 }
        });
      }
    } else {
      if (map.getLayer(layerId)) map.removeLayer(layerId);
      if (map.getSource(sourceId)) map.removeSource(sourceId);
    }
  }, [nexradDetail, nexradSite, nexradTimestamp, nexradVisible]);

  const handleToggleRadar = async () => {
    if (!nexradVisible) {
      // Need data first
      if (!nexradDetail) {
        try {
          await triggerNexrad();
        } catch {
          return;
        }
      }
      setNexradVisible(true);
    } else {
      setNexradVisible(false);
    }
  };

  return (
    <div className="basemap-view" ref={containerRef}>
      <div style={{ position: "absolute", top: 8, right: 8, zIndex: 10, display: "flex", gap: 8 }}>
        <button onClick={handleToggleRadar} disabled={radarLoading} style={{ padding: "4px 8px" }}>
          {nexradVisible ? "Hide Radar" : radarLoading ? "Loading…" : "Show Radar"}
        </button>
        {radarError && (
          <span style={{ background: "#300", color: "#fdd", padding: "2px 4px", fontSize: 12 }}>
            {radarError}
          </span>
        )}
      </div>
    </div>
  );
}

export default BasemapView;

type SourceLike = VectorSourceSpecification | RasterSourceSpecification | undefined;

function buildPmtilesStyle(pmtilesUrl: string, options: BuildStyleOptions = {}): StyleSpecification {
  const style = JSON.parse(JSON.stringify(styleJson)) as StyleSpecification;
  const baseNormalized = options.baseNormalized ?? normalizePmtilesUrl(pmtilesUrl, window.location.href);
  const baseHttp = extractHttpUrl(baseNormalized);
  const baseDir = baseHttp ? baseHttp.replace(/[^/]+$/, "") : undefined;

  const sources = style.sources ?? {};
  const osmSource = sources.osm as VectorSourceSpecification | undefined;
  if (osmSource && baseNormalized) {
    osmSource.url = baseNormalized;
  }

  for (const [name, source] of Object.entries(sources)) {
    const typed = source as SourceLike;
    if (!typed || typeof typed !== "object") {
      continue;
    }

    if (name === "osm") {
      continue;
    }

    if (name === "cyclosm-bicycle") {
      if (options.bicycleUrl) {
        typed.url = options.bicycleUrl;
      } else {
        delete (style.sources as Record<string, unknown>)[name];
      }
      continue;
    }

    const url = typed.url;
    if (typeof url === "string" && url.startsWith("pmtiles://./") && baseDir) {
      const relativePath = url.slice("pmtiles://./".length);
      try {
        const absolute = new URL(relativePath, baseDir).toString();
        typed.url = `pmtiles://${absolute}`;
      } catch {
        // Leave source URL untouched if it cannot be resolved.
      }
    }
  }

  if (!options.bicycleUrl) {
    for (const layer of style.layers ?? []) {
      if ("source" in layer && (layer as { source?: string }).source === "cyclosm-bicycle") {
        (layer as { source?: string }).source = "osm";
      }
    }
  }

  if (style.sprite) {
    style.sprite = resolveAssetUrl(style.sprite as string, window.location.origin);
  }

  if (style.glyphs) {
    style.glyphs = resolveAssetUrl(style.glyphs as string, window.location.origin);
  }

  return style;
}

function buildCyclosmRasterStyle(
  template: string,
  subdomains: string[],
): StyleSpecification {
  const tileUrls = expandCyclosmTemplate(template, subdomains);

  return {
    version: 8,
    name: "CyclOSM",
    metadata: {},
    sources: {
      cyclosm: {
        type: "raster",
        tiles: tileUrls,
        tileSize: 256,
        attribution:
          "© <a href=\"https://www.openstreetmap.org/copyright\" target=\"_blank\" rel=\"noopener noreferrer\">OpenStreetMap contributors</a> · <a href=\"https://github.com/cyclosm/cyclosm-cartocss-style\" target=\"_blank\" rel=\"noopener noreferrer\">CyclOSM</a>",
      },
    },
    glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
    layers: [
      {
        id: "cyclosm-base",
        type: "raster",
        source: "cyclosm",
      },
    ],
  } satisfies StyleSpecification;
}

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

function extractHttpUrl(pmtilesUrl: string | undefined): string | undefined {
  if (!pmtilesUrl || !pmtilesUrl.startsWith("pmtiles://")) {
    return undefined;
  }
  return pmtilesUrl.slice("pmtiles://".length);
}

function siblingUrl(baseUrl: string, filename: string): string | undefined {
  try {
    const url = new URL(baseUrl);
    const parts = url.pathname.split("/");
    if (parts.length === 0) {
      return undefined;
    }
    parts[parts.length - 1] = filename;
    url.pathname = parts.join("/");
    return url.toString();
  } catch {
    return undefined;
  }
}

async function pmtilesExists(url: string): Promise<boolean> {
  try {
    const response = await fetch(url, { method: "HEAD" });
    if (response.ok) {
      return true;
    }
    if (response.status === 405) {
      const rangeResponse = await fetch(url, {
        headers: { Range: "bytes=0-0" },
      });
      return rangeResponse.ok;
    }
    return false;
  } catch (error) {
    console.warn("Failed to reach PMTiles archive", url, error);
    return false;
  }
}

function expandCyclosmTemplate(template: string, subdomains: string[]): string[] {
  if (!template.includes("{s}")) {
    return [template];
  }
  if (subdomains.length === 0) {
    return [template.replace("{s}", "a")];
  }
  return subdomains.map((sub) => template.replace("{s}", sub));
}
