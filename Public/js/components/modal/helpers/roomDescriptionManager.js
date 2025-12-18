import { createLabel, createInput } from '../primitives.js';

function formatDateTimeLabel(value) {
  if (!value) return '';
  try {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '';
    return date.toLocaleString();
  } catch (error) {
    return '';
  }
}

function buildChip(entry, onRemove) {
  const chip = document.createElement('div');
  chip.className = 'description-chip';
  chip.dataset.descriptionEntry = 'true';
  chip.dataset.description = entry.description || '';
  chip.dataset.startTime = entry.start_time || '';
  chip.dataset.endTime = entry.end_time || '';

  const label = document.createElement('span');
  const rangeLabel = `${formatDateTimeLabel(entry.start_time)} – ${formatDateTimeLabel(entry.end_time)}`.trim();
  const textParts = [];
  if (rangeLabel.trim() !== '–') textParts.push(rangeLabel);
  if (entry.description) textParts.push(entry.description);
  label.textContent = textParts.join(' | ');

  const removeBtn = document.createElement('button');
  removeBtn.type = 'button';
  removeBtn.className = 'description-chip__remove';
  removeBtn.textContent = '×';
  removeBtn.title = 'Remove description';
  removeBtn.addEventListener('click', () => onRemove(entry));

  chip.appendChild(label);
  chip.appendChild(removeBtn);
  return chip;
}

function createDescriptionModal(onSubmit) {
  const overlay = document.createElement('div');
  overlay.className = 'nested-modal-overlay';
  overlay.style.display = 'none';

  const modal = document.createElement('div');
  modal.className = 'nested-modal';

  const title = document.createElement('h3');
  title.textContent = 'Add Room Description';
  modal.appendChild(title);

  const form = document.createElement('form');
  form.className = 'nested-modal__form';

  const descriptionLabel = createLabel('Description');
  descriptionLabel.htmlFor = 'roomDescriptionText';
  const descriptionInput = createInput({ type: 'text', name: 'roomDescriptionText', id: 'roomDescriptionText' });

  const startLabel = createLabel('Start time');
  startLabel.htmlFor = 'roomDescriptionStart';
  const startInput = createInput({ type: 'datetime-local', name: 'roomDescriptionStart', id: 'roomDescriptionStart' });

  const endLabel = createLabel('End time');
  endLabel.htmlFor = 'roomDescriptionEnd';
  const endInput = createInput({ type: 'datetime-local', name: 'roomDescriptionEnd', id: 'roomDescriptionEnd' });

  const errorEl = document.createElement('p');
  errorEl.className = 'form-error-message';

  const actions = document.createElement('div');
  actions.className = 'nested-modal__actions';

  const cancelBtn = document.createElement('button');
  cancelBtn.type = 'button';
  cancelBtn.textContent = 'Cancel';
  cancelBtn.className = 'secondary';

  const submitBtn = document.createElement('button');
  submitBtn.type = 'submit';
  submitBtn.textContent = 'Save description';
  submitBtn.className = 'primary';

  actions.appendChild(cancelBtn);
  actions.appendChild(submitBtn);

  form.appendChild(descriptionLabel);
  form.appendChild(descriptionInput);
  form.appendChild(startLabel);
  form.appendChild(startInput);
  form.appendChild(endLabel);
  form.appendChild(endInput);
  form.appendChild(errorEl);
  form.appendChild(actions);

  modal.appendChild(form);
  overlay.appendChild(modal);
  document.body.appendChild(overlay);

  function close() {
    overlay.style.display = 'none';
    errorEl.textContent = '';
    descriptionInput.value = '';
    startInput.value = '';
    endInput.value = '';
  }

  cancelBtn.addEventListener('click', () => {
    close();
  });

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const description = descriptionInput.value.trim();
    const startValue = startInput.value;
    const endValue = endInput.value;
    const result = onSubmit({ description, startValue, endValue, setError: (message) => { errorEl.textContent = message; } });
    if (result !== false) {
      close();
    }
  });

  function open() {
    overlay.style.display = 'flex';
    descriptionInput.focus();
  }

  return { open, close, setError: (message) => { errorEl.textContent = message; } };
}

