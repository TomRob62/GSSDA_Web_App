import { createCell, createRow, createActionsCell } from './utils.js';

export const eventHeaders = ['ID', 'Room', 'Callers/Cuers', 'Start', 'End', 'Dance Types', 'Actions'];

function findRoomLabel(rooms, id) {
  return rooms.find((room) => room.id === id)?.room_number || id;
}

function formatCallerLabels(callers, ids) {
  if (!Array.isArray(ids) || !ids.length) return '—';
  return ids
    .map((id) => {
      const caller = callers.find((item) => item.id === id);
      if (!caller) return `#${id}`;
      const suffix = caller.suffix ? ` ${caller.suffix}` : '';
      return `${caller.first_name} ${caller.last_name}${suffix}`.trim();
    })
    .join(', ');
}

function formatDateTime(value) {
  return value ? new Date(value).toLocaleString() : '';
}

export function createEventRow(item, caches, handlers, options = {}) {
  const allowActions = options.allowActions !== false;
  const cells = [
    createCell(item.id),
    createCell(findRoomLabel(caches.rooms, item.room_id)),
    createCell(formatCallerLabels(caches.callers, item.caller_cuer_ids)),
    createCell(formatDateTime(item.start)),
    createCell(formatDateTime(item.end)),
    createCell((item.dance_types || []).join(', ')),
  ];
  if (allowActions) {
    cells.push(createActionsCell(handlers.onEdit, handlers.onDelete));
  }
  return createRow(cells);
}
