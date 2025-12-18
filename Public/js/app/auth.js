import { authHeaders, fetchJson } from '../components/api.js';

export function ensureAuthenticated() {
  const token = localStorage.getItem('token');
  if (token) return true;
  window.location.href = '/login';
  return false;
}

export function registerLogout(link) {
  if (!link) return;
  link.addEventListener('click', async (event) => {
    event.preventDefault();
    try {
      await fetchJson('/api/logout', { method: 'POST', headers: authHeaders() });
    } catch (error) {
      console.error('Logout failed', error);
    }
    localStorage.removeItem('token');
    window.location.href = '/login';
  });
}
