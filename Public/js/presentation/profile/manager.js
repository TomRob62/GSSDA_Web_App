import { getProfileByCaller } from '../state.js';
import { renderProfile, clearProfile, syncScrolling } from './renderer.js';

const ROTATION_INTERVAL_MS = 15000;

function normalizeCallerId(value) {
  if (typeof value === 'number' && Number.isInteger(value)) {
    return value;
  }
  if (typeof value === 'string' && value.trim().length) {
    const parsed = Number(value);
    return Number.isInteger(parsed) ? parsed : null;
  }
  return null;
}

function buildAlternatingQueue(callers, advertisements) {
  if (!callers.length && !advertisements.length) {
    return [];
  }
  if (!callers.length) {
    return advertisements.slice();
  }
  if (!advertisements.length) {
    return callers.slice();
  }
  // Strategy B: build a queue of length max(callers, advertisements) * 2
  // by alternating caller -> advertisement and wrapping both arrays as
  // needed. This means when one list is shorter it will repeat to ensure
  // a strict alternation across the full pass.
  const queue = [];
  const maxLength = Math.max(callers.length, advertisements.length);
  for (let i = 0; i < maxLength; i += 1) {
    const callerProfile = callers[i % callers.length];
    const advertisementProfile = advertisements[i % advertisements.length];
    if (callerProfile) queue.push(callerProfile);
    if (advertisementProfile) queue.push(advertisementProfile);
  }
  return queue;
}

function preloadImageForProfile(profile) {
  if (!profile || !profile.image_path) {
    return;
  }
  const img = new Image();
  img.decoding = 'async';
  img.src = profile.image_path;
}

