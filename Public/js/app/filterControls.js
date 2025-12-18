import { CONTROL_CONFIG } from './config/index.js';
import { createFilterInput } from './filterInputFactory.js';
import { extractFilterValue, applyFilterValue } from './filterValueHelpers.js';

function populateSelect(select, options) {
  select.innerHTML = '';
  options.forEach((option) => {
    const opt = document.createElement('option');
    opt.value = option.value;
    opt.textContent = option.label;
    select.appendChild(opt);
  });
  const defaultOpt = options.find((option) => option.default) || options[0];
  if (defaultOpt) select.value = defaultOpt.value;
}

function getDefinition(view, value) {
  const config = CONTROL_CONFIG[view] || { filters: [] };
  return config.filters.find((item) => item.value === value) || config.filters.find((item) => item.default) || null;
}

export function createFilterController({ sortSelect, filterSelect, filterValueContainer }) {
  let activeInput = null;
  let activeDefinition = null;

  function renderInput(definition, preserveValue) {
    const previousValue =
      preserveValue && activeInput ? extractFilterValue(activeDefinition, activeInput) : '';
    filterValueContainer.innerHTML = '';
    activeDefinition = definition;
    activeInput = createFilterInput(definition);
    if (!activeInput) {
      const placeholder = document.createElement('span');
      placeholder.textContent = '—';
      placeholder.style.color = '#6B7280';
      filterValueContainer.appendChild(placeholder);
      return;
    }
    if (previousValue) applyFilterValue(definition, activeInput, previousValue);
    filterValueContainer.appendChild(activeInput);
  }

  function applyView(view) {
    const config = CONTROL_CONFIG[view] || { sorts: [], filters: [] };
    populateSelect(sortSelect, config.sorts.length ? config.sorts : [{ value: '', label: 'Default', default: true }]);
    populateSelect(filterSelect, config.filters.length ? config.filters : [{ value: '', label: 'No filter', type: 'none', default: true }]);
    const definition = getDefinition(view, filterSelect.value);
    renderInput(definition, false);
  }

  function getFilterParams(view) {
    if (!activeDefinition || activeDefinition.type === 'none' || !activeInput) return null;
    const raw = extractFilterValue(activeDefinition, activeInput);
    if (!raw) return null;
    if (activeDefinition.type === 'text') return { field: activeDefinition.value, value: raw.trim() };
    return { field: activeDefinition.value, value: raw };
  }

  function refreshInput() {
    if (!activeDefinition) return;
    renderInput(activeDefinition, true);
  }

  return { applyView, getFilterParams, refreshInput, getDefinition: (view, value) => getDefinition(view, value), renderInput: (definition, preserve) => renderInput(definition, preserve), get activeInput() { return activeInput; }, get activeDefinition() { return activeDefinition; } };
}
