from fastapi import FastAPI
from pydantic_settings import BaseSettings
import os
import socket
from minio import Minio
import psycopg

class Settings(BaseSettings):
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8081"))

    # MinIO / S3-compatible
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "http://object-store:9000")
    minio_access_key: str = os.getenv("MINIO_ROOT_USER", "localminio")
    minio_secret_key: str = os.getenv("MINIO_ROOT_PASSWORD", "change-me-now")
    minio_secure: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"

    # Postgres
    database_url: str = os.getenv("DATABASE_URL", "postgresql://osm:change-me-too@postgres:5432/osm")

settings = Settings()
app = FastAPI(title="Atmos API", version="0.1.0")


def check_minio():
    # Parse endpoint into host/port and secure flag
    endpoint = settings.minio_endpoint
    # strip protocol for Minio client endpoint
    if endpoint.startswith("http://"):
        host = endpoint[len("http://"):]
        secure = False
    elif endpoint.startswith("https://"):
        host = endpoint[len("https://"):]
        secure = True
    else:
        host = endpoint
        secure = settings.minio_secure

    client = Minio(
        host,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=secure,
    )
    # simple list to confirm connectivity
    _ = list(client.list_buckets())
    return True


def check_postgres():
    with psycopg.connect(settings.database_url, connect_timeout=3) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            _ = cur.fetchone()
    return True


@app.get("/healthz")
async def healthz():
    status: dict[str, str] = {"service": "api", "host": socket.gethostname()}
    try:
        check_minio()
        status["minio"] = "ok"
    except Exception as e:
        status["minio"] = f"error: {e}"

    try:
        check_postgres()
        status["postgres"] = "ok"
    except Exception as e:
        status["postgres"] = f"error: {e}"

    overall = all(v == "ok" for k, v in status.items() if k in ("minio", "postgres"))
    status["ok"] = "true" if overall else "false"
    return status

def get_minio_client() -> Minio:
    endpoint = settings.minio_endpoint
    if endpoint.startswith("http://"):
        host = endpoint[len("http://"):]
        secure = False
    elif endpoint.startswith("https://"):
        host = endpoint[len("https://"):]
        secure = True
    else:
        host = endpoint
        secure = settings.minio_secure
    return Minio(
        host,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=secure,
    )

@app.get("/timeline/{layer}")
async def timeline(layer: str):
    """List available timeline entries by enumerating index objects under indices/{layer}/ in the derived bucket.

    Returns a list of object names (without the prefix) sorted lexicographically.
    """
    bucket = os.getenv("S3_BUCKET_DERIVED", "derived")
    prefix = f"indices/{layer}/"
    client = get_minio_client()
    objs = client.list_objects(bucket, prefix=prefix, recursive=True)
    entries: list[str] = []
    for obj in objs:
        key = obj.object_name
        if key.startswith(prefix):
            entries.append(key[len(prefix):])
    entries.sort()
    return {"layer": layer, "count": len(entries), "entries": entries}

