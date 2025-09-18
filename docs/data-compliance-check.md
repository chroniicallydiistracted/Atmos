# Data Retention & Compliance Assessment

## 1. Regulatory & Contractual Obligations
- **NOAA/NWS data** – Public domain; no redistribution restrictions, but retain attribution in UI (already provided). No mandated retention period.
- **Cloud-to-ground lightning / MRMS / GOES** – Same as above; ensure metadata includes acquisition timestamps.
- **User accounts / PII** – None in current stack. If future users introduced, reassess GDPR/CCPA requirements.
- **Operational logs** – CloudWatch currently retains 14 days. For on-prem migration, choose retention that balances troubleshooting vs. storage (recommend 30–60 days hot, archive quarterly snapshots).

## 2. Business Retention Goals
- Current S3 lifecycle policies keep derived weather data for 7 days, with optional Glacier tiers at 90/365 days and deletion after 7 years.
- Determine whether long-term archives are required locally:
  - **Short-term (≤7 days)** – Keep raw and derived data on fast storage (`data/derived`, `data/raw`).
  - **Medium-term (30–180 days)** – Move to slower disks or NAS if analysis workloads demand.
  - **Long-term (>1 year)** – Optional; cost/benefit should be revisited. If needed, schedule quarterly offline backups (tape or cold NAS).

## 3. Local Hardware & Storage Verification
- **Primary node** – Requirement defined earlier: ≥24 cores, 96 GB RAM, 1 TB NVMe primary, 2 TB secondary/NAS.
- **Capacity check** – Storage plan totals ~670 GB, so a 1 TB NVMe with 30% headroom suffices. Ensure ZFS/Btrfs snapshots or RAID1 for redundancy.
- **Backup target** – Need 2–3 TB external/NAS to store incremental snapshots (Postgres dumps, MinIO object store, configuration).
- **Network** – Provision UPS + surge protection, monitor bandwidth for NOAA downloads.

## 4. Gaps & Actions
- [ ] Confirm actual hardware specs match or exceed requirements (CPU, RAM, NVMe, backup storage, UPS). Document serial numbers/warranty.
- [ ] Define backup cadence (daily Postgres dump, hourly object-store rsync, weekly full snapshot). Automate and test restorations quarterly.
- [ ] Choose logging retention policy (hot vs. cold storage). Implement log rotation on services to avoid disk fill.
- [ ] Document NOAA data attribution/usage policy in README/status page to maintain compliance.

## 5. Acceptance Criteria
- Hardware audit completed and recorded.
- Backup strategy approved and test schedule defined.
- Retention policy for each dataset tier accepted by stakeholders.
- Compliance notes (public-domain data, no PII) acknowledged.

Once all boxes above are checked, Phase 0 Step 3 can be marked complete.
