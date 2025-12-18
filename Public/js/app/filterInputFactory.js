import { getRooms, getCallers, getMcCallers, getEventDays } from './state.js';

function buildBooleanSelect() {
  const select = document.createElement('select');
  select.appendChild(new Option('-- Any --', ''));
  select.appendChild(new Option('Yes', 'true'));
  select.appendChild(new Option('No', 'false'));
  return select;
}

function buildTextInput() {
  const input = document.createElement('input');
  input.type = 'text';
  input.placeholder = 'Enter value';
  return input;
}

function buildNumberInput() {
  const input = document.createElement('input');
  input.type = 'number';
  input.placeholder = 'Enter number';
  return input;
}

function buildDateTimeInput() {
  const input = document.createElement('input');
  input.type = 'datetime-local';
  return input;
}

function buildSelect(options, getLabel) {
  const select = document.createElement('select');
  select.appendChild(new Option('-- Select --', ''));
  options
    .slice()
    .sort((a, b) => getLabel(a).localeCompare(getLabel(b)))
    .forEach((item) => {
      select.appendChild(new Option(getLabel(item), item.id));
    });
  return select;
}

function buildMultiDaySelect() {
  const select = document.createElement('select');
  select.multiple = true;
  select.classList.add('filter-input--multiselect');

  const days = getEventDays();
  if (!days.length) {
    const placeholder = new Option('No days available', '');
    placeholder.disabled = true;
    select.appendChild(placeholder);
    select.disabled = true;
    select.size = 1;
    return select;
  }

  days
    .slice()
    .sort((a, b) => {
      const left = a.first_start || '';
      const right = b.first_start || '';
      if (left !== right) return left.localeCompare(right);
      const leftKey = a.day_key || a.value || '';
      const rightKey = b.day_key || b.value || '';
      return leftKey.localeCompare(rightKey);
    })
    .forEach((day) => {
      // Compute a user-friendly, localized label from the server-provided first_start.
      // Fall back to the server-provided label or value if first_start isn't present.
      let localLabel = day.label || day.value || '';
      if (day.first_start) {
        try {
          const dt = new Date(day.first_start);
          // Use numeric month/day and include year so the user sees the correct calendar day in their locale
          localLabel = dt.toLocaleDateString(undefined, { month: 'numeric', day: 'numeric', year: 'numeric' });
        } catch (e) {
          // keep the fallback label if parsing/formatting fails
        }
      }

      const option = new Option(localLabel, day.value);
      option.dataset.dayKey = day.day_key || '';
      option.dataset.count = typeof day.count === 'number' ? String(day.count) : '';
      select.appendChild(option);
    });

  select.size = Math.min(6, Math.max(3, days.length));

  return select;
}

export function createFilterInput(definition) {
  if (!definition || definition.type === 'none') return null;
  if (definition.type === 'boolean') return buildBooleanSelect();
  if (definition.type === 'text') return buildTextInput();
  if (definition.type === 'number') return buildNumberInput();
  if (definition.type === 'datetime') return buildDateTimeInput();
  if (definition.type === 'select-room') return buildSelect(getRooms(), (room) => room.room_number);
  if (definition.type === 'select-mc') return buildSelect(getMcCallers(), (caller) => `${caller.first_name} ${caller.last_name}`);
  if (definition.type === 'select-caller') return buildSelect(getCallers(), (caller) => `${caller.first_name} ${caller.last_name}`);
  if (definition.type === 'multi-day') return buildMultiDaySelect();
  return null;
}
