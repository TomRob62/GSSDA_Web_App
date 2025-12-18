import { formatCallerNames } from '../state.js';

function formatTime(value) {
  return new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function classifyEvent(start, end) {
  const now = new Date();
  if (end < now) return 'is-past';
  if (start <= now && now <= end) return 'is-current';
  return 'is-upcoming';
}


function buildLine(event) {
  const line = document.createElement('div');
  line.className = 'queue-line';
  const caller = document.createElement('span');
  caller.className = 'caller';
  caller.textContent = formatCallerNames(event.caller_cuer_ids);
  line.appendChild(caller);

  const danceTypes = Array.isArray(event.dance_types) ? event.dance_types.filter(Boolean) : [];
  if (danceTypes.length) {
    const dance = document.createElement('span');
    dance.className = 'dance';
    dance.textContent = danceTypes.join(', ');
    line.appendChild(dance);
  }

  const timeSpan = document.createElement('span');
  timeSpan.className = 'time';
  timeSpan.textContent = `${formatTime(event.start)} – ${formatTime(event.end)}`;
  line.appendChild(timeSpan);

  return line;
}

function createEventItem(event, index) {
  const li = document.createElement('li');
  li.className = `queue-item ${classifyEvent(new Date(event.start), new Date(event.end))}`;
  const position = document.createElement('div');
  position.className = 'queue-index';
  position.textContent = index + 1;
  const content = document.createElement('div');
  content.className = 'queue-content';
  content.append(buildLine(event));
  li.append(position, content);
  return li;
}

export function renderEvents(eventList, events) {
  eventList.innerHTML = '';
  events.forEach((event, index) => {
    eventList.appendChild(createEventItem(event, index));
  });
}
