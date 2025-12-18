function isMultiSelect(input) {
  return input && input.tagName === 'SELECT' && input.multiple;
}

function normaliseListValue(value) {
  if (Array.isArray(value)) return value.filter(Boolean);
  if (typeof value !== 'string') return [];
  return value
    .split(',')
    .map((part) => part.trim())
    .filter((part) => part);
}

export function extractFilterValue(definition, input) {
  if (!input) return '';
  if (isMultiSelect(input)) {
    return Array.from(input.selectedOptions)
      .map((option) => option.value)
      .filter((value) => value)
      .join(',');
  }
  return input.value ?? '';
}

export function applyFilterValue(definition, input, value) {
  if (!input || value === undefined || value === null) return;
  if (isMultiSelect(input)) {
    const selectedValues = new Set(normaliseListValue(value));
    Array.from(input.options).forEach((option) => {
      option.selected = selectedValues.has(option.value);
    });
    return;
  }
  input.value = value;
}
