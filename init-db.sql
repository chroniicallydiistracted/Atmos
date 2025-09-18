-- Initialize PostGIS extensions for development database
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS hstore;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Show versions for verification
SELECT PostGIS_version();
SELECT version();