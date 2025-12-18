import { getTimezone } from './state.js';

export function buildQueryString(elements, filterController) {
  const view = elements.getActiveView();
  const params = new URLSearchParams({ view, page_size: '100', page: '1' });
  if (elements.sortSelect.value) params.set('sort', elements.sortSelect.value);
  const searchTerm = elements.searchInput.value.trim();
  if (searchTerm) params.set('search', searchTerm);
  const filter = filterController.getFilterParams(view);
  if (filter) {
    params.set('filter_field', filter.field);
    params.set('filter_value', filter.value);
  }
  const timezone = getTimezone();
  if (timezone) params.set('timezone', timezone);
  return params.toString();
}
