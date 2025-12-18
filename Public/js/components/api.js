const JSON_CONTENT_TYPE = 'application/json';

function buildHeaders(extra = {}, { isMultipart = false } = {}) {
  const token = localStorage.getItem('token') || '';
  const authHeader = token ? { Authorization: `Bearer ${token}` } : {};
  const normalized = { ...extra };
  const hasContentType = Object.keys(normalized).some((key) => key.toLowerCase() === 'content-type');
  const base = {};
  if (!isMultipart && !hasContentType) {
    base['Content-Type'] = JSON_CONTENT_TYPE;
  }
  return { ...base, ...authHeader, ...normalized };
}

export function authHeaders(extra = {}, options = {}) {
  return buildHeaders(extra, options);
}

export async function fetchJson(url, options = {}) {
  const config = { ...options };
  if (options.headers) {
    config.headers = options.headers;
  } else {
    const isMultipart = options.body instanceof FormData;
    config.headers = buildHeaders({}, { isMultipart });
  }
  const response = await fetch(url, config);
  const data = await response
    .clone()
    .json()
    .catch(() => null);
  return { response, data };
}
