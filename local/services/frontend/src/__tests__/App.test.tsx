import { vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import App from "../pages/App";
import { queryClient } from "../lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";

vi.mock("maplibre-gl", () => {
  const mapMock = vi.fn(() => ({
    on: vi.fn(),
    off: vi.fn(),
    remove: vi.fn(),
    flyTo: vi.fn(),
    getStyle: () => ({ layers: [], sources: {} }),
  }));

  const protocolMock = vi.fn();

  const defaultExport = {
    Map: mapMock,
    addProtocol: protocolMock,
    removeProtocol: protocolMock,
  };

  return {
    __esModule: true,
    default: defaultExport,
    Map: mapMock,
    addProtocol: protocolMock,
    removeProtocol: protocolMock,
  };
});

function renderApp() {
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <App />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

vi.stubGlobal("fetch", vi.fn((url: RequestInfo | URL) => {
  if (typeof url === "string" && url.endsWith("/v1/healthz")) {
    return Promise.resolve(
      new Response(JSON.stringify({ checks: { minio: "ok" }, ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      })
    );
  }
  // Allow MapLibre and Vite asset requests to resolve with an empty payload during tests
  return Promise.resolve(
    new Response("", {
      status: 200,
      headers: { "Content-Type": "application/json" }
    })
  );
}));

afterEach(() => {
  queryClient.clear();
  vi.clearAllMocks();
});

test("renders basemap shell", async () => {
  renderApp();

  await waitFor(() => expect(screen.getByText(/Atmos Insight/)).toBeInTheDocument());
  expect(screen.getByPlaceholderText(/e\.g\./i)).toBeInTheDocument();
});
