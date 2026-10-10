// Real photography from Unsplash (free licence), served by Unsplash's CDN.
const ID = {
  hero: "1539635278303-d4002c07eae3",
  walk: "1529003532648-93cc0f57b7eb",
  leaf: "1509070016581-915335454d19",
  bird: "1620588280212-bf1d2b23b112",
  path: "1487956382158-bb926046304a",
  sky: "1592596959482-34fb465b60e1",
  run: "1486218119243-13883505764c",
  street: "1619492213998-d5088da53dad",
  lake: "1464198016405-33fd4527b89d",
  calm: "1534396708547-d8e912eb38ba",
  camera: "1602538715538-9c034a2f8043",
  picnic: "1613109040830-ffdd96756f5e",
  rain: "1433863448220-78aaa064ff47",
  friends: "1525474089639-b5fff4440315",
};

export const CATEGORY_PHOTO = {
  nature: "leaf", birds: "bird", sky: "sky", move: "run", explore: "street", water: "lake",
  mindful: "calm", photo: "camera", social: "friends", food: "picnic", rain: "rain",
};

export function photo(key, w = 800) {
  return `https://images.unsplash.com/photo-${ID[key] ?? ID.path}?w=${w}&q=70&auto=format&fit=crop`;
}
