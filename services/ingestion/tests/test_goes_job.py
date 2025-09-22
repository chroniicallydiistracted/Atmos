import unittest
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from src.atmos_ingestion.config import IngestionSettings
from src.atmos_ingestion.jobs.goes import GoesIngestion


class _StubClients:
    def __init__(self):
        self.source = MagicMock(name="source_client")
        self.derived = MagicMock(name="derived_client")


class GoesIngestionJobTest(unittest.TestCase):
    def setUp(self):
        self.settings = IngestionSettings(
            MINIO_ENDPOINT="http://localhost:9000",
            MINIO_ROOT_USER="test",
            MINIO_ROOT_PASSWORD="secret",
            MINIO_REGION="us-east-1",
            S3_BUCKET_DERIVED="derived-test",
            GOES_SOURCE_BUCKET="goes-bucket",
            GOES_DEFAULT_BAND=13,
            GOES_DEFAULT_SECTOR="CONUS",
        )
        self.clients = _StubClients()
        self.job = GoesIngestion(self.settings, self.clients)

    def test_run_latest_uses_helpers(self):
        timestamp = datetime(2024, 8, 10, 0, 40)
        with patch(
            "src.atmos_ingestion.jobs.goes.find_latest_goes_data",
            return_value=(timestamp, "path/to/file.nc"),
        ) as latest, patch(
            "src.atmos_ingestion.jobs.goes.process_goes_file",
            return_value={"cog_key": "derived/goes/file.tif"},
        ) as processor:
            result = self.job.run(None, None, None)

        latest.assert_called_once()
        processor.assert_called_once_with(
            13,
            "CONUS",
            timestamp,
            "path/to/file.nc",
            source_bucket="goes-bucket",
            source_s3_client=self.clients.source,
            derived_s3_client=self.clients.derived,
            derived_bucket="derived-test",
        )
        self.assertEqual(result["band"], 13)
        self.assertEqual(result["sector"], "CONUS")
        self.assertEqual(result["requested_time"], "latest")
        self.assertIn("ingested_time", result)

    def test_run_with_timestamp_normalises(self):
        requested = datetime(2024, 8, 10, 0, 0, tzinfo=UTC)
        with patch(
            "src.atmos_ingestion.jobs.goes.find_goes_file_for_time",
            return_value="prefix/file.nc",
        ) as finder, patch(
            "src.atmos_ingestion.jobs.goes.extract_goes_timestamp",
            return_value=None,
        ), patch(
            "src.atmos_ingestion.jobs.goes.process_goes_file",
            return_value={},
        ) as processor:
            result = self.job.run(8, "conus", requested)

        finder.assert_called_once()
        # Ensure timestamp converted to naive UTC
        args, kwargs = processor.call_args
        self.assertEqual(kwargs["source_bucket"], "goes-bucket")
        self.assertEqual(args[0], 8)
        self.assertEqual(args[1], "CONUS")
        self.assertIsNone(args[2].tzinfo)
        self.assertEqual(result["requested_time"], "2024-08-10T00:00:00Z")

    def test_run_rejects_invalid_timestamp_string(self):
        with self.assertRaises(ValueError):
            self.job.run(None, None, "2024-08-10T00:00:00Z")


if __name__ == "__main__":
    unittest.main()
