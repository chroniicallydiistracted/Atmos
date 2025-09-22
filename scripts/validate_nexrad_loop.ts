#!/usr/bin/env ts-node
/**
 * Validation script for NEXRAD radar loop endpoint.
 *
 * Responsibilities:
 * 1. Optionally trigger ingestion for a site (if --trigger provided)
 * 2. Fetch frames index from API `/api/radar/nexrad/{site}/frames` (adjust path if different)
 * 3. Validate tile templates are reachable (HTTP 200) for one zoom/x/y sample
 * 4. Emit summary JSON with frame count and sample tile status
 */

// Uses native fetch (Node 18+). No external fetch dependency required.
import { URL } from 'url';

interface FrameMeta {
  timestamp_key: string;
  tile_template: string;
}

interface Options {
  site: string;
  apiBase: string;
  trigger: boolean;
  zoom: number;
  x: number;
  y: number;
}

function parseArgs(): Options {
  const args = process.argv.slice(2);
  const opts: Options = { site: 'KTLX', apiBase: 'http://localhost:8081', trigger: false, zoom: 2, x: 1, y: 1 };
  const expectValue = (flag: string, idx: number) => {
    if (idx >= args.length) throw new Error(`Missing value for ${flag}`);
    return args[idx];
  };
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    switch (a) {
      case '--site':
        opts.site = expectValue(a, ++i);
        break;
      case '--api':
        opts.apiBase = expectValue(a, ++i);
        break;
      case '--trigger':
        opts.trigger = true;
        break;
      case '--z':
        opts.zoom = parseInt(expectValue(a, ++i), 10);
        break;
      case '--x':
        opts.x = parseInt(expectValue(a, ++i), 10);
        break;
      case '--y':
        opts.y = parseInt(expectValue(a, ++i), 10);
        break;
      case '--help':
      case '-h':
        printHelp();
        process.exit(0);
      default:
        throw new Error(`Unknown argument: ${a}`);
    }
  }
  return opts;
}

function printHelp() {
  console.log(`NEXRAD Loop Validation

Usage: validate_nexrad_loop.ts [options]

Options:
  --site <ID>        NEXRAD site (default KTLX)
  --api <URL>        API base (default http://localhost:8081)
  --trigger          Trigger ingestion before validation
  --z <ZOOM>         Tile zoom (default 2)
  --x <X>            Tile x coordinate (default 1)
  --y <Y>            Tile y coordinate (default 1)
  -h, --help         Show help
`);
}

async function triggerIngestion(opts: Options) {
  const url = `${opts.apiBase}/api/radar/nexrad/${opts.site}/ingest`;
  try {
    const res = await fetch(url, { method: 'POST' });
    if (!res.ok) throw new Error(`Trigger failed: ${res.status}`);
    return await res.json();
  } catch (e) {
    console.error('Ingestion trigger error:', e);
  }
}

async function fetchFrames(opts: Options): Promise<FrameMeta[]> {
  const url = `${opts.apiBase}/api/radar/nexrad/${opts.site}/frames`;
  const res = await fetch(url, { method: 'GET' });
  if (!res.ok) throw new Error(`Frames fetch failed: ${res.status} ${res.statusText}`);
  const data: any = await res.json();
  if (!Array.isArray(data.frames)) return [];
  return data.frames.filter((f: any): f is FrameMeta => typeof f?.timestamp_key === 'string' && typeof f?.tile_template === 'string');
}

async function checkTile(apiBase: string, template: string, z: number, x: number, y: number): Promise<number> {
  // template should contain {z}/{x}/{y}
  if (!template.includes('{z}') || !template.includes('{x}') || !template.includes('{y}')) return 0;
  const path = template.replace('{z}', String(z)).replace('{x}', String(x)).replace('{y}', String(y));
  const url = new URL(path, apiBase).toString();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);
  try {
    const res = await fetch(url, { signal: controller.signal });
    return res.status;
  } catch (e) {
    return 0;
  } finally {
    clearTimeout(timeout);
  }
}

async function main() {
  const opts = parseArgs();
  if (opts.trigger) {
    console.log('Triggering ingestion...');
    await triggerIngestion(opts);
    // brief wait to allow processing
    await new Promise(r => setTimeout(r, 4000));
  }
  const frames = await fetchFrames(opts);
  if (!frames.length) {
    console.error('No frames returned');
    process.exit(2);
  }
  const latest = frames[frames.length - 1];
  const status = await checkTile(opts.apiBase, latest.tile_template, opts.zoom, opts.x, opts.y);
  const summary = {
    site: opts.site,
    frameCount: frames.length,
    latest: latest.timestamp_key,
    sampleTileStatus: status,
    ok: status === 200,
  };
  console.log(JSON.stringify(summary, null, 2));
  if (!summary.ok) process.exit(1);
}

main().catch(e => {
  console.error(e);
  process.exit(1);
});
