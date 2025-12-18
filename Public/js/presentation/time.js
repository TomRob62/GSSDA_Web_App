function formatClock(now) {
  // Display hours and minutes only (we still update every second for accuracy)
  const display = now.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  return display.replace(/\s+/g, '').toLowerCase();
}

export function startClock(element) {
  function update() {
    element.textContent = formatClock(new Date());
  }
  update();
  // Update every second for a live clock
  return setInterval(update, 1000);
}

export function stopClock(timerId) {
  if (timerId) clearInterval(timerId);
}
