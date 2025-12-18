import { createLabel, createInput, createDurationPicker } from '../primitives.js';

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

function appendMcSelect(form, callers, data) {
  form.appendChild(createLabel('MC'));
  const select = document.createElement('select');
  select.name = 'caller_cuer_id';
  callers
    .filter((caller) => caller.mc)
    .forEach((caller) => {
      const option = document.createElement('option');
      option.value = caller.id;
      option.textContent = `${caller.first_name} ${caller.last_name}`;
      option.selected = data?.caller_cuer_id === caller.id;
      select.appendChild(option);
    });
  form.appendChild(select);
}

function appendTimingFields(form, data, utils) {
  form.appendChild(createLabel('Start Time'));
  form.appendChild(createInput({ type: 'datetime-local', name: 'start', value: utils.toLocalDateTime(data?.start) }));
  const duration = data?.start && data?.end ? utils.calculateDurationMinutes(data.start, data.end) : 10;
  form.appendChild(createLabel('Duration'));
  form.appendChild(createDurationPicker('duration', duration, utils.normalizeDuration));
}

export function buildMcForm(form, data, caches, utils) {
  appendRoomSelect(form, caches.rooms, data);
  appendMcSelect(form, caches.callers, data);
  appendTimingFields(form, data, utils);
}
