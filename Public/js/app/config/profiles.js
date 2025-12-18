export const profilesConfig = {
  sorts: [
    { value: '', label: 'Default (Caller)', default: true },
    { value: 'caller:asc', label: 'Caller A→Z' },
    { value: 'caller:desc', label: 'Caller Z→A' },
    { value: 'created_at:desc', label: 'Newest' },
    { value: 'updated_at:desc', label: 'Recently Updated' },
    { value: 'advertisement:desc', label: 'Advertisements First' },
  ],
  filters: [
    { value: '', label: 'No filter', type: 'none', default: true },
    { value: 'caller_cuer_id', label: 'Caller ID', type: 'number' },
    { value: 'has_image', label: 'Has Image', type: 'boolean' },
    { value: 'has_content', label: 'Has Content', type: 'boolean' },
    { value: 'advertisement', label: 'Advertisement', type: 'boolean' },
  ],
};
