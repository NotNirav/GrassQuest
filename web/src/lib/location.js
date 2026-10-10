// Browser location. The exact point stays in this browser and is sent only to measure distances; the server never stores it.
/** "granted" | "prompt" | "denied" | "unknown" — lets us explain a block instead of failing silently. */
export async function locationPermission() {
  try {
    return (await navigator.permissions.query({ name: "geolocation" })).state;
  } catch {
    return "unknown";
  }
}

export function currentPlace() {
  return new Promise((resolve, reject) => {
    if (!("geolocation" in navigator)) return reject(new Error("This browser can't share location. Search for your city instead."));
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: round(pos.coords.latitude), lon: round(pos.coords.longitude), accuracy: Math.round(pos.coords.accuracy), label: null }),
      (err) => reject(Object.assign(new Error(err.code === 1 ? "denied" : err.code === 3 ? "timeout" : "unavailable"), { code: err.code })),
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60 * 1000 },
    );
  });
}

export const round = (x) => Math.round(x * 1e5) / 1e5; // ~1 m

export function bearingArrow(bearing) {
  return { north: 0, "north-east": 45, east: 90, "south-east": 135, south: 180, "south-west": 225, west: 270, "north-west": 315 }[bearing] ?? 0;
}

export function formatDistance(m) {
  return m < 1000 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toFixed(1)} km`;
}
