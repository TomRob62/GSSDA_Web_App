import { loadRooms, loadCallers, loadEvents } from './dataService.js';
import { setRooms, setCallers, setEvents, getRooms, getDisplayEvents } from './state.js';
import { renderEvents, showLoadingState, showErrorState, showEmptyState } from './render.js';

export function createBoardController(elements, scrollManager) {
  async function loadLookups() {
    const [rooms, callers] = await Promise.all([loadRooms(), loadCallers()]);
    setRooms(rooms);
    setCallers(callers);
  }

  async function refreshBoard({ showLoading = false } = {}) {
    if (showLoading) {
      showLoadingState(elements.list);
    }
    try {
      const events = await loadEvents();
      setEvents(events);
      const displayEvents = getDisplayEvents();
      if (!displayEvents.length) {
        showEmptyState(elements.list);
        return;
      }
      renderEvents(elements.list, displayEvents);
      // status element removed; nothing to clear here
      scrollManager.refresh();
    } catch (error) {
      console.error('Failed to refresh caller board', error);
      showErrorState(elements.list, error.message);
    }
  }

  return { loadLookups, refreshBoard };
}
