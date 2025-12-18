import { loadRooms, loadCallers, loadEventDays } from '../dataService.js';
import { setRooms, setCallers, setEventDays, getTimezone } from '../state.js';

export function createCacheController(filterController, onFilterReady, notifyError) {
  async function refreshCaches() {
    try {
      const timezone = getTimezone();
      const [rooms, callers, days] = await Promise.all([
        loadRooms(),
        loadCallers(),
        loadEventDays(timezone),
      ]);
      setRooms(rooms);
      setCallers(callers);
      setEventDays(days);
      filterController.refreshInput();
      onFilterReady();
    } catch (error) {
      notifyError(error.message);
    }
  }

  return { refreshCaches };
}
