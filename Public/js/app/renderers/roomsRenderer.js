import { createCell, createRow, createActionsCell } from './utils.js';

export const roomHeaders = ['ID', 'Room Number', 'Static', 'Descriptions', 'Actions'];

function buildDescription(item) {
  return item.descriptions
    .map((description) => {
      if (item.static) return description.description || '';
      const start = description.start_time ? new Date(description.start_time).toLocaleString() : '';
      const end = description.end_time ? new Date(description.end_time).toLocaleString() : '';
      const label = description.description || '';
      return `${start} – ${end}: ${label}`.trim();
    })
    .join('\n');
}

export function createRoomRow(item, _caches, handlers, options = {}) {
  const allowActions = options.allowActions !== false;
  const cells = [
    createCell(item.id),
    createCell(item.room_number),
    createCell(item.static ? 'Yes' : 'No'),
    createCell(buildDescription(item)),
  ];
  cells[3].style.whiteSpace = 'pre-wrap';
  if (allowActions) {
    cells.push(createActionsCell(handlers.onEdit, handlers.onDelete));
  }
  return createRow(cells);
}
