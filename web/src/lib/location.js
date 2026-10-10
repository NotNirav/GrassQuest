// Browser location, rounded to ~1 km before it's stored or sent anywhere.
export function currentPlace() {
  return new Promise((resolve, reject) => {
    if (!("geolocation" in navigator)) return reject(new Error("This browser can't share location. Search for your city instead."));
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: round(pos.coords.latitude), lon: round(pos.coords.longitude), label: null }),
      (err) => reject(new Error(err.code === 1 ? "Location permission was denied. Search for your city instead." : "Couldn't get your location. Search for your city instead.")),
      { enableHighAccuracy: false, timeout: 12000, maximumAge: 10 * 60 * 1000 },
    );
  });
}

const round = (x) => Math.round(x * 100) / 100;

export function bearingArrow(bearing) {
  return { north: 0, "north-east": 45, east: 90, "south-east": 135, south: 180, "south-west": 225, west: 270, "north-west": 315 }[bearing] ?? 0;
}

export function formatDistance(m) {
  return m < 1000 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toFixed(1)} km`;
}
