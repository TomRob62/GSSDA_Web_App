import { fetchJson, authHeaders } from '../components/api.js';
import { loadRooms as baseLoadRooms, loadCallers as baseLoadCallers } from '../app/dataService.js';

export const loadRooms = baseLoadRooms;
export const loadCallers = baseLoadCallers;

export async function loadEvents() {
  const { response, data } = await fetchJson('/api/events?page_size=200&sort=start', {
    headers: authHeaders(),
  });
  if (!response.ok) {
    const message = data?.error?.message || 'Unable to load events';
    throw new Error(message);
  }
  return Array.isArray(data?.data) ? data.data : [];
}
