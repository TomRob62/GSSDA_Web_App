import { createCell, createRow, createActionsCell } from './utils.js';

function buildCallerName(profile) {
  const caller = profile.caller || {};
  const suffix = caller.suffix ? ` ${caller.suffix}` : '';
  const baseName = `${caller.first_name || ''} ${caller.last_name || ''}${suffix}`.trim();
  if (profile.advertisement) {
    if (baseName) return `${baseName} (Advertisement)`;
    return 'Advertisement';
  }
  return baseName || '—';
}

function buildImageCell(profile) {
  const wrapper = document.createElement('div');
  wrapper.className = 'profile-image-cell';
  if (profile.image_path) {
    const img = document.createElement('img');
    img.src = profile.image_path;
    img.alt = profile.advertisement
      ? 'Advertisement graphic'
      : `${buildCallerName(profile)} portrait`;
    img.loading = 'lazy';
    wrapper.appendChild(img);
  } else {
    wrapper.textContent = '—';
  }
  return createCell(wrapper);
}

function buildContentSnippet(profile) {
  const snippet = (profile.content || '').trim();
  if (!snippet) return '—';
  if (snippet.length <= 120) return snippet;
  return `${snippet.slice(0, 117)}…`;
}

function formatUpdatedAt(value) {
  if (!value) return '—';
  try {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '—';
    return date.toLocaleString();
  } catch (error) {
    return '—';
  }
}

export const profileHeaders = ['ID', 'Caller', 'Image', 'Summary', 'Updated', 'Actions'];

export function createProfileRow(item, _caches, handlers, options = {}) {
  const allowActions = options.allowActions !== false;
  const cells = [
    createCell(item.id),
    createCell(buildCallerName(item)),
    buildImageCell(item),
    createCell(buildContentSnippet(item)),
    createCell(formatUpdatedAt(item.updated_at)),
  ];
  if (allowActions) {
    cells.push(createActionsCell(handlers.onEdit, handlers.onDelete));
  }
  return createRow(cells);
}
