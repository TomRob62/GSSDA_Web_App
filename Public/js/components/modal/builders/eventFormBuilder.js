import { createLabel, createInput, createDurationPicker } from '../primitives.js';
import { createCallerMultiSelect } from '../callerMultiSelect.js';

function appendRoomSelect(form, rooms, data) {
  form.appendChild(createLabel('Room'));
  const select = document.createElement('select');
  select.name = 'room_id';
  rooms.forEach((room) => {
    const option = document.createElement('option');
    option.value = room.id;
    option.textContent = room.room_number;
    option.selected = data?.room_id === room.id;
    select.appendChild(option);
  });
  form.appendChild(select);
}

function appendCallerSelector(form, callers, data) {
  form.appendChild(createLabel('Caller/Cuer(s)'));
  const selector = createCallerMultiSelect({
    callers,
    selectedIds: data?.caller_cuer_ids || [],
  });
  form.appendChild(selector);
}

function appendTimingFields(form, data, utils) {
  form.appendChild(createLabel('Start Time'));
  form.appendChild(createInput({ type: 'datetime-local', name: 'start', value: utils.toLocalDateTime(data?.start) }));
  const duration = data?.start && data?.end ? utils.calculateDurationMinutes(data.start, data.end) : 10;
  form.appendChild(createLabel('Duration'));
  form.appendChild(createDurationPicker('duration', duration, utils.normalizeDuration));
}

function appendDanceTypes(form, data) {
  const value = (data?.dance_types || []).join(', ');
  form.appendChild(createLabel('Dance Types (comma separated)'));
  form.appendChild(createInput({ type: 'text', name: 'dance_types', value }));
}

export function buildEventForm(form, data, caches, utils) {
  appendRoomSelect(form, caches.rooms, data);
  appendCallerSelector(form, caches.callers, data);
  appendTimingFields(form, data, utils);
  appendDanceTypes(form, data);
}
