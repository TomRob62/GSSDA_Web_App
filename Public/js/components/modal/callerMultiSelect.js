const CHIP_PLACEHOLDER_TEXT = 'No callers or cuers selected';

function formatCallerLabel(caller) {
  if (!caller) return 'Unknown caller';
  const suffix = caller.suffix ? ` ${caller.suffix}` : '';
  return `${caller.first_name} ${caller.last_name}${suffix}`.trim();
}

function buildOptionList(select, callers) {
  select.appendChild(new Option('-- Select Caller/Cuer --', ''));
  callers
    .slice()
    .sort((a, b) => formatCallerLabel(a).localeCompare(formatCallerLabel(b)))
    .forEach((caller) => {
      select.appendChild(new Option(formatCallerLabel(caller), caller.id));
    });
}

export function createCallerMultiSelect({ callers, selectedIds = [] }) {
  const state = new Set();
  selectedIds.forEach((id) => {
    const numeric = Number(id);
    if (!Number.isNaN(numeric)) state.add(numeric);
  });

  const container = document.createElement('div');
  container.className = 'caller-multi-select';

  const chipList = document.createElement('div');
  chipList.className = 'caller-chip-list';

  const hiddenInputs = document.createElement('div');
  hiddenInputs.className = 'caller-chip-hidden-inputs';
  hiddenInputs.style.display = 'none';

  const controls = document.createElement('div');
  controls.className = 'caller-chip-controls';

  const addButton = document.createElement('button');
  addButton.type = 'button';
  addButton.className = 'secondary';
  addButton.textContent = 'Add Caller/Cuer';
  controls.appendChild(addButton);

  container.append(chipList, hiddenInputs, controls);

  let activeSelector = null;

  function availableCallers() {
    return callers.filter((caller) => !state.has(caller.id));
  }

  function renderHiddenInputs() {
    hiddenInputs.innerHTML = '';
    state.forEach((id) => {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = 'caller_cuer_ids';
      input.value = String(id);
      hiddenInputs.appendChild(input);
    });
  }

  function renderChipPlaceholder() {
    const placeholder = document.createElement('span');
    placeholder.className = 'caller-chip-placeholder';
    placeholder.textContent = CHIP_PLACEHOLDER_TEXT;
    chipList.appendChild(placeholder);
  }

  function renderChips() {
    chipList.innerHTML = '';
    if (state.size === 0) {
      renderChipPlaceholder();
      return;
    }
    state.forEach((id) => {
      const caller = callers.find((item) => item.id === id);
      const chip = document.createElement('span');
      chip.className = 'caller-chip';

      const label = document.createElement('span');
      label.className = 'caller-chip-label';
      label.textContent = formatCallerLabel(caller) || `Caller ${id}`;

      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.className = 'caller-chip-remove';
      removeBtn.setAttribute('aria-label', `Remove ${label.textContent}`);
      removeBtn.textContent = '×';
      removeBtn.addEventListener('click', () => {
        state.delete(id);
        sync();
      });

      chip.append(label, removeBtn);
      chipList.appendChild(chip);
    });
  }

  function updateButtonState() {
    const remaining = availableCallers().length;
    addButton.disabled = remaining === 0;
    addButton.title = remaining === 0 ? 'All callers/cuers have been selected' : '';
  }

  function closeSelector() {
    if (!activeSelector) return;
    controls.replaceChild(addButton, activeSelector);
    activeSelector = null;
    updateButtonState();
  }

  function handleSelectionChange(event) {
    const value = Number(event.target.value);
    if (!value || Number.isNaN(value)) return;
    state.add(value);
    closeSelector();
    sync();
  }

  function showSelector() {
    if (activeSelector) return;
    const remaining = availableCallers();
    if (!remaining.length) return;

    const wrapper = document.createElement('div');
    wrapper.className = 'caller-select-wrapper';

    const select = document.createElement('select');
    select.className = 'caller-select';
    buildOptionList(select, remaining);
    select.addEventListener('change', handleSelectionChange);
    wrapper.appendChild(select);

    const cancelBtn = document.createElement('button');
    cancelBtn.type = 'button';
    cancelBtn.className = 'link-button caller-select-cancel';
    cancelBtn.textContent = 'Cancel';
    cancelBtn.addEventListener('click', () => closeSelector());
    wrapper.appendChild(cancelBtn);

    controls.replaceChild(wrapper, addButton);
    activeSelector = wrapper;
    select.focus();
  }

  function sync() {
    renderChips();
    renderHiddenInputs();
    updateButtonState();
  }

  addButton.addEventListener('click', () => {
    showSelector();
  });

  sync();
  return container;
}
