import { populateRoomSelect } from './roomSelect.js';
import { renderMcInfo } from './mcInfo.js';
import { renderEvents } from './events.js';
import { showLoadingState, renderSelectionPrompt, renderErrorState, renderEmptySchedule } from './placeholders.js';

export { populateRoomSelect, showLoadingState, renderSelectionPrompt, renderErrorState };

export function renderSchedule(elements, room, events, currentMc, nextMc) {
  elements.roomTitle.textContent = room ? room.room_number : 'Select a room';
  // Set room description if available. Rooms store descriptions as an array
  // with optional start_time / end_time windows. Choose the one active now.
  if (elements.roomDescription) {
    let descText = '';
    if (room && Array.isArray(room.descriptions) && room.descriptions.length) {
      const now = new Date();
      // find descriptions where (start_time is null or <= now) and (end_time is null or >= now)
      const active = room.descriptions.find((d) => {
        const start = d.start_time ? new Date(d.start_time) : null;
        const end = d.end_time ? new Date(d.end_time) : null;
        if (start && start > now) return false;
        if (end && end < now) return false;
        return true;
      });
      const chosen = active || room.descriptions[0];
      descText = chosen && chosen.description ? chosen.description : '';
    }
    elements.roomDescription.textContent = descText;
  }
  renderMcInfo(elements.mcInfo, currentMc, nextMc);
  // Remove expired events (those that ended before now) so the presentation
  // does not show past items. Keep the original array untouched.
  const now = new Date();
  const visibleEvents = events.filter((ev) => new Date(ev.end) >= now);
  if (!visibleEvents.length) {
    renderEmptySchedule(elements.eventList);
    return;
  }
  renderEvents(elements.eventList, visibleEvents);
}
