import { fetchJson, authHeaders } from '../components/api.js';

async function requestJson(url, options = {}) {
  const isMultipart = options.isMultipart || options.body instanceof FormData;
  const headers = authHeaders(options?.headers, { isMultipart });
  const fetchOptions = { ...options, headers };
  delete fetchOptions.isMultipart;
  const { response, data } = await fetchJson(url, fetchOptions);
  if (response.ok) return data;
  const message = data?.error?.message || 'Request failed';
  throw new Error(message);
}

export async function loadRooms() {
  const data = await requestJson('/api/rooms?page_size=200');
  return data?.data || [];
}

export async function loadCallers() {
  const data = await requestJson('/api/caller_cuers?page_size=200');
  return data?.data || [];
}

export async function loadEventDays(timezone) {
  const params = new URLSearchParams();
  if (timezone) params.set('timezone', timezone);
  const query = params.toString();
  const url = query ? `/api/events/days?${query}` : '/api/events/days';
  const data = await requestJson(url);
  return Array.isArray(data) ? data : [];
}

export async function fetchAdvancedList(query) {
  const data = await requestJson(`/api/advanced?${query}`);
  return data?.data || [];
}

export async function submitItem(type, mode, payload, id, options = {}) {
  const url = mode === 'edit' ? `/api/${type}/${id}` : `/api/${type}`;
  const method = mode === 'edit' ? 'PATCH' : 'POST';
  const isMultipart = options.isMultipart || payload instanceof FormData;
  const body = isMultipart ? payload : JSON.stringify(payload);
  await requestJson(url, { method, body, isMultipart });
}

export async function removeItem(type, id) {
  await requestJson(`/api/${type}/${id}`, { method: 'DELETE' });
}

export async function fetchProfileImageSas(durationHours = 24) {
  const params = new URLSearchParams({ duration_hours: String(durationHours) });
  return requestJson(`/api/profiles/image-sas?${params.toString()}`);
}

export { requestJson };
