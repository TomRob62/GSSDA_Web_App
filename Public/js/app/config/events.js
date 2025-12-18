export const eventsConfig = {
  sorts: [
    { value: 'start:asc', label: 'Start (Earliest)', default: true },
    { value: 'start:desc', label: 'Start (Latest)' },
    { value: 'end:asc', label: 'End (Earliest)' },
    { value: 'end:desc', label: 'End (Latest)' },
    { value: 'created_at:desc', label: 'Newest' },
  ],
  filters: [
    { value: '', label: 'No filter', type: 'none', default: true },
    { value: 'room', label: 'Room', type: 'select-room' },
    { value: 'caller', label: 'Includes Caller/Cuer', type: 'select-caller' },
    { value: 'dance_type', label: 'Dance Type Contains', type: 'text' },
    { value: 'start_from', label: 'Start On/After', type: 'datetime' },
    { value: 'start_to', label: 'Start On/Before', type: 'datetime' },
    { value: 'start_day', label: 'Day (MM/DD)', type: 'multi-day' },
  ],
};
