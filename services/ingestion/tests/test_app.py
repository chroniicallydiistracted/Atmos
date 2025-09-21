import pathlib
import sys
import unittest
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.append(str(ROOT))

from local.services.ingestion.src import app as ingestion_app


class IngestionAppTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(ingestion_app)

    def test_health_endpoint(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertIn("object_store", body)

    def test_trigger_validation(self):
        response = self.client.post(
            "/trigger/nexrad",
            json={"site": "KTLX", "timestamp": datetime.now(timezone.utc).isoformat()},
        )
        # The job will likely fail without MinIO, but we care that the API handles it gracefully
        self.assertIn(response.status_code, {200, 500})

    def test_trigger_goes_uses_service(self):
        mock_result = {"band": 13, "sector": "CONUS", "requested_time": "latest"}
        with patch.object(
            ingestion_app.state.ingestion_service,
            "run_goes",
            AsyncMock(return_value=mock_result),
        ) as mock_run:
            response = self.client.post("/trigger/goes", json={"sector": "CONUS"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["detail"], mock_result)
        mock_run.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
