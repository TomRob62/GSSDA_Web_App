import { createCell, createRow, createActionsCell } from './utils.js';

export const callerHeaders = ['ID', 'First Name', 'Last Name', 'MC', 'Dance Types', 'Actions'];

export function createCallerRow(item, _caches, handlers, options = {}) {
  const allowActions = options.allowActions !== false;
  const danceTypes = (item.dance_types || []).join(', ');
  const cells = [
    createCell(item.id),
    createCell(item.first_name),
    createCell(item.last_name),
    createCell(item.mc ? 'Yes' : 'No'),
    createCell(danceTypes),
  ];
  if (allowActions) {
    cells.push(createActionsCell(handlers.onEdit, handlers.onDelete));
  }
  return createRow(cells);
}
