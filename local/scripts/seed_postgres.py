#!/usr/bin/env python3
"""Create placeholder tables and data inside the local Postgres instance."""
from __future__ import annotations

import argparse
import os

import psycopg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dsn",
        default=os.getenv(
            "DATABASE_URL",
            "postgresql://osm:change-me-too@localhost:5432/osm",
        ),
        help="Postgres connection string",
    )
    return parser.parse_args()


def seed_database(dsn: str) -> None:
    ddl = """
    CREATE TABLE IF NOT EXISTS ingestion_events (
        id SERIAL PRIMARY KEY,
        job TEXT NOT NULL,
        parameters JSONB NOT NULL,
        status TEXT NOT NULL,
        detail JSONB,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """

    with psycopg.connect(dsn, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
            cur.execute(
                "INSERT INTO ingestion_events (job, parameters, status) VALUES (%s, %s, %s)",
                ("seed", {"note": "bootstrap"}, "ok"),
            )

    print("Seeded ingestion_events table with placeholder row.")


def main() -> None:
    args = parse_args()
    try:
        seed_database(args.dsn)
    except Exception as exc:  # pragma: no cover - CLI surface
        raise SystemExit(f"Failed to seed Postgres: {exc}")


if __name__ == "__main__":
    main()
