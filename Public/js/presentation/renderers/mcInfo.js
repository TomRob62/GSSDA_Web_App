import { findCallerName } from '../state.js';

function formatTime(value) {
  return new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }).replace(/\s+/g, '').toLowerCase();
}

function buildLine(prefix, mc) {
  if (!mc) return `${prefix}: None`;
  return `${prefix}: ${findCallerName(mc.caller_cuer_id)} | ${formatTime(mc.start)} - ${formatTime(mc.end)}`;
}

export function renderMcInfo(container, currentMc, nextMc) {
  container.innerHTML = '';
  const wrapper = document.createElement('div');
  wrapper.className = 'presentation-mcs';
  const current = document.createElement('div');
  current.className = 'presentation-mcs-current';
  current.textContent = buildLine('Current MC', currentMc);
  const upcoming = document.createElement('div');
  upcoming.className = 'presentation-mcs-next';
  upcoming.textContent = buildLine('Next MC', nextMc);
  wrapper.append(current, upcoming);
  container.appendChild(wrapper);
}
