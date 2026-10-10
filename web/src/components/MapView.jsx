import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

// OpenFreeMap: free vector tiles, no API key.
const STYLE = "https://tiles.openfreemap.org/styles/positron";

/** You (rounded to ~1 km) and where the quest sends you. */
export default function MapView({ center, destination }) {
  const el = useRef(null);
  const map = useRef(null);

  useEffect(() => {
    if (!el.current || !center) return;
    const m = new maplibregl.Map({ container: el.current, style: STYLE, center: [center.lon, center.lat], zoom: 14, attributionControl: { compact: true } });
    m.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    map.current = m;
    return () => m.remove();
  }, [center?.lat, center?.lon]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const m = map.current;
    if (!m || !center) return;
    const markers = [];
    const you = document.createElement("div");
    you.style.cssText = "width:16px;height:16px;border-radius:50%;background:#17140f;border:3px solid #fff;box-shadow:0 0 0 6px rgba(23,20,15,.15)";
    markers.push(new maplibregl.Marker({ element: you }).setLngLat([center.lon, center.lat]).addTo(m));
    if (destination) {
      const pin = document.createElement("div");
      pin.style.cssText = "width:22px;height:22px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);background:#ff5b1f;border:3px solid #fff;box-shadow:0 4px 10px rgba(0,0,0,.3)";
      markers.push(new maplibregl.Marker({ element: pin, anchor: "bottom" }).setLngLat([destination.lon, destination.lat]).addTo(m));
      const b = new maplibregl.LngLatBounds([center.lon, center.lat], [center.lon, center.lat]).extend([destination.lon, destination.lat]);
      m.fitBounds(b, { padding: 60, maxZoom: 16, duration: 600 });
    } else {
      m.easeTo({ center: [center.lon, center.lat], zoom: 15, duration: 600 });
    }
    return () => markers.forEach((mk) => mk.remove());
  }, [center?.lat, center?.lon, destination?.lat, destination?.lon]); // eslint-disable-line react-hooks/exhaustive-deps

  return <div ref={el} className="map" role="img" aria-label={destination ? `Map to ${destination.name}` : "Map of your area"} />;
}