export function createProfilePresenter(elements) {
  const state = {
    callerProfiles: [],
    advertisementProfiles: [],
    profilesByCaller: new Map(),
    profilesById: new Map(),
    queue: [],
    queueIndex: -1,
    timerId: null,
    currentProfileId: null,
    currentSource: 'none',
    activeCallerIds: [],
    activeEventSignature: null,
    // Timestamp when an advertisement was last shown (ms since epoch)
    lastAdShownAt: null,
    // When we entered a locked active profile view
    lockedSince: null,
    // Temporary ad-override state: when true we'll show a small number of
    // advertisements even while a caller profile is locked.
    adOverrideActive: false,
    adOverrideRemaining: 0,
  };

  const options = {
    showCallers: true,
    showAdvertisements: true,
    lockActive: true,
  };

  function stopTimer() {
    if (state.timerId) {
      clearInterval(state.timerId);
      state.timerId = null;
    }
  }

  function startTimer() {
    if (state.timerId) {
      return;
    }
    state.timerId = setInterval(() => {
      handleTimerTick();
    }, ROTATION_INTERVAL_MS);
  }

  function ensureTimer() {
    const hasQueue = state.queue.length > 0 && (options.showCallers || options.showAdvertisements);
    if (hasQueue) {
      startTimer();
    } else {
      stopTimer();
    }
  }

  function computeQueue() {
    if (options.showCallers && options.showAdvertisements) {
      return buildAlternatingQueue(state.callerProfiles, state.advertisementProfiles);
    }
    if (options.showCallers) {
      return state.callerProfiles.slice();
    }
    if (options.showAdvertisements) {
      return state.advertisementProfiles.slice();
    }
    return [];
  }

  function rebuildQueue() {
    const queueProfileId = state.currentSource === 'queue' ? state.currentProfileId : null;
    const queue = computeQueue();
    state.queue = queue;
    if (queueProfileId !== null) {
      const preservedIndex = queue.findIndex((profile) => profile?.id === queueProfileId);
      state.queueIndex = preservedIndex >= 0 ? preservedIndex : -1;
    } else if (!queue.length) {
      state.queueIndex = -1;
    } else if (state.queueIndex >= queue.length) {
      state.queueIndex = queue.length - 1;
    }
    ensureTimer();
  }

  function resolveActiveProfile() {
    if (!state.activeCallerIds.length) {
      return null;
    }
    for (const callerId of state.activeCallerIds) {
      const profile = state.profilesByCaller.get(callerId) || getProfileByCaller(callerId);
      if (profile) {
        return profile;
      }
    }
    return null;
  }

  function handleNoProfile() {
    clearProfile(elements);
    state.currentProfileId = null;
    if (state.currentSource !== 'lock') {
      state.queueIndex = -1;
    }
    state.currentSource = 'none';
  }

  function showQueueProfile(index) {
    if (!state.queue.length) {
      handleNoProfile();
      return;
    }
    const safeIndex = ((index % state.queue.length) + state.queue.length) % state.queue.length;
    const profile = state.queue[safeIndex] || null;
    if (!profile) {
      handleNoProfile();
      return;
    }
  state.queueIndex = safeIndex;
  state.currentSource = 'queue';
  // We're showing from the queue, so clear any locked timestamp.
  state.lockedSince = null;
    state.currentProfileId = profile.id || null;
    renderProfile(elements, profile);
    syncScrolling(elements);
    preloadNextProfile();
    // Track when an ad is shown so we can enforce ad intervals during lock.
    if (profile && profile.advertisement) {
      state.lastAdShownAt = Date.now();
    }
  }

  function showNextAdvertisement() {
    if (!state.queue.length) return;
    // Find the next advertisement in the queue after the current index.
    const start = state.queueIndex >= 0 ? state.queueIndex : -1;
    for (let offset = 1; offset <= state.queue.length; offset += 1) {
      const idx = (start + offset) % state.queue.length;
      const candidate = state.queue[idx];
      if (candidate && candidate.advertisement) {
        showQueueProfile(idx);
        // decrement remaining override count and record the ad time
        state.adOverrideRemaining = Math.max(0, state.adOverrideRemaining - 1);
        state.lastAdShownAt = Date.now();
        return;
      }
    }
    // No advertisement found in queue; nothing to do.
  }

  function triggerAdOverride() {
    const AD_OVERRIDE_COUNT = 2; // show two ads
    if (state.adOverrideActive) return;
    if (!state.queue.length) return;
    // Only trigger if there is at least one advertisement in the queue
    const hasAd = state.queue.some((p) => p && p.advertisement);
    if (!hasAd) return;
    state.adOverrideActive = true;
    state.adOverrideRemaining = AD_OVERRIDE_COUNT;
    // Immediately show the first advertisement
    showNextAdvertisement();
  }

  function advanceQueue() {
    if (!state.queue.length) {
      handleNoProfile();
      return;
    }
    const baseIndex = state.queueIndex >= 0 ? state.queueIndex : -1;
    const nextIndex = state.queue.length === 1 ? 0 : (baseIndex + 1 + state.queue.length) % state.queue.length;
    showQueueProfile(nextIndex);
  }

  function getNextQueueProfile() {
    if (!state.queue.length) {
      return null;
    }
    if (state.queue.length === 1) {
      return state.queue[0];
    }
    const baseIndex = state.queueIndex >= 0 ? state.queueIndex : -1;
    const nextIndex = (baseIndex + 1 + state.queue.length) % state.queue.length;
    return state.queue[nextIndex] || null;
  }

  function preloadNextProfile() {
    const nextProfile = getNextQueueProfile();
    if (nextProfile && nextProfile.id !== state.currentProfileId) {
      preloadImageForProfile(nextProfile);
    }
  }

  function displayActiveProfile(force = false) {
    if (!options.lockActive) {
      return false;
    }
    const activeProfile = resolveActiveProfile();
    if (!activeProfile) {
      return false;
    }
    const alreadyLocked = state.currentSource === 'lock' && state.currentProfileId === activeProfile.id;
    if (!force && alreadyLocked) {
      return true;
    }
    // Transition into (or refresh) the locked view. Only set the locked
    // timestamp when we first enter the locked state — do not overwrite
    // it on forced re-renders (e.g. data refreshes) because that would
    // continuously postpone the ad-override timer.
    const enteringLock = !alreadyLocked;
    state.currentSource = 'lock';
    state.currentProfileId = activeProfile.id || null;
    if (enteringLock) {
      // Record when we entered the locked active profile state so we can
      // detect prolonged locked periods without ads.
      state.lockedSince = Date.now();
    }
    renderProfile(elements, activeProfile);
    syncScrolling(elements);
    preloadNextProfile();
    return true;
  }

  function handleTimerTick() {
    // Log current and next profile IDs whenever the rotation timer fires.
    // This helps troubleshoot mismatches between the visual rotation and
    // the configured rotation interval (e.g. 15s).
    const currentId = state.currentProfileId;
    const nextProfile = getNextQueueProfile();
    const nextId = nextProfile ? nextProfile.id : null;
  // Use a clearly namespaced message so it is easy to find in the console.
  // Print the current source as well (queue, lock, none) for context.
  // Also print time since last advertisement (human-friendly seconds) to
  // help debug ad-override/lock situations.
  const sinceLastAdMs = state.lastAdShownAt ? (Date.now() - state.lastAdShownAt) : null;
  const sinceLastAdLabel = sinceLastAdMs === null ? 'never' : `${Math.floor(sinceLastAdMs / 1000)}s`;
  // eslint-disable-next-line no-console
  console.log('[presentation] timer tick -> current:', currentId, 'source:', state.currentSource, 'next:', nextId, 'sinceLastAd:', sinceLastAdLabel);

    // If we're currently running an ad-override sequence, continue it.
    if (state.adOverrideActive) {
      if (state.adOverrideRemaining <= 0) {
        // End override and return to the previous behaviour (try to show
        // the active profile again).
        state.adOverrideActive = false;
        state.adOverrideRemaining = 0;
        state.lockedSince = null; // will be reset if displayActiveProfile sets lock again
        displayActiveProfile(true);
        return;
      }
      // Show the next ad and return; the ad sequence controls how many
      // ads are shown via adOverrideRemaining.
      showNextAdvertisement();
      return;
    }

    if (displayActiveProfile()) {
      // If the presenter is locked on an active profile, check whether
      // we've gone too long without an advertisement and, if so, trigger
      // a short ad override.
      const AD_OVERRIDE_INTERVAL_MS = 5 * 60 * 1000; // 1 minute (temporarily reduced for testing)
      const now = Date.now();
      const lockedSince = state.lockedSince || 0;
      const lastAd = state.lastAdShownAt || 0;
      // Trigger only if we've been locked for at least the interval and
      // no advertisement has been shown since the lock started.
      if (lockedSince && (now - lockedSince) >= AD_OVERRIDE_INTERVAL_MS && lastAd < lockedSince) {
        triggerAdOverride();
      }
      return;
    }

    if (!state.queue.length) {
      if (state.currentSource === 'queue') {
        handleNoProfile();
      }
      return;
    }

    advanceQueue();
  }

  function setProfiles(profiles, advertisements = []) {
    state.callerProfiles = Array.isArray(profiles)
      ? profiles.filter((item) => item && !item.advertisement)
      : [];
    state.advertisementProfiles = Array.isArray(advertisements)
      ? advertisements.filter((item) => item && item.advertisement)
      : [];
    state.profilesByCaller = new Map();
    state.profilesById = new Map();
    state.callerProfiles.forEach((profile) => {
      const callerId = normalizeCallerId(profile?.caller_cuer_id);
      if (callerId !== null) {
        state.profilesByCaller.set(callerId, profile);
      }
    });
    [...state.callerProfiles, ...state.advertisementProfiles].forEach((profile) => {
      if (profile && Object.prototype.hasOwnProperty.call(profile, 'id')) {
        state.profilesById.set(profile.id, profile);
      }
    });
    rebuildQueue();

    if (state.currentProfileId !== null) {
      const updatedProfile = state.profilesById.get(state.currentProfileId);
      if (updatedProfile) {
        renderProfile(elements, updatedProfile);
        syncScrolling(elements);
      } else if (state.currentSource === 'queue') {
        handleNoProfile();
      }
    }

    if (displayActiveProfile(true)) {
      return;
    }

    if (!state.currentProfileId && state.queue.length) {
      advanceQueue();
    } else if (!state.queue.length) {
      handleNoProfile();
    } else {
      preloadNextProfile();
    }
  }

  function setOptions(partial = {}) {
    const previousLock = options.lockActive;
    if (Object.prototype.hasOwnProperty.call(partial, 'showCallers')) {
      options.showCallers = Boolean(partial.showCallers);
    }
    if (Object.prototype.hasOwnProperty.call(partial, 'showAdvertisements')) {
      options.showAdvertisements = Boolean(partial.showAdvertisements);
    }
    if (Object.prototype.hasOwnProperty.call(partial, 'lockActive')) {
      options.lockActive = Boolean(partial.lockActive);
    }

    rebuildQueue();

    if (!options.lockActive && previousLock && state.currentSource === 'lock') {
      if (state.queue.length) {
        advanceQueue();
      } else {
        handleNoProfile();
      }
      return;
    }

    if (displayActiveProfile(true)) {
      return;
    }

    if (!state.queue.length) {
      handleNoProfile();
      return;
    }

    if (!state.currentProfileId) {
      advanceQueue();
      return;
    }

    preloadNextProfile();
  }

  function updateActiveContext({ callerIds = [], eventId = null, startsAt = null, endsAt = null } = {}) {
    const normalized = Array.isArray(callerIds)
      ? callerIds.map((id) => normalizeCallerId(id)).filter((id) => id !== null)
      : [];
    const signature = [eventId || '', startsAt || '', endsAt || ''].join('|');
    const eventChanged = signature !== state.activeEventSignature;
    state.activeCallerIds = normalized;
    state.activeEventSignature = signature;

    const displayed = displayActiveProfile(eventChanged);

    if (!displayed) {
      if (state.currentSource === 'lock') {
        if (state.queue.length) {
          advanceQueue();
        } else {
          handleNoProfile();
        }
      } else if (!state.currentProfileId && state.queue.length) {
        advanceQueue();
      }
    }

    ensureTimer();
  }

  return {
    setProfiles,
    setOptions,
    updateActiveContext,
    refreshScroll() {
      syncScrolling(elements);
    },
    getOptions() {
      return { ...options };
    },
    hasProfileForCaller(callerId) {
      const normalized = normalizeCallerId(callerId);
      if (normalized === null) {
        return false;
      }
      return state.profilesByCaller.has(normalized);
    },
  };
}
