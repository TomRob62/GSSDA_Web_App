const cache = {
  rooms: [],
  callers: [],
  eventDays: [],
  timezone: null,
};

export function setRooms(rooms) {
  cache.rooms = rooms;
}

export function setCallers(callers) {
  cache.callers = callers;
}

export function setEventDays(days) {
  cache.eventDays = Array.isArray(days) ? days : [];
}

export function setTimezone(timezone) {
  cache.timezone = timezone || null;
}

export function getRooms() {
  return cache.rooms;
}

export function getCallers() {
  return cache.callers;
}

export function getMcCallers() {
  return cache.callers.filter((caller) => caller.mc);
}

export function getEventDays() {
  return cache.eventDays;
}

export function getTimezone() {
  return cache.timezone;
}
