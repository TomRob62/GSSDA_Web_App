import { createLabel, createInput } from '../primitives.js';
import { createRoomDescriptionManager } from '../helpers/roomDescriptionManager.js';

function appendRoomNumber(form, data) {
  const wrapper = document.createElement('div');
  wrapper.className = 'room-form__section';
  wrapper.appendChild(createLabel('Room Number'));
  wrapper.appendChild(createInput({ type: 'text', name: 'room_number', value: data?.room_number || '' }));
  form.appendChild(wrapper);
}

function buildStaticToggle(form, data) {
  const wrapper = document.createElement('div');
  wrapper.style.display = 'flex';
  wrapper.style.alignItems = 'center';
  wrapper.style.gap = '8px';
  wrapper.id = 'staticToggle';

  const label = createLabel('Static');
  const selectId = 'staticSelect';
  label.htmlFor = selectId;

  const select = document.createElement('select');
  select.id = selectId;
  select.name = 'static';

  const optYes = document.createElement('option');
  optYes.value = 'yes';
  optYes.textContent = 'Yes';
  const optNo = document.createElement('option');
  optNo.value = 'no';
  optNo.textContent = 'No';
  select.appendChild(optYes);
  select.appendChild(optNo);

  const isStatic = data?.static ?? true;
  select.value = isStatic ? 'yes' : 'no';

  wrapper.appendChild(label);
  wrapper.appendChild(select);
  form.appendChild(wrapper);
  return select;
}

export function buildRoomsForm(form, data) {
  appendRoomNumber(form, data);
  const staticSelect = buildStaticToggle(form, data);
  const descriptionManager = createRoomDescriptionManager({ data });
  form.appendChild(descriptionManager.staticWrapper);
  form.appendChild(descriptionManager.dynamicWrapper);

  const retentionNotice = document.createElement('p');
  retentionNotice.className = 'room-form__hint';
  retentionNotice.textContent = 'Updates keep all linked events and MC assignments intact.';
  form.appendChild(retentionNotice);

  const initialIsStatic = staticSelect.value === 'yes';
  descriptionManager.setStaticMode(initialIsStatic);
  form.__descriptionManager = descriptionManager;

  staticSelect.addEventListener('change', () => {
    const isStatic = staticSelect.value === 'yes';
    descriptionManager.setStaticMode(isStatic);
  });
}
