function formatTimeRange(start, end) {
  const format = (value) => value.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  return `${format(start)} – ${format(end)}`;
}

function classify(start, end) {
  const now = new Date();
  if (end < now) return 'is-past';
  if (start <= now && now <= end) return 'is-current';
  return 'is-upcoming';
}

function buildEventContent(event) {
  const container = document.createElement('div');
  container.className = 'caller-event__content';
  // Order: caller -> time -> room -> dance
  const caller = document.createElement('div');
  caller.className = 'caller-event__caller';
  caller.textContent = event.callerNames;

  const time = document.createElement('div');
  time.className = 'caller-event__time';
  time.textContent = formatTimeRange(event.start, event.end);

  const room = document.createElement('div');
  room.className = 'caller-event__room';
  room.textContent = event.roomName;

  container.append(caller, time, room);

  if (event.danceText) {
    const dances = document.createElement('div');
    dances.className = 'caller-event__dances';
    dances.textContent = event.danceText;
    container.appendChild(dances);
  }
  return container;
}

function createEventItem(event) {
  const item = document.createElement('li');
  item.className = `caller-event ${classify(event.start, event.end)}`;
  item.dataset.start = event.start.toISOString();
  item.dataset.end = event.end.toISOString();
  item.appendChild(buildEventContent(event));
  return item;
}

export function renderEvents(listElement, events) {
  // Render events without inserting date dividers (presentation dividers removed for caller board)
  if (!listElement) return;
  listElement.innerHTML = '';
  events.forEach((event) => {
    listElement.appendChild(createEventItem(event));
  });
}

export function showLoadingState(listElement) {
  if (listElement) listElement.innerHTML = '';
}

export function showErrorState(listElement, message) {
  if (listElement) listElement.innerHTML = '';
  // Optionally could render an inline error item here; leaving list empty by design
}

export function showEmptyState(listElement) {
  if (listElement) listElement.innerHTML = '';
}

