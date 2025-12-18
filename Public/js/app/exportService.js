import { authHeaders } from '../components/api.js';
import { buildQueryString } from './queryBuilder.js';

export const FORMAT_CONFIG = {
  pdf: {
    endpoint: '/api/export',
    accept: 'application/pdf',
    extension: 'pdf',
    label: 'PDF',
    successMessage: 'PDF export ready. Downloading…',
  },
  excel: {
    endpoint: '/api/export/excel',
    accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    extension: 'xlsx',
    label: 'Excel',
    successMessage: 'Excel export ready. Downloading…',
  },
};

function parseFilename(disposition, fallback) {
  if (!disposition) return fallback;
  const match = /filename\*=UTF-8''([^;]+)|filename="?([^";]+)"?/i.exec(disposition);
  if (match) {
    const value = match[1] || match[2];
    try {
      return decodeURIComponent(value);
    } catch (err) {
      return value;
    }
  }
  return fallback;
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export async function requestExport(elements, filterController, formatKey) {
  const format = FORMAT_CONFIG[formatKey];
  if (!format) {
    throw new Error('Unsupported export format.');
  }

  const query = buildQueryString(elements, filterController);
  const url = `${format.endpoint}?${query}`;
  let response;
  try {
    response = await fetch(url, {
      headers: authHeaders({ Accept: format.accept }),
    });
  } catch (err) {
    throw new Error('Unable to reach the server to create the export.');
  }

  if (!response.ok) {
    let message = 'Failed to create export.';
    try {
      const data = await response.json();
      message = data?.error?.message || message;
    } catch (error) {
      // ignore JSON parse errors
    }
    throw new Error(message);
  }

  const blob = await response.blob();
  const fallback = `${elements.getActiveView()}-export.${format.extension}`;
  const filename = parseFilename(response.headers.get('Content-Disposition'), fallback);
  triggerDownload(blob, filename);
  return format.successMessage;
}

