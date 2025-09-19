import { FormEvent, useMemo, useState } from "react";

import { useHealthQuery } from "../hooks/useHealthQuery";
import { useMapState } from "../context/MapStateContext";

function TopBar() {
  const { data, isFetching } = useHealthQuery();
  const { focusLocation, setFocusLocation } = useMapState();
  const [query, setQuery] = useState("");

  const healthStatus = useMemo(() => {
    if (isFetching) return "checking";
    if (!data || !data.ok) return "degraded";
    return "operational";
  }, [data, isFetching]);

  const handleLocationSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!query.trim()) return;

    const parts = query.trim().split(/[,\s]+/);
    if (parts.length >= 2) {
      const lat = Number.parseFloat(parts[0]);
      const lon = Number.parseFloat(parts[1]);
      if (!Number.isNaN(lat) && !Number.isNaN(lon)) {
        setFocusLocation({ lat, lon, label: query.trim() });
        setQuery("");
      }
    }
  };

  return (
    <header className="top-bar overlay-card">
      <div className="brand">
        <span className="brand-mark" />
        <div>
          <h1>Atmos Insight</h1>
          <p className="brand-subtitle">Realtime weather situational awareness</p>
        </div>
      </div>
      <form className="location-form" onSubmit={handleLocationSubmit}>
        <label className="sr-only" htmlFor="location-input">
          Jump to coordinates
        </label>
        <input
          id="location-input"
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="e.g. 39.0997 -94.5786"
        />
        <button type="submit">Go</button>
      </form>
      <div className="status-group">
        <div className={`status-indicator status-${healthStatus}`}>
          <span className="dot" />
          <span className="label">{healthStatus}</span>
        </div>
        <div className="focus-readout">
          <span>Center:</span>
          <strong>{focusLocation.label}</strong>
        </div>
      </div>
    </header>
  );
}

export default TopBar;
