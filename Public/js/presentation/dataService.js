import { fetchJson, authHeaders } from '../components/api.js';
import { loadRooms as loadRoomsBase, loadCallers as loadCallersBase } from '../app/dataService.js';
import { attachSasToProfiles } from '../app/profileImageService.js';

export const loadRooms = loadRoomsBase;
export const loadCallers = loadCallersBase;

async function fetchCollection(url) {
  const { response, data } = await fetchJson(url, { headers: authHeaders() });
  if (!response.ok) {
    const message = data?.error?.message || 'Request failed';
    throw new Error(message);
  }
  if (Array.isArray(data)) {
    return data;
  }
  return data?.data || [];
}

export function loadEvents(roomId) {
  return fetchCollection(`/api/events?room_id=${roomId}&page_size=200`);
}

export function loadMcs(roomId) {
  return fetchCollection(`/api/mcs?room_id=${roomId}&page_size=200`);
}

export async function loadProfiles() {
  const profiles = await fetchCollection('/api/profiles?page_size=200&sort=caller:asc');
  return attachSasToProfiles(profiles);
}

export async function loadAdvertisementProfiles(limit = 50) {
  const params = new URLSearchParams();
  if (limit) params.set('limit', String(limit));
  const profiles = await fetchCollection(`/api/profiles/advertisements?${params.toString()}`);
  return attachSasToProfiles(profiles);
}
