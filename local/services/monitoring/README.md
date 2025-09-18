# Monitoring Stack

Optional component enabling Prometheus + Grafana + Loki for observability. Enabled via compose profile `monitoring`.

## Planned Setup
- Prometheus scraping ingestion, basemap, API, Postgres, system metrics.
- Loki collecting structured logs (JSON) from containers.
- Grafana dashboards for weather data freshness, tile latency, resource usage.

## TODO
- Define `docker-compose.monitoring.yml` overrides or extend main compose with service definitions.
- Create dashboards and alert rules referencing local needs (no CloudWatch).
