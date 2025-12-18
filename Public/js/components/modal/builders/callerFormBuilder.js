import { createLabel, createInput } from '../primitives.js';

function appendNameFields(form, data) {
  form.appendChild(createLabel('First Name'));
  form.appendChild(createInput({ type: 'text', name: 'first_name', value: data?.first_name || '' }));
  form.appendChild(createLabel('Last Name'));
  form.appendChild(createInput({ type: 'text', name: 'last_name', value: data?.last_name || '' }));
  form.appendChild(createLabel('Suffix'));
  form.appendChild(createInput({ type: 'text', name: 'suffix', value: data?.suffix || '' }));
}

function appendMcToggle(form, data) {
  const wrapper = document.createElement('div');
  wrapper.style.display = 'flex';
  wrapper.style.alignItems = 'center';
  wrapper.style.gap = '8px';

  const label = createLabel('MC');
  const selectId = 'mcSelect';
  label.htmlFor = selectId;

  const select = document.createElement('select');
  select.id = selectId;
  select.name = 'mc';
  const optYes = document.createElement('option');
  optYes.value = 'yes';
  optYes.textContent = 'Yes';
  const optNo = document.createElement('option');
  optNo.value = 'no';
  optNo.textContent = 'No';
  select.appendChild(optYes);
  select.appendChild(optNo);

  select.value = data?.mc ? 'yes' : 'no';

  wrapper.appendChild(label);
  wrapper.appendChild(select);
  form.appendChild(wrapper);
  return select;
}

function appendDanceTypes(form, data) {
  const value = (data?.dance_types || []).join(', ');
  form.appendChild(createLabel('Dance Types (comma separated)'));
  form.appendChild(createInput({ type: 'text', name: 'dance_types', value }));
}

export function buildCallerForm(form, data) {
  appendNameFields(form, data);
  appendMcToggle(form, data);
  appendDanceTypes(form, data);
}
