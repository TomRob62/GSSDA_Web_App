export function toLocalDateTime(isoString) {
  if (!isoString) return '';
  const input = new Date(isoString);
  const offset = input.getTimezoneOffset() * 60000;
  return new Date(input.getTime() - offset).toISOString().slice(0, 16);
}

export function normalizeDuration(minutes) {
  // Treat 0 as a valid value. Only default when minutes is null/undefined
  // or cannot be parsed as a number. Allow durations up to 24 hours.
  if (minutes === null || minutes === undefined || Number.isNaN(minutes)) return 60;
  const MAX_MINUTES = 24 * 60; // 1440 minutes
  const clamped = Math.min(MAX_MINUTES, Math.max(5, Number(minutes)));
  return Math.round(clamped / 5) * 5;
}

export function calculateDurationMinutes(start, end) {
  if (!start || !end) return 60;
  const diffMs = new Date(end).getTime() - new Date(start).getTime();
  return normalizeDuration(Math.round(diffMs / 60000));
}

export function formatDuration(minutes) {
  const hours = Math.floor(minutes / 60);
  const remaining = minutes % 60;
  const parts = [];
  if (hours > 0) parts.push(`${hours} hour${hours > 1 ? 's' : ''}`);
  if (remaining > 0) parts.push(`${remaining} minute${remaining > 1 ? 's' : ''}`);
  return parts.length ? parts.join(' ') : '0 minutes';
}
