export const callersConfig = {
  sorts: [
    { value: '', label: 'Default (ID)', default: true },
    { value: 'first_name:asc', label: 'First Name A→Z' },
    { value: 'first_name:desc', label: 'First Name Z→A' },
    { value: 'last_name:asc', label: 'Last Name A→Z' },
    { value: 'last_name:desc', label: 'Last Name Z→A' },
    { value: 'created_at:desc', label: 'Newest' },
  ],
  filters: [
    { value: '', label: 'No filter', type: 'none', default: true },
    { value: 'mc', label: 'MC Flag', type: 'boolean' },
    { value: 'dance_type', label: 'Dance Type Contains', type: 'text' },
  ],
};
