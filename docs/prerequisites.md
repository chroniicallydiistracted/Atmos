# Local Stack Prerequisites

- **Hardware**: ≥24 CPU threads, 96 GB RAM, 1 TB NVMe primary storage, secondary 2 TB NAS/RAID for backups.
- **OS**: Ubuntu 22.04 LTS (or similar) with latest updates, firewall enabled, SSH key-based auth.
- **Required software**:
  - Docker Engine 24+
  - Docker Compose plugin 2.27+
  - Make (optional convenience)
  - Python 3.11 (for tooling/testing)
  - Node.js 20 (for frontend)
  - MinIO client (`mc`) for local object-store interaction
- **Networking**: Static IP or DHCP reservation, UPS-backed power, monitored bandwidth.
- **Certificates**: ACME client (e.g., Caddy or Certbot) if public HTTPS exposure is required.

Before running any services, ensure you have created `config/.env` based on the example file and generated any required TLS certificates (see `docs/security.md`).
