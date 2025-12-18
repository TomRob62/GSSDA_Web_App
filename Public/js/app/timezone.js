export function detectBrowserTimezone() {
  try {
    const { timeZone } = Intl.DateTimeFormat().resolvedOptions();
    return timeZone || null;
  } catch (error) {
    return null;
  }
}
