export const roomsConfig = {
  sorts: [
    { value: '', label: 'Default (ID)', default: true },
    { value: 'room_number:asc', label: 'Room Number A→Z' },
    { value: 'room_number:desc', label: 'Room Number Z→A' },
    { value: 'created_at:desc', label: 'Newest' },
    { value: 'created_at:asc', label: 'Oldest' },
  ],
  filters: [
    { value: '', label: 'No filter', type: 'none', default: true },
    { value: 'static', label: 'Static Room', type: 'boolean' },
    { value: 'room_number', label: 'Room Number Contains', type: 'text' },
    { value: 'description', label: 'Description Contains', type: 'text' },
    { value: 'start_from', label: 'Description Start After', type: 'datetime' },
    { value: 'start_to', label: 'Description Start Before', type: 'datetime' },
  ],
};
