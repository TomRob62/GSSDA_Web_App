import { fetchProfileImageSas } from './dataService.js';

const cache = {
  token: null,
  expiresAt: 0,
};

const CLOCK_SKEW_BUFFER_MS = 60 * 1000;

function isAzureUrl(url) {
  if (typeof url !== 'string') return false;
  return url.toLowerCase().includes('blob.core.windows.net');
}

function hasValidToken() {
  if (!cache.token) return false;
  return Date.now() + CLOCK_SKEW_BUFFER_MS < cache.expiresAt;
}

function sanitizeUrl(url) {
  if (!isAzureUrl(url)) return typeof url === 'string' ? url : '';
  const [base] = url.split('?');
  return base;
}

function needsSas(url) {
  if (!isAzureUrl(url)) return false;
  if (url.includes('sig=')) return false;
  return true;
}

function appendToken(url, token) {
  const base = sanitizeUrl(url);
  if (!base) return base;
  const separator = base.includes('?') ? '&' : '?';
  return `${base}${separator}${token}`;
}

export function invalidateProfileImageToken() {
  cache.token = null;
  cache.expiresAt = 0;
}

export async function ensureProfileImageToken() {
  if (hasValidToken()) return cache.token;
  try {
    const response = await fetchProfileImageSas();
    if (!response || !response.token) {
      cache.token = null;
      cache.expiresAt = 0;
      return null;
    }
    const expires = Date.parse(response.expires_at);
    cache.token = response.token;
    cache.expiresAt = Number.isNaN(expires) ? Date.now() + 23 * 60 * 60 * 1000 : expires;
    return cache.token;
  } catch (error) {
    console.error('Failed to obtain profile image SAS token', error);
    cache.token = null;
    cache.expiresAt = 0;
    return null;
  }
}

export async function resolveProfileImageUrl(url) {
  if (!needsSas(url)) return url;
  const token = await ensureProfileImageToken();
  if (!token) return sanitizeUrl(url);
  return appendToken(url, token);
}

export async function attachSasToProfiles(profiles) {
  if (!Array.isArray(profiles) || !profiles.length) return profiles;
  const token = await ensureProfileImageToken();
  if (!token) {
    return profiles.map((profile) => ({ ...profile, image_path: sanitizeUrl(profile?.image_path || '') || profile?.image_path || null }));
  }
  return profiles.map((profile) => {
    if (!profile || !needsSas(profile.image_path)) return profile;
    return { ...profile, image_path: appendToken(profile.image_path, token) };
  });
}
