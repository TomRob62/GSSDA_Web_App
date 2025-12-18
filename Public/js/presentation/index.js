import { ensureAuthenticated, registerLogout } from '../app/auth.js';
import {
  loadRooms,
  loadCallers,
  loadEvents,
  loadMcs,
  loadProfiles,
  loadAdvertisementProfiles,
} from './dataService.js';
import { setRooms, setCallers, setProfiles, getRooms, getStoredRoom, storeRoom } from './state.js';
import { populateRoomSelect, renderSchedule, showLoadingState, renderSelectionPrompt, renderErrorState } from './renderers/index.js';
import { startClock } from './time.js';
import { setupFullscreen } from './fullscreen.js';
import { createSessionManager } from '../app/session.js';
import { applyRoleVisibility } from '../components/navVisibility.js';
import { createProfilePresenter } from './profile/manager.js';

const elements = {
  roomSelect: document.getElementById('roomSelect'),
  roomTitle: document.getElementById('roomTitle'),
  roomDescription: document.getElementById('roomDescription'),
  mcInfo: document.getElementById('mcInfo'),
  currentTime: document.getElementById('currentTime'),
  eventList: document.getElementById('eventQueue'),
  fullscreenBtn: document.getElementById('fullscreenBtn'),
  logoutLink: document.getElementById('logoutLink'),
  profilePanel: document.getElementById('profilePanel'),
  profileImage: document.getElementById('profileImage'),
  profileImageWrapper: document.getElementById('profileImageWrapper'),
  profileCallerName: document.getElementById('profileCallerName'),
  profileContentWrapper: document.getElementById('profileContentWrapper'),
  profileContent: document.getElementById('profileContent'),
  presentationContainer: document.getElementById('presentationContainer'),
  adsToggle: document.getElementById('adsToggle'),
  callersToggle: document.getElementById('callersToggle'),
  lockToggle: document.getElementById('lockToggle'),
};

if (!ensureAuthenticated()) {
  throw new Error('Authentication required');
}

const sessionManager = createSessionManager();

function sortEvents(events) {
  return events.slice().sort((a, b) => new Date(a.start) - new Date(b.start));
}

function splitMcAssignments(mcs) {
  const now = new Date();
  const current = mcs.find((mc) => new Date(mc.start) <= now && now <= new Date(mc.end)) || null;
  const upcoming = mcs
    .map((mc) => ({ ...mc, startDate: new Date(mc.start) }))
    .filter((mc) => mc.startDate > now)
    .sort((a, b) => a.startDate - b.startDate);
  return { current, next: upcoming[0] || null };
}

function findActiveEvent(events) {
  if (!Array.isArray(events) || !events.length) {
    return null;
  }
  const now = new Date();
  return (
    events.find((event) => {
      if (!event) return false;
      const start = event.start ? new Date(event.start) : null;
      const end = event.end ? new Date(event.end) : null;
      if (!start) return false;
      if (!end) return start <= now;
      return start <= now && now <= end;
    }) || null
  );
}

const profilePresenter = createProfilePresenter(elements);

const REFRESH_INTERVAL_STANDARD = 60000;
const REFRESH_INTERVAL_FAST = 15000;
const ADDITIONAL_AUTO_REFRESH_ATTEMPTS = 3;
const MAX_SCHEDULE_LOAD_ATTEMPTS = 1 + ADDITIONAL_AUTO_REFRESH_ATTEMPTS;

let lastProfileRefresh = 0;
let lastActiveCallerIds = [];
let lastHasActiveProfile = false;

const scheduleCache = new Map();

const autoRefreshController = {
  timerId: null,
  intervalMs: REFRESH_INTERVAL_STANDARD,
};

const autoRefreshExecution = {
  activeCount: 0,
  skippedCount: 0,
};

function stopAutoRefresh() {
  if (autoRefreshController.timerId) {
    clearInterval(autoRefreshController.timerId);
    autoRefreshController.timerId = null;
  }
}

function startAutoRefresh() {
  stopAutoRefresh();
  autoRefreshController.timerId = setInterval(() => {
    void handleAutoRefresh();
  }, autoRefreshController.intervalMs);
}

function setAutoRefreshInterval(intervalMs) {
  if (autoRefreshController.intervalMs === intervalMs && autoRefreshController.timerId) {
    return;
  }
  autoRefreshController.intervalMs = intervalMs;
  startAutoRefresh();
}

