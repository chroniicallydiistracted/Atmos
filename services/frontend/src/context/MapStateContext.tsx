import { createContext, ReactNode, useContext, useMemo, useState } from "react";

export interface FocusLocation {
  lat: number;
  lon: number;
  label: string;
}

interface MapState {
  focusLocation: FocusLocation;
  setFocusLocation: (location: FocusLocation) => void;
}

const MapStateContext = createContext<MapState | null>(null);

export const MapStateProvider = ({ children }: { children: ReactNode }) => {
  const [focusLocation, setFocusLocation] = useState<FocusLocation>({ lat: 38, lon: -97, label: "CONUS" });

  const value = useMemo<MapState>(
    () => ({
      focusLocation,
      setFocusLocation,
    }),
    [focusLocation]
  );

  return <MapStateContext.Provider value={value}>{children}</MapStateContext.Provider>;
};

export function useMapState(): MapState {
  const context = useContext(MapStateContext);
  if (!context) {
    throw new Error("useMapState must be used within MapStateProvider");
  }
  return context;
}
