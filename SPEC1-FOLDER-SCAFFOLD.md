# AtmosInsight — Folder Scaffold (MVP)

Below is a pragmatic monorepo skeleton you can clone into. It reflects everything we locked in the SPEC: S3+CloudFront static, PMTiles basemap, TiTiler on Lambda, and four tiny Lambda jobs.

```text
atmosinsight/
├─ README.md
├─ .editorconfig
├─ .gitignore
├─ .nvmrc                       # node 20
├─ .python-version               # 3.11
├─ package.json                  # root scripts (lint, format)
├─ scripts/
│  ├─ pmtiles/
│  │  └─ convert.sh             # planet.mbtiles → planet.z15.pmtiles
│  └─ deploy/
│     └─ cf-invalidate.sh       # invalidate CloudFront paths
├─ infra/
│  └─ terraform/
│     ├─ main.tf                # providers + minimal stacks
│     ├─ outputs.tf
│     ├─ variables.tf
│     ├─ env/
│     │  └─ us-east-1.tfvars
│     └─ modules/
│        ├─ static_site/        # S3 static + OAC + CloudFront + ACM + Route53 alias
│        ├─ api_gw_lambda/      # API Gateway + Lambda (http api)
│        ├─ events/             # EventBridge schedules
│        └─ dynamo/             # tiny table for indices (optional)
├─ web/                          # Vite + React + MapLibre frontend
│  ├─ index.html
│  ├─ package.json
│  ├─ tsconfig.json
│  ├─ vite.config.ts
│  ├─ .env.sample               # VITE_API_BASE, VITE_TILE_BASE, VITE_STYLE_URL
│  └─ src/
│     ├─ main.tsx
│     ├─ App.tsx
│     ├─ lib/
│     │  ├─ time.ts            # unit conversions, slider helpers
│     │  └─ api.ts             # fetch helpers with retries
│     ├─ components/
│     │  ├─ MapView.tsx        # MapLibre init + layers
│     │  ├─ LayerToggle.tsx
│     │  ├─ Legend.tsx
│     │  └─ TimeSlider.tsx
│     └─ styles/
│        └─ global.css
├─ web-static/                   # assets served from S3 (same CF origin as SPA)
│  ├─ styles/cyclosm.json
│  ├─ sprites/cyclosm/*         # cyclosm.png/json + @2x
│  ├─ fonts/**                  # SDF glyphs
│  └─ basemaps/
│     └─ planet.z15.pmtiles     # uploaded artifact
├─ services/                     # all Lambda functions (container image-ready)
│  ├─ tiler/                     # TiTiler (as Lambda container)
│  │  ├─ Dockerfile
│  │  └─ README.md
│  ├─ radar-prepare/
│  │  ├─ Dockerfile
│  │  ├─ handler.py
│  │  ├─ requirements.txt
│  │  └─ README.md
│  ├─ goes-prepare/
│  │  ├─ Dockerfile
│  │  ├─ handler.py
│  │  ├─ requirements.txt
│  │  └─ README.md
│  ├─ mrms-prepare/
│  │  ├─ Dockerfile
│  │  ├─ handler.py
│  │  ├─ requirements.txt
│  │  └─ README.md
│  ├─ alerts-bake/
│  │  ├─ Dockerfile
│  │  ├─ handler.py
│  │  ├─ requirements.txt
│  │  └─ README.md
│  └─ healthz/
│     ├─ handler.py
│     └─ requirements.txt
└─ ops/
   └─ github-actions/
      └─ deploy.yml             # optional CI (build containers, terraform apply)
```

---

## Minimal file contents

> These are skeletal, meant to compile and give you a first render quickly. Replace TODOs when you wire real logic.

### Root `package.json`
```json
{
  "name": "atmosinsight",
  "private": true,
  "workspaces": ["web"],
  "scripts": {
    "fmt": "prettier -w .",
    "lint": "eslint web/src --ext .ts,.tsx",
    "dev": "npm --workspace web run dev",
    "build": "npm --workspace web run build",
    "preview": "npm --workspace web run preview"
  },
  "devDependencies": {
    "eslint": "^9.9.0",
    "prettier": "^3.3.3"
  }
}
```

### `scripts/pmtiles/convert.sh`
```bash
#!/usr/bin/env bash
set -euo pipefail
MBTILES=${1:-planet.mbtiles}
OUT=${2:-planet.z15.pmtiles}
command -v pmtiles >/dev/null 2>&1 || { echo "Install pmtiles: https://github.com/protomaps/PMTiles"; exit 1; }
pmtiles convert "$MBTILES" "$OUT"
echo "Wrote $OUT"
```

