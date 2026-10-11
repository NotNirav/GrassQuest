import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

// Streets: OpenFreeMap "Liberty" (free vector tiles, no key, building outlines when zoomed in).
// Satellite: Esri World Imagery + Esri road and place labels (free, no key, credited on the map).
const STREETS = "https://tiles.openfreemap.org/styles/liberty";
const ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services";
const SATELLITE = {
  version: 8,
  sources: {
    imagery: { type: "raster", tileSize: 256, maxzoom: 19, tiles: [`${ESRI}/World_Imagery/MapServer/tile/{z}/{y}/{x}`],
      attribution: "Imagery © Esri, Maxar, Earthstar Geographics" },
    roads: { type: "raster", tileSize: 256, maxzoom: 19, tiles: [`${ESRI}/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}`] },
    places: { type: "raster", tileSize: 256, maxzoom: 19, tiles: [`${ESRI}/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}`] },
  },
  layers: [
    { id: "imagery", type: "raster", source: "imagery" },
    { id: "roads", type: "raster", source: "roads" },
    { id: "places", type: "raster", source: "places" },
  ],
};

function youMarker() {
  const el = document.createElement("div");
  el.style.cssText = "width:20px;height:20px;border-radius:50%;background:#ff5b1f;border:4px solid #fff;box-shadow:0 0 0 6px rgba(255,91,31,.25),0 2px 8px rgba(0,0,0,.35)";
  return el;
}
function destMarker() {
  const el = document.createElement("div");
  el.style.cssText = "width:24px;height:24px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);background:#17140f;border:3px solid #fff;box-shadow:0 4px 10px rgba(0,0,0,.35)";
  return el;
}

/**
 * center: { lat, lon }   your base camp (or the spot being picked)
 * destination: optional quest destination
 * onPick: when set, the pin is draggable and tapping the map moves it (base camp picker)
 * flyZoom: zoom to fly to when `center` changes (the picker uses street level)
 */
export default function MapView({ center, destination, onPick, zoom = 14, flyZoom, satellite: startSatellite = false, height }) {
  const el = useRef(null);
  const map = useRef(null);
  const you = useRef(null);
  const [satellite, setSatellite] = useState(startSatellite);

  useEffect(() => {
    if (!el.current || !center) return;
    const m = new maplibregl.Map({
      container: el.current, style: satellite ? SATELLITE : STREETS, center: [center.lon, center.lat], zoom,
      attributionControl: { compact: true }, maxZoom: 19,
    });
    m.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    you.current = new maplibregl.Marker({ element: youMarker(), draggable: !!onPick }).setLngLat([center.lon, center.lat]).addTo(m);
    map.current = m;
    return () => m.remove();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // street / satellite
  useEffect(() => { map.current?.setStyle(satellite ? SATELLITE : STREETS); }, [satellite]);

  // picker: drag the pin or tap the map
  useEffect(() => {
    const m = map.current;
    const mk = you.current;
    if (!m || !mk || !onPick) return;
    m.getCanvas().style.cursor = "crosshair";
    const tap = (e) => { mk.setLngLat(e.lngLat); onPick({ lat: e.lngLat.lat, lon: e.lngLat.lng }); };
    const drag = () => { const p = mk.getLngLat(); onPick({ lat: p.lat, lon: p.lng }); };
    m.on("click", tap);
    mk.on("dragend", drag);
    return () => { m.off("click", tap); mk.off("dragend", drag); };
  }, [onPick]);

  // follow the center (and frame the destination when there is one)
  useEffect(() => {
    const m = map.current;
    if (!m || !center) return;
    you.current?.setLngLat([center.lon, center.lat]);
    let dest;
    if (destination) {
      dest = new maplibregl.Marker({ element: destMarker(), anchor: "bottom" }).setLngLat([destination.lon, destination.lat]).addTo(m);
      const b = new maplibregl.LngLatBounds([center.lon, center.lat], [center.lon, center.lat]).extend([destination.lon, destination.lat]);
      m.fitBounds(b, { padding: 70, maxZoom: 17, duration: 700 });
    } else if (flyZoom) {
      m.flyTo({ center: [center.lon, center.lat], zoom: flyZoom, duration: 900 });
    } else {
      m.easeTo({ center: [center.lon, center.lat], duration: 500 });
    }
    return () => dest?.remove();
  }, [center?.lat, center?.lon, destination?.lat, destination?.lon]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div style={{ position: "relative" }}>
      <div ref={el} className="map" style={height ? { height } : undefined} role="img"
        aria-label={destination ? `Map from your base camp to ${destination.name}` : "Map of your base camp"} />
      <div className="map-toggle" role="group" aria-label="Map style">
        <button aria-pressed={!satellite} onClick={() => setSatellite(false)}>Map</button>
        <button aria-pressed={satellite} onClick={() => setSatellite(true)}>Satellite</button>
      </div>
    </div>
  );
}