function computeHasActiveProfile(callerIds) {
  if (!Array.isArray(callerIds) || callerIds.length === 0) {
    return false;
  }
  return callerIds.some((id) => profilePresenter.hasProfileForCaller(id));
}

function recomputeActiveProfileState() {
  const hasActiveProfile = computeHasActiveProfile(lastActiveCallerIds);
  if (hasActiveProfile !== lastHasActiveProfile) {
    lastHasActiveProfile = hasActiveProfile;
    updateAutoRefreshInterval();
  }
}

function updateAutoRefreshInterval() {
  const options = profilePresenter.getOptions();
  const rotationEnabled = Boolean(options.showCallers || options.showAdvertisements);
  const needsFastInterval = rotationEnabled && !lastHasActiveProfile;
  setAutoRefreshInterval(needsFastInterval ? REFRESH_INTERVAL_FAST : REFRESH_INTERVAL_STANDARD);
}

function updateProfileDisplayOptions() {
  const showAdvertisements = elements.adsToggle ? elements.adsToggle.checked : false;
  const showCallers = elements.callersToggle ? elements.callersToggle.checked : false;
  const lockActive = elements.lockToggle ? elements.lockToggle.checked : false;

  profilePresenter.setOptions({
    showAdvertisements,
    showCallers,
    lockActive,
  });

  if (elements.presentationContainer) {
    elements.presentationContainer.classList.toggle('queue-enabled', showAdvertisements || showCallers);
  }
}

function logScheduleLoadError(error, attempt) {
  if (attempt === 1) {
    console.error('Initial schedule load failed', error);
    return;
  }
  console.error(`Schedule load attempt ${attempt} failed`, error);
}

function handleScheduleLoadFailure({ silent, attempt, error }) {
  logScheduleLoadError(error, attempt);
  if (!silent) {
    renderErrorState(elements);
  }
  lastHasActiveProfile = false;
  return attempt < MAX_SCHEDULE_LOAD_ATTEMPTS;
}

async function refreshProfiles() {
  try {
    const [profiles, advertisements] = await Promise.all([
      loadProfiles(),
      loadAdvertisementProfiles(),
    ]);
    setProfiles(profiles, advertisements);
    profilePresenter.setProfiles(profiles, advertisements);
    lastProfileRefresh = Date.now();
    recomputeActiveProfileState();
  } catch (error) {
    console.error('Failed to load profiles', error);
  }
}

async function refreshCaches() {
  try {
    const [rooms, callers, profiles, advertisements] = await Promise.all([
      loadRooms(),
      loadCallers(),
      loadProfiles(),
      loadAdvertisementProfiles(),
    ]);
    setRooms(rooms);
    setCallers(callers);
    setProfiles(profiles, advertisements);
    profilePresenter.setProfiles(profiles, advertisements);
    lastProfileRefresh = Date.now();
    populateRoomSelect(elements.roomSelect, getRooms());
    recomputeActiveProfileState();
  } catch (error) {
    console.error('Failed to load lookup data', error);
  }
}

async function fetchScheduleData(roomId) {
  const [events, mcs] = await Promise.all([loadEvents(roomId), loadMcs(roomId)]);
  const sortedEvents = sortEvents(events);
  const data = { events: sortedEvents, mcs, fetchedAt: Date.now() };
  scheduleCache.set(roomId, data);
  return data;
}

async function getScheduleData(roomId, { refresh = true } = {}) {
  if (!refresh) {
    return scheduleCache.get(roomId) || null;
  }
  return fetchScheduleData(roomId);
}