export function createRoomDescriptionManager({ data }) {
  const containerStatic = document.createElement('div');
  containerStatic.className = 'room-form__section';
  const staticLabel = createLabel('Description');
  staticLabel.htmlFor = 'staticRoomDescription';
  const staticInput = createInput({ type: 'text', name: 'static_description', id: 'staticRoomDescription' });
  if (data?.static && data.descriptions?.length) {
    staticInput.value = data.descriptions[0]?.description || '';
  }
  containerStatic.appendChild(staticLabel);
  containerStatic.appendChild(staticInput);
  const staticErrorEl = document.createElement('p');
  staticErrorEl.className = 'form-error-message';
  containerStatic.appendChild(staticErrorEl);

  const containerDynamic = document.createElement('div');
  containerDynamic.className = 'room-form__section room-form__section--descriptions';

  const header = document.createElement('div');
  header.className = 'room-form__section-header';
  const listLabel = createLabel('Descriptions');
  listLabel.classList.add('room-form__section-title');
  const addBtn = document.createElement('button');
  addBtn.type = 'button';
  addBtn.className = 'primary';
  addBtn.textContent = 'Add description';
  header.appendChild(listLabel);
  header.appendChild(addBtn);

  const hint = document.createElement('p');
  hint.className = 'room-form__hint';
  hint.textContent = 'Provide time-bound descriptions for the room. Each description must end before the next one begins.';

  const dynamicErrorEl = document.createElement('p');
  dynamicErrorEl.className = 'form-error-message';

  const list = document.createElement('div');
  list.className = 'description-chip-list';

  containerDynamic.appendChild(header);
  containerDynamic.appendChild(hint);
  containerDynamic.appendChild(dynamicErrorEl);
  containerDynamic.appendChild(list);

  const entries = [];
  let currentIsStatic = false;

  function sortEntries() {
    entries.sort((a, b) => {
      const startA = a.start_time ? new Date(a.start_time).getTime() : 0;
      const startB = b.start_time ? new Date(b.start_time).getTime() : 0;
      return startA - startB;
    });
  }

  function renderEntries() {
    list.innerHTML = '';
    if (!entries.length) {
      const empty = document.createElement('p');
      empty.className = 'room-form__empty';
      empty.textContent = 'No descriptions have been added yet.';
      list.appendChild(empty);
      return;
    }
    entries.forEach((entry) => {
      const chip = buildChip(entry, (target) => {
        const index = entries.findIndex((item) => item === target);
        if (index !== -1) {
          entries.splice(index, 1);
          renderEntries();
        }
      });
      list.appendChild(chip);
    });
  }

  function setDynamicError(message) {
    dynamicErrorEl.textContent = message || '';
  }

  function setStaticError(message) {
    staticErrorEl.textContent = message || '';
  }

  function validateEntry({ description, startISO, endISO }) {
    if (!description) {
      return 'Please provide a description.';
    }
    if (!startISO || !endISO) {
      return 'Start and end times are required.';
    }
    const startDate = new Date(startISO);
    const endDate = new Date(endISO);
    if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
      return 'Start and end times must be valid dates.';
    }
    if (endDate <= startDate) {
      return 'The end time must be later than the start time.';
    }
    const hasOverlap = entries.some((existing) => {
      if (!existing.start_time || !existing.end_time) return false;
      const existingStart = new Date(existing.start_time).getTime();
      const existingEnd = new Date(existing.end_time).getTime();
      const overlapStart = Math.max(existingStart, startDate.getTime());
      const overlapEnd = Math.min(existingEnd, endDate.getTime());
      return overlapEnd > overlapStart;
    });
    if (hasOverlap) {
      return 'Description times cannot overlap. Ensure each description ends before the next begins.';
    }
    return null;
  }

  function addEntry({ description, startValue, endValue }) {
    const startISO = startValue ? new Date(startValue).toISOString() : null;
    const endISO = endValue ? new Date(endValue).toISOString() : null;
    const error = validateEntry({ description, startISO, endISO });
    if (error) {
      setDynamicError(error);
      return { success: false, error };
    }
    setDynamicError('');
    entries.push({ description, start_time: startISO, end_time: endISO });
    sortEntries();
    renderEntries();
    return { success: true };
  }

  const modal = createDescriptionModal(({ description, startValue, endValue, setError: setModalError }) => {
    const result = addEntry({ description, startValue, endValue });
    if (!result.success) {
      setModalError(result.error);
      return false;
    }
    return true;
  });

  addBtn.addEventListener('click', () => {
    setDynamicError('');
    modal.open();
  });

  function setStaticMode(isStatic) {
    currentIsStatic = isStatic;
    containerStatic.style.display = isStatic ? 'block' : 'none';
    containerDynamic.style.display = isStatic ? 'none' : 'block';
    if (isStatic) {
      setDynamicError('');
      return;
    }
    setStaticError('');
  }

  function getStaticDescription() {
    return staticInput.value.trim();
  }

  function getEntries() {
    return entries.map((entry) => ({
      description: entry.description,
      start_time: entry.start_time,
      end_time: entry.end_time,
    }));
  }

  function showError(message) {
    if (currentIsStatic) {
      setStaticError(message);
      return;
    }
    setDynamicError(message);
  }

  function clearError() {
    setStaticError('');
    setDynamicError('');
  }

  if (Array.isArray(data?.descriptions) && data.descriptions.length) {
    const editableEntries = data.descriptions.filter((item) => item.start_time && item.end_time);
    editableEntries.forEach((item) => {
      entries.push({
        description: item.description || '',
        start_time: item.start_time,
        end_time: item.end_time,
      });
    });
    sortEntries();
    renderEntries();
  } else {
    renderEntries();
  }

  return {
    staticWrapper: containerStatic,
    dynamicWrapper: containerDynamic,
    setStaticMode,
    getStaticDescription,
    getEntries,
    showError,
    clearError,
    modal,
  };
}
