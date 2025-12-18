import { createCell, createRow, createActionsCell } from './utils.js';

export const mcHeaders = ['ID', 'Room', 'Caller', 'Start', 'End', 'Actions'];

function findRoomLabel(rooms, id) {
  return rooms.find((room) => room.id === id)?.room_number || id;
}

function findCallerLabel(callers, id) {
  const caller = callers.find((item) => item.id === id);
  if (!caller) return id;
  return `${caller.first_name} ${caller.last_name}`;
}

function formatDateTime(value) {
  return value ? new Date(value).toLocaleString() : '';
}

export function createMcRow(item, caches, handlers, options = {}) {
  const allowActions = options.allowActions !== false;
  const cells = [
    createCell(item.id),
    createCell(findRoomLabel(caches.rooms, item.room_id)),
    createCell(findCallerLabel(caches.callers, item.caller_cuer_id)),
    createCell(formatDateTime(item.start)),
    createCell(formatDateTime(item.end)),
  ];
  if (allowActions) {
    cells.push(createActionsCell(handlers.onEdit, handlers.onDelete));
  }
  return createRow(cells);
}
