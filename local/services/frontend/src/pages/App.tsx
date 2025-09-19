import BasemapView from "../components/BasemapView";
import TopBar from "../components/TopBar";
import { MapStateProvider } from "../context/MapStateContext";

function App() {
  return (
    <MapStateProvider>
      <div className="app-shell">
        <BasemapView />
        <TopBar />
      </div>
    </MapStateProvider>
  );
}

export default App;
