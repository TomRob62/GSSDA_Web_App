import { roomHeaders, createRoomRow } from './roomsRenderer.js';
import { callerHeaders, createCallerRow } from './callerRenderer.js';
import { eventHeaders, createEventRow } from './eventRenderer.js';
import { mcHeaders, createMcRow } from './mcRenderer.js';
import { profileHeaders, createProfileRow } from './profileRenderer.js';

const RENDERERS = {
  rooms: { headers: roomHeaders, row: createRoomRow, actionsHeader: 'Actions' },
  caller_cuers: { headers: callerHeaders, row: createCallerRow, actionsHeader: 'Actions' },
  events: { headers: eventHeaders, row: createEventRow, actionsHeader: 'Actions' },
  mcs: { headers: mcHeaders, row: createMcRow, actionsHeader: 'Actions' },
  profiles: { headers: profileHeaders, row: createProfileRow, actionsHeader: 'Actions' },
};

function buildHeaderRow(headers) {
  const thead = document.createElement('thead');
  const row = document.createElement('tr');
  headers.forEach((title) => {
    const cell = document.createElement('th');
    cell.textContent = title;
    row.appendChild(cell);
  });
  thead.appendChild(row);
  return thead;
}

function buildBody(viewConfig, items, caches, handlers, options) {
  const tbody = document.createElement('tbody');
  // Insert a date divider when the day changes between consecutive items.
  let prevDate = null;
  const colCount = options.colCount || viewConfig.headers.length;
  items.forEach((item) => {
    // Determine item start timestamp (events/mcs use `start`)
    const startVal = item.start || item.start_time || null;
    if (startVal) {
      try {
        const itemDate = new Date(startVal).toLocaleDateString(undefined, {
          month: 'long',
          day: 'numeric',
          year: 'numeric',
        });
        if (itemDate !== prevDate) {
          const divider = document.createElement('tr');
          divider.className = 'date-divider-row';
          const td = document.createElement('td');
          td.colSpan = colCount;
          td.style.textAlign = 'center';
          td.className = 'date-divider-cell';
          td.textContent = itemDate;
          divider.appendChild(td);
          tbody.appendChild(divider);
          prevDate = itemDate;
        }
      } catch (e) {
        // ignore date parsing errors and continue
      }
    }

    const rowHandlers = {
      onEdit: handlers.onEdit ? () => handlers.onEdit(item) : undefined,
      onDelete: handlers.onDelete ? () => handlers.onDelete(item) : undefined,
    };
    const row = viewConfig.row(item, caches, rowHandlers, options);
    tbody.appendChild(row);
  });
  return tbody;
}

export function renderList(container, view, items, caches, handlers, options = {}) {
  const viewConfig = RENDERERS[view];
  if (!viewConfig) return;
  const allowActions = options.allowActions !== false;
  container.innerHTML = '';
  const table = document.createElement('table');
  const headers = allowActions
    ? viewConfig.headers
    : viewConfig.headers.filter((header) => header !== viewConfig.actionsHeader);
  table.appendChild(buildHeaderRow(headers));
  const rowHandlers = allowActions ? handlers : {};
  // Pass column count to buildBody so divider rows can span the full width
  table.appendChild(buildBody(viewConfig, items, caches, rowHandlers, { ...options, allowActions, colCount: headers.length }));
  const card = document.createElement('div');
  card.className = 'table-container';
  card.appendChild(table);
  container.appendChild(card);
}
