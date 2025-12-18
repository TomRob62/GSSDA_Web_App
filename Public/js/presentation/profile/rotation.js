export function createRotation({ intervalMs = 30000 } = {}) {
  let timerId = null;
  let profiles = [];
  let index = 0;
  let listener = () => {};

  function notify() {
    if (!profiles.length) {
      listener(null);
      return;
    }
    const profile = profiles[index % profiles.length];
    listener(profile || null);
  }

  function scheduleNext() {
    clearInterval(timerId);
    timerId = setInterval(() => {
      if (!profiles.length) {
        notify();
        return;
      }
      index = (index + 1) % profiles.length;
      notify();
    }, intervalMs);
  }

  function start(list) {
    // Preserve running state and currently-displayed profile id so we can
    // attempt to continue from the same index when the list is updated.
    const wasRunning = Boolean(timerId);
    const currentProfileId = profiles[index]?.id;

    stop();
    profiles = Array.isArray(list) ? list.slice() : [];

    if (!profiles.length) {
      index = 0;
      notify();
      return;
    }

    if (wasRunning) {
      // Try to locate the previously shown profile in the new list.
      const newIndex = profiles.findIndex((p) => p?.id === currentProfileId);
      index = newIndex >= 0 ? newIndex : 0;
    } else {
      index = 0;
    }

    notify();
    if (profiles.length > 1) {
      scheduleNext();
    }
  }

  function stop() {
    clearInterval(timerId);
    timerId = null;
    index = 0;
  }

  function update(list) {
    const wasRunning = timerId !== null;
    const currentProfile = profiles[index] || null;
    profiles = Array.isArray(list) ? list.slice() : [];
    if (!profiles.length) {
      stop();
      notify();
      return;
    }
    const newIndex = profiles.findIndex((item) => item?.id === currentProfile?.id);
    index = newIndex >= 0 ? newIndex : 0;
    if (wasRunning || profiles.length > 1) {
      if (profiles.length > 1) {
        scheduleNext();
      } else {
        stop();
      }
    }
    notify();
  }

  return {
    start,
    stop,
    update,
    setListener(callback) {
      listener = typeof callback === 'function' ? callback : () => {};
    },
    isRunning() {
      return timerId !== null;
    },
  };
}
