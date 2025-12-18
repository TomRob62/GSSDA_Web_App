const cache = {
  rooms: [],
  callers: [],
  events: [],
};

export function setRooms(rooms) {
  cache.rooms = Array.isArray(rooms) ? rooms : [];
}

export function setCallers(callers) {
  cache.callers = Array.isArray(callers) ? callers : [];
}

export function setEvents(events) {
  cache.events = Array.isArray(events) ? events : [];
}

export function getRooms() {
  return cache.rooms;
}

export function getCallers() {
  return cache.callers;
}

export function getEvents() {
  return cache.events;
}

function findRoom(roomId) {
  return cache.rooms.find((room) => room.id === roomId) || null;
}

function findCaller(callerId) {
  return cache.callers.find((caller) => caller.id === callerId) || null;
}

export function formatCallerNames(ids) {
  if (!Array.isArray(ids) || !ids.length) return '—';
  return ids
    .map((id) => {
      const caller = findCaller(id);
      if (!caller) return `#${id}`;
      const suffix = caller.suffix ? ` ${caller.suffix}` : '';
      return `${caller.first_name} ${caller.last_name}${suffix}`.trim();
    })
    .join(', ');
}

export function getRoomLabel(roomId) {
  const room = findRoom(roomId);
  return room ? room.room_number : `Room ${roomId}`;
}

function sortEvents(events) {
  const copy = events.slice();
  return copy.sort((a, b) => {
    const startA = new Date(a.start).getTime();
    const startB = new Date(b.start).getTime();
    if (startA !== startB) return startA - startB;
    const roomNameA = getRoomLabel(a.room_id).toLowerCase();
    const roomNameB = getRoomLabel(b.room_id).toLowerCase();
    if (roomNameA !== roomNameB) return roomNameA.localeCompare(roomNameB);
    const callerA = formatCallerNames(a.caller_cuer_ids).toLowerCase();
    const callerB = formatCallerNames(b.caller_cuer_ids).toLowerCase();
    return callerA.localeCompare(callerB);
  });
}

function isUpcoming(event) {
  const endDate = new Date(event.end);
  return endDate >= new Date();
}

export function getDisplayEvents() {
  return sortEvents(cache.events)
    .filter(isUpcoming)
    .map((event) => {
      const start = new Date(event.start);
      const end = new Date(event.end);
      const dances = Array.isArray(event.dance_types) ? event.dance_types.filter(Boolean) : [];
      return {
        ...event,
        start,
        end,
        roomName: getRoomLabel(event.room_id),
        callerNames: formatCallerNames(event.caller_cuer_ids),
        danceText: dances.join(', '),
      };
    });
}
