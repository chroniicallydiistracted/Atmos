#!/usr/bin/env node
/*
 End-to-end NEXRAD validation script.
 Steps:
 1. Trigger ingestion via API proxy (/api/v1/trigger/nexrad)
 2. Extract site & timestamp_key
 3. Fetch legend endpoint (/api/v1/legend/nexrad/{site}/{timestamp_key})
 4. Probe a small set of tile coordinates (z=4 sample range) until one returns 200 or timeout
 5. Summarize pass/fail
*/

let fetchFn = globalThis.fetch;
if (!fetchFn) {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    fetchFn = require('node-fetch');
  } catch (e) {
    console.error('Fetch API not available and node-fetch not installed.');
    process.exit(1);
  }
}
const fetch = fetchFn;

const API_BASE = process.env.VALIDATION_API_BASE || 'http://localhost/api';
const TILE_BASE = process.env.VALIDATION_TILE_BASE || 'http://localhost/tiles';
const SITE = process.env.VALIDATION_SITE || 'KTLX';

function log(step, msg) {
  console.log(`[${step}] ${msg}`);
}

const LOOKBACK_MINUTES = Number(process.env.VALIDATION_LOOKBACK_MINUTES || '20');

function isoTimeLookback(minutes) {
  const d = new Date(Date.now() - minutes * 60000);
  return d.toISOString().replace(/\.\d{3}Z$/, 'Z');
}

async function trigger() {
  const targetIso = isoTimeLookback(LOOKBACK_MINUTES);
  const res = await fetch(`${API_BASE}/v1/trigger/nexrad`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ parameters: { site: SITE, timestamp: targetIso } })
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(`Trigger failed ${res.status}: ${JSON.stringify(body)}`);
  if (!body.detail?.timestamp_key) throw new Error('Missing timestamp_key in trigger response');
  return body.detail;
}

async function fetchLegend(site, tsKey) {
  const res = await fetch(`${API_BASE}/v1/legend/nexrad/${site}/${tsKey}`);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(`Legend failed ${res.status}`);
  if (!body.legend?.rescale) throw new Error('Legend missing rescale');
  return body;
}

// Sample candidate tiles (basic scatter around world) for z=4
const TILE_COORDS = [
  [4, 2, 5],
  [4, 5, 6],
  [4, 4, 6],
  [4, 7, 5]
];

async function probeTiles(site, tsKey, attempts = 12, delayMs = 2500) {
  const successes = [];
  for (let attempt = 1; attempt <= attempts; attempt++) {
    for (const [z, x, y] of TILE_COORDS) {
      const url = `${TILE_BASE}/weather/nexrad-${site}/${tsKey}/${z}/${x}/${y}.png`;
      try {
        const res = await fetch(url);
        if (res.ok && res.headers.get('content-type')?.includes('image/png')) {
          const size = Number(res.headers.get('content-length') || '0');
            successes.push({ url, size });
            if (successes.length >= 1) return successes; // minimal success criteria
        }
      } catch (_) { /* ignore */ }
    }
    await new Promise(r => setTimeout(r, delayMs));
  }
  return successes;
}

(async () => {
  try {
    log('INFO', `Triggering ingestion for site ${SITE}`);
    const detail = await trigger();
    const tsKey = detail.timestamp_key;
    const site = detail.site;
    log('INFO', `Ingestion returned timestamp_key=${tsKey}`);

    log('INFO', 'Fetching legend');
    const legend = await fetchLegend(site, tsKey);
    log('INFO', `Legend units=${legend.legend.units} rescale=${legend.legend.rescale}`);

    log('INFO', 'Probing tiles');
    const tiles = await probeTiles(site, tsKey);

    const passed = tiles.length > 0;
    console.log(JSON.stringify({
      status: passed ? 'PASS' : 'FAIL',
      site,
      timestamp_key: tsKey,
      legend: legend.legend,
      sample_tiles: tiles
    }, null, 2));

    if (!passed) process.exit(2);
  } catch (err) {
    console.error('VALIDATION_ERROR', err);
    process.exit(1);
  }
})();
