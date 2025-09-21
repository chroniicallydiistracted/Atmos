import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: "./vitest.setup.ts",
    globals: true
  },
  server: {
    port: 4173,
    host: true,
    proxy: {
      // Forward API calls during dev directly to the API service container
      '/api': {
        target: 'http://api:8081',
        changeOrigin: true,
        // IMPORTANT: mimic Caddy's `handle_path /api/*` which STRIPS the /api prefix
        // so the FastAPI app still sees /v1/... (not /api/v1/...). Without this rewrite
        // dev requests to /api/v1/... return 404 because the backend has no /api/v1 routes.
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      // Forward tiles to tiler (Caddy also does this when using reverse proxy on port 80)
      '/tiles': {
        target: 'http://tiler:8083',
        changeOrigin: true,
      }
    }
  }
});