async function loadSchedule(
  roomId,
  { refresh = true, silent = false, attempt = 1 } = {}
) {
  if (!roomId) {
    renderSelectionPrompt(elements);
    profilePresenter.updateActiveContext({ callerIds: [], eventId: null });
    lastActiveCallerIds = [];
    lastHasActiveProfile = false;
    stopAutoRefresh();
    return;
  }

  let scheduleData = null;
  let currentAttempt = attempt;
  let currentSilent = silent;
  let currentRefresh = refresh;

  while (currentAttempt <= MAX_SCHEDULE_LOAD_ATTEMPTS && !scheduleData) {
    if (!currentSilent && currentRefresh) {
      showLoadingState(elements);
    }

    try {
      scheduleData = await getScheduleData(roomId, { refresh: currentRefresh });
      if (!scheduleData) {
        if (!currentSilent) {
          showLoadingState(elements);
        }
        scheduleData = await fetchScheduleData(roomId);
      }
    } catch (error) {
      const shouldRetry = handleScheduleLoadFailure({
        silent: currentSilent,
        attempt: currentAttempt,
        error,
      });

      if (!shouldRetry) {
        lastActiveCallerIds = [];
        lastHasActiveProfile = false;
        updateAutoRefreshInterval();
        return;
      }

      currentAttempt += 1;
      currentSilent = true;
      currentRefresh = true;
      scheduleData = null;
    }
  }

  if (!scheduleData) {
    lastActiveCallerIds = [];
    lastHasActiveProfile = false;
    updateAutoRefreshInterval();
    return;
  }

  const { events, mcs } = scheduleData;
  const { current, next } = splitMcAssignments(mcs);
  const room = getRooms().find((item) => item.id === Number(roomId));
  renderSchedule(elements, room, events, current, next);
  const activeEvent = findActiveEvent(events);
  const activeCallerIds = Array.isArray(activeEvent?.caller_cuer_ids)
    ? activeEvent.caller_cuer_ids
    : [];
  const normalizedActiveCallerIds = activeCallerIds
    .map((id) => (typeof id === 'number' ? id : Number(id)))
    .filter((id) => Number.isInteger(id));

  lastActiveCallerIds = normalizedActiveCallerIds;
  lastHasActiveProfile = computeHasActiveProfile(normalizedActiveCallerIds);
  updateAutoRefreshInterval();
  profilePresenter.updateActiveContext({
    callerIds: normalizedActiveCallerIds,
    eventId: activeEvent ? activeEvent.id || null : null,
    startsAt: activeEvent ? activeEvent.start || null : null,
    endsAt: activeEvent ? activeEvent.end || null : null,
  });
  profilePresenter.refreshScroll();
}

elements.roomSelect.addEventListener('change', (event) => {
  const roomId = event.target.value;
  storeRoom(roomId);
  void loadSchedule(roomId, { refresh: true, silent: false });
});

async function refreshPresentationView({ refresh = true, silent = false } = {}) {
  updateProfileDisplayOptions();
  const roomId = elements.roomSelect ? elements.roomSelect.value : null;
  await loadSchedule(roomId || null, { refresh, silent });
}

async function handleAutoRefresh() {
  if (autoRefreshExecution.activeCount > 0) {
    autoRefreshExecution.skippedCount += 1;
    if (autoRefreshExecution.skippedCount > 4) {
      console.error(
        'Auto-refresh skipped more than 4 times because a previous refresh is still running. Please investigate network conditions or manually reload the presentation.'
      );
    }
    return;
  }

  autoRefreshExecution.activeCount += 1;
  const roomId = elements.roomSelect ? elements.roomSelect.value : null;
  try {
    if (roomId) {
      await loadSchedule(roomId, { refresh: true, silent: true });
    }
    if (Date.now() - lastProfileRefresh > 5 * 60 * 1000) {
      await refreshProfiles();
    }
    autoRefreshExecution.skippedCount = 0;
  } finally {
    autoRefreshExecution.activeCount = Math.max(0, autoRefreshExecution.activeCount - 1);
  }
}

async function initialize() {
  try {
    const user = await sessionManager.loadSession();
    applyRoleVisibility(user);
  } catch (error) {
    console.error('Unable to load session', error);
    localStorage.removeItem('token');
    window.location.href = '/login';
    return;
  }

  registerLogout(elements.logoutLink);
  setupFullscreen(elements.fullscreenBtn);
  startClock(elements.currentTime);

  if (elements.adsToggle) {
    elements.adsToggle.addEventListener('change', () => {
      void refreshPresentationView({ refresh: false, silent: true });
    });
  }

  if (elements.callersToggle) {
    elements.callersToggle.addEventListener('change', () => {
      void refreshPresentationView({ refresh: false, silent: true });
    });
  }

  if (elements.lockToggle) {
    elements.lockToggle.addEventListener('change', () => {
      void refreshPresentationView({ refresh: false, silent: true });
    });
  }

  updateProfileDisplayOptions();

  await refreshCaches();
  const stored = getStoredRoom();
  if (stored && getRooms().some((room) => String(room.id) === stored)) {
    elements.roomSelect.value = stored;
    await loadSchedule(stored);
  } else {
    renderSelectionPrompt(elements);
  }
  window.addEventListener('resize', () => profilePresenter.refreshScroll());
}

initialize();
