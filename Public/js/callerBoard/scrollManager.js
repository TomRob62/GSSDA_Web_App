const SCROLL_INTERVAL = 30000;

function parseTime(value) {
  return value ? new Date(value).getTime() : Number.NaN;
}

export function createScrollManager(listElement) {
  if (!listElement) {
    return {
      start() {},
      stop() {},
      refresh() {},
    };
  }

  let timerId = null;

  function findTarget() {
    const items = Array.from(listElement.querySelectorAll('[data-start][data-end]'));
    if (!items.length) return null;
    const now = Date.now();
    const exact = items.find((item) => {
      const start = parseTime(item.dataset.start);
      const end = parseTime(item.dataset.end);
      return !Number.isNaN(start) && !Number.isNaN(end) && start <= now && now <= end;
    });
    if (exact) return exact;
    const upcoming = items.find((item) => {
      const start = parseTime(item.dataset.start);
      return !Number.isNaN(start) && start > now;
    });
    return upcoming || items[items.length - 1];
  }

  function scrollToTarget() {
    const target = findTarget();
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  function start() {
    stop();
    scrollToTarget();
    timerId = setInterval(scrollToTarget, SCROLL_INTERVAL);
  }

  function stop() {
    if (timerId) clearInterval(timerId);
    timerId = null;
  }

  function refresh() {
    scrollToTarget();
  }

  return { start, stop, refresh };
}
