function renderPlaceholder(list, message) {
  list.innerHTML = '';
  const item = document.createElement('li');
  item.className = 'queue-item queue-empty';
  item.textContent = message;
  list.appendChild(item);
}

export function showLoadingState({ roomTitle, mcInfo, eventList }) {
  roomTitle.textContent = 'Loading…';
  mcInfo.textContent = 'Loading MC information…';
  renderPlaceholder(eventList, 'Loading events…');
}

export function renderSelectionPrompt({ roomTitle, mcInfo, eventList }) {
  roomTitle.textContent = 'Select a room';
  mcInfo.textContent = '';
  renderPlaceholder(eventList, 'Select a room to view its full schedule.');
}

export function renderErrorState({ mcInfo, eventList }) {
  mcInfo.textContent = 'Unable to load MC information';
  renderPlaceholder(eventList, 'Unable to load events for this room.');
}

export function renderEmptySchedule(eventList) {
  renderPlaceholder(eventList, 'No scheduled events for this room.');
}
