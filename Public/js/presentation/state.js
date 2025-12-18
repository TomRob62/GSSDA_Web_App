const ROOM_STORAGE_KEY = 'presentation:selectedRoom';

const cache = {
  rooms: [],
  callers: [],
  profiles: [],
  advertisements: [],
  profilesByCaller: new Map(),
};

export function setRooms(rooms) {
  cache.rooms = rooms;
}

export function setCallers(callers) {
  cache.callers = callers;
}

export function setProfiles(profiles, advertisements = []) {
  cache.profiles = Array.isArray(profiles) ? profiles : [];
  cache.advertisements = Array.isArray(advertisements) ? advertisements : [];
  cache.profilesByCaller = new Map();
  cache.profiles.forEach((profile) => {
    if (profile && typeof profile.caller_cuer_id === 'number') {
      cache.profilesByCaller.set(profile.caller_cuer_id, profile);
    }
  });
}

export function getRooms() {
  return cache.rooms;
}

export function getCallers() {
  return cache.callers;
}

export function getProfiles() {
  return cache.profiles;
}

export function getAdvertisements() {
  return cache.advertisements;
}

export function getProfileByCaller(callerId) {
  return cache.profilesByCaller.get(callerId) || null;
}

export function getStoredRoom() {
  return localStorage.getItem(ROOM_STORAGE_KEY) || '';
}

export function storeRoom(id) {
  if (id) {
    localStorage.setItem(ROOM_STORAGE_KEY, id);
  } else {
    localStorage.removeItem(ROOM_STORAGE_KEY);
  }
}

export function findCallerName(id) {
  const caller = cache.callers.find((item) => item.id === id);
  if (!caller) return id;
  return `${caller.first_name} ${caller.last_name}`;
}

export function formatCallerNames(ids) {
  if (!Array.isArray(ids) || !ids.length) return '—';
  return ids
    .map((id) => {
      const caller = cache.callers.find((item) => item.id === id);
      if (!caller) return `#${id}`;
      const suffix = caller.suffix ? ` ${caller.suffix}` : '';
      return `${caller.first_name} ${caller.last_name}${suffix}`.trim();
    })
    .join(', ');
}
