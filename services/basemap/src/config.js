import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const repoEnv = path.resolve(__dirname, '..', '..', '..', 'config', '.env');
dotenv.config({ path: repoEnv, override: false });

typeof process.env.BASEMAP_DATA_DIR;

function resolveLocation(value, fallback) {
  if (!value || value.trim().length === 0) {
    return fallback;
  }
  if (path.isAbsolute(value)) {
    return value;
  }
  return path.resolve(value);
}

export const config = {
  port: parseInt(process.env.BASEMAP_PORT || '8082', 10),
  dataDir: resolveLocation(process.env.BASEMAP_DATA_DIR, path.resolve('local/data/basemaps')),
  defaultPmtiles: process.env.BASEMAP_PMTILES_DEFAULT || 'planet.pmtiles',
  corsOrigins: (process.env.BASEMAP_CORS_ORIGINS || 'http://localhost:4173').split(',').map((origin) => origin.trim()).filter(Boolean),
};

export default config;