### `infra/terraform/main.tf` (skeleton)
```hcl
terraform {
  required_version = ">= 1.5"
  required_providers { aws = { source = "hashicorp/aws", version = ">= 5.0" } }
}
provider "aws" { region = var.region }

# Modules (fill in actual module code later)
module "static_site" {
  source                 = "./modules/static_site"
  domain_name            = var.domain_name            # weather.westfam.media
  create_route53_zone    = true                       # delegated subdomain
}

module "api" {
  source = "./modules/api_gw_lambda"
  # expose /tiles, /prepare, /healthz, etc.
}

module "events" {
  source = "./modules/events"
  # schedules for MRMS + Alerts
}

variable "region" { type = string default = "us-east-1" }
variable "domain_name" { type = string }
```

### `web/.env.sample`
```env
VITE_API_BASE=https://weather.westfam.media
VITE_TILE_BASE=https://weather.westfam.media
VITE_STYLE_URL=https://weather.westfam.media/styles/cyclosm.json
```

### `web/package.json`
```json
{
  "name": "ai-web",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview --port 4173"
  },
  "dependencies": {
    "maplibre-gl": "^4.7.1",
    "pmtiles": "^3.0.6",
    "zustand": "^4.5.2",
    "clsx": "^2.1.1"
  },
  "devDependencies": {
    "vite": "^5.4.0",
    "typescript": "^5.5.4",
    "@types/node": "^20.14.9"
  }
}
```

### `web/index.html`
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AtmosInsight</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

### `web/src/main.tsx`
```ts
import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles/global.css'

createRoot(document.getElementById('root')!).render(<App />)
```

### `web/src/App.tsx`
```tsx
import React from 'react'
import MapView from './components/MapView'

export default function App() {
  return (
    <div style={{ height: '100vh', width: '100vw' }}>
      <MapView />
    </div>
  )
}
```

### `web/src/components/MapView.tsx`
```tsx
import React, { useEffect, useRef } from 'react'
import maplibregl, { Map } from 'maplibre-gl'
import { PMTiles } from 'pmtiles'

const styleUrl = import.meta.env.VITE_STYLE_URL

export default function MapView() {
  const mapRef = useRef<Map | null>(null)
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    // PMTiles protocol for CyclOSM basemap
    const protocol = new PMTiles('pmtiles')
    (maplibregl as any).addProtocol('pmtiles', protocol.tile)

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: styleUrl,
      center: [-98.5, 39.5],
      zoom: 4,
      hash: true,
      attributionControl: true
    })

    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right')
    mapRef.current = map

    return () => {
      protocol.remove()
      map.remove()
    }
  }, [])

  return <div ref={containerRef} style={{ height: '100%', width: '100%' }} />
}
```

### `web/src/lib/time.ts`
```ts
export const kToC = (k: number) => k - 273.15
export const kToF = (k: number) => (k - 273.15) * (9 / 5) + 32
```

### `services/healthz/handler.py`
```py
import json, os, time

def lambda_handler(event, context):
    # TODO: wire real probes (S3 read, tiler latency, index ages)
    resp = {
        "ok": True,
        "version": os.getenv("VERSION", "v0.1.0"),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "probes": {"placeholder": True}
    }
    return {"statusCode": 200, "headers": {"content-type": "application/json"}, "body": json.dumps(resp)}
```

### `services/*/Dockerfile` (template)
```Dockerfile
# syntax=docker/dockerfile:1
FROM public.ecr.aws/lambda/python:3.11

# For raster workflows you will likely need GDAL/PROJ — keep image small by only adding what you use.
# RUN yum -y install gdal proj && yum clean all

COPY requirements.txt ./
RUN pip install -r requirements.txt --no-cache-dir

COPY handler.py ./
CMD ["handler.lambda_handler"]
```

### `services/radar-prepare/requirements.txt` (start here)
```
boto3
xarray
numpy
pyart
rasterio
rio-cogeo
```

> Repeat the same pattern for `goes-prepare`, `mrms-prepare`, `alerts-bake` with their own dependency sets.

---

## Next steps (in order)
1) Convert & upload **planet.z15.pmtiles** into `web-static/basemaps/` (or your S3 directly) and verify the style URL in `.env`.
2) `npm i && npm run dev` inside `/web` → you should see CyclOSM basemap render.
3) Scaffold Terraform modules (or use SAM/CDK if preferred) to stand up S3 + CloudFront + API GW + Lambdas.
4) Deploy `healthz` first to validate API wiring, then TiTiler and the three prepare jobs.

> When you’re ready, I can expand any module (e.g., Terraform `static_site`) into working code in the same structure. 

