const REMOVE_FIELD_NAME = 'remove_image';
const DESCRIPTION_PLACEHOLDER = 'Description';

function appendIfPresent(formData, key, value) {
  if (value === undefined || value === null) return;
  if (typeof value === 'string' && value.trim() === '') return;
  formData.append(key, value);
}

function parseBoolean(value) {
  if (typeof value === 'boolean') return value;
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase();
    if (!normalized) return false;
    return ['true', '1', 'yes', 'on'].includes(normalized);
  }
  return Boolean(value);
}

function getFileFromForm(form) {
  const fileInput = form.querySelector('input[name="image_file"]');
  if (!fileInput || !fileInput.files || !fileInput.files.length) return null;
  return fileInput.files[0];
}

function shouldRemoveImage(form) {
  const removeInput = form.querySelector(`input[name="${REMOVE_FIELD_NAME}"]`);
  if (!removeInput) return false;
  if (removeInput.type === 'checkbox') return removeInput.checked;
  if (typeof removeInput.value === 'string') {
    return ['true', '1', 'yes', 'on'].includes(removeInput.value.toLowerCase());
  }
  return Boolean(removeInput.value);
}

export function createProfileFormData(form, payload) {
  const isAdvertisement = parseBoolean(payload.advertisement);
  const callerRaw = typeof payload.caller_cuer_id === 'string' ? payload.caller_cuer_id.trim() : payload.caller_cuer_id;
  const callerId = callerRaw ? Number(callerRaw) : NaN;
  const hasCaller = Number.isInteger(callerId) && callerId > 0;
  if (!isAdvertisement && !hasCaller) {
    throw new Error('Select a caller for the profile.');
  }

  const formData = new FormData();
  formData.append('advertisement', String(isAdvertisement));
  if (hasCaller) {
    formData.append('caller_cuer_id', String(callerId));
  }

  const rawContent = typeof payload.content === 'string' ? payload.content.trim() : '';
  const content = rawContent === DESCRIPTION_PLACEHOLDER ? '' : rawContent;
  appendIfPresent(formData, 'content', content);

  const file = getFileFromForm(form);
  if (file) {
    formData.append('image_file', file);
  }

  if (shouldRemoveImage(form)) {
    formData.append(REMOVE_FIELD_NAME, 'true');
  }

  return formData;
}
