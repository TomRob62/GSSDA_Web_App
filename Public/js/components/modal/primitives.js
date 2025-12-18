export function createLabel(text) {
  const label = document.createElement('label');
  label.textContent = text;
  return label;
}

export function createInput({ type, name, value = '', id }) {
  const input = document.createElement('input');
  input.type = type;
  input.name = name;
  if (id) input.id = id;
  input.value = value;
  return input;
}

export function createTextarea({ name, value = '', rows = 6, placeholder = '' }) {
  const textarea = document.createElement('textarea');
  textarea.name = name;
  textarea.rows = rows;
  textarea.value = value;
  if (placeholder) {
    textarea.placeholder = placeholder;
  }
  return textarea;
}

export function createCheckbox({ id, label, checked }) {
  const wrapper = document.createElement('div');
  wrapper.style.display = 'flex';
  wrapper.style.alignItems = 'center';
  wrapper.style.gap = '8px';

  const input = document.createElement('input');
  input.type = 'checkbox';
  if (id) input.id = id;
  input.checked = Boolean(checked);

  const text = document.createElement('label');
  text.textContent = label;

  wrapper.appendChild(input);
  wrapper.appendChild(text);
  return { wrapper, input };
}

export function createDurationPicker(name, selectedMinutes, normalizeDuration) {
  const container = document.createElement('div');
  container.className = 'duration-picker';

  const hoursSelect = document.createElement('select');
  hoursSelect.name = `${name}_hours`;
  hoursSelect.className = 'duration-hours';
  for (let h = 0; h <= 23; h += 1) {
    const option = document.createElement('option');
    option.value = String(h);
    option.textContent = `${h} h`;
    hoursSelect.appendChild(option);
  }

  const minutesSelect = document.createElement('select');
  minutesSelect.name = `${name}_minutes`;
  minutesSelect.className = 'duration-minutes';
  for (let m = 0; m < 60; m += 5) {
    const option = document.createElement('option');
    option.value = String(m);
    option.textContent = `${m.toString().padStart(2, '0')} m`;
    minutesSelect.appendChild(option);
  }

  const normalized = normalizeDuration(selectedMinutes);
  const hours = Math.floor(normalized / 60);
  const minutes = normalized % 60;
  hoursSelect.value = String(Math.min(23, Math.max(0, hours)));
  minutesSelect.value = String(Math.min(55, Math.max(0, Math.round(minutes / 5) * 5)));

  const flex = document.createElement('div');
  flex.style.display = 'flex';
  flex.style.gap = '8px';
  flex.style.alignItems = 'center';
  flex.appendChild(hoursSelect);
  flex.appendChild(minutesSelect);

  container.appendChild(flex);
  return container;
}
