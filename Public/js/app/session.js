import { fetchJson } from '../components/api.js';

export function createSessionManager() {
  let user = null;

  async function loadSession() {
    const { response, data } = await fetchJson('/api/session');
    if (!response.ok) {
      const message = data?.error?.message || 'Unable to load session';
      throw new Error(message);
    }
    user = data;
    return user;
  }

  function getUser() {
    return user;
  }

  function canModify() {
    const readOnlyRoles = new Set(['attendee', 'caller']);
    if (!user?.role) return false;
    return !readOnlyRoles.has(user.role);
  }

  return { loadSession, getUser, canModify };
}
