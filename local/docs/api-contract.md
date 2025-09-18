# API Contract (Draft)

This document will define the HTTP interface exposed by the new API service. Populate with OpenAPI definitions as endpoints are implemented.

## Planned Endpoints

| Endpoint | Method | Description | Status |
| --- | --- | --- | --- |
| `/healthz` | GET | Overall system health summary | TODO |
| `/timeline/{layer}` | GET | Return timestamp list for a given layer | TODO |
| `/trigger/{job}` | POST | Manually trigger ingestion job | TODO |
| `/tiles/...` | GET | Proxy or redirect to tile assets (optional) | TODO |

Use this file to maintain a single source of truth for the API specification.
