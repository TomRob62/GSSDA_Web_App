import { FORMAT_CONFIG, requestExport } from '../exportService.js';

export function createExportController(elements, filterController, callbacks = {}) {
  const button = elements.exportBtn;
  const dropdown = elements.exportDropdown;
  const menu = elements.exportMenu;
  const options = elements.exportOptions || [];
  const notifySuccess = callbacks.notifySuccess || (() => {});
  const notifyError = callbacks.notifyError || (() => {});

  const state = {
    isMenuOpen: false,
    isExporting: false,
    focusIndex: 0,
    originalLabel: button?.textContent?.trim() || 'Export',
  };

  function updateOptionDisabled(disabled) {
    options.forEach((option) => {
      option.disabled = disabled;
      if (disabled) {
        option.setAttribute('aria-disabled', 'true');
      } else {
        option.removeAttribute('aria-disabled');
      }
    });
  }

  function closeMenu({ focusTrigger = false } = {}) {
    if (!state.isMenuOpen || !button || !menu || !dropdown) return;
    state.isMenuOpen = false;
    dropdown.classList.remove('dropdown--open');
    button.setAttribute('aria-expanded', 'false');
    menu.hidden = true;
    document.removeEventListener('click', handleDocumentClick);
    document.removeEventListener('keydown', handleMenuKeydown);
    if (focusTrigger) {
      button.focus();
    }
  }

  function focusOption(index) {
    if (!options.length) return;
    const normalized = (index + options.length) % options.length;
    state.focusIndex = normalized;
    options[normalized].focus();
  }

  function openMenu(initialIndex = 0) {
    if (state.isMenuOpen || state.isExporting || !button || !menu || !dropdown) return;
    state.isMenuOpen = true;
    dropdown.classList.add('dropdown--open');
    button.setAttribute('aria-expanded', 'true');
    menu.hidden = false;
    document.addEventListener('click', handleDocumentClick);
    document.addEventListener('keydown', handleMenuKeydown);
    requestAnimationFrame(() => {
      const targetIndex = options.length ? initialIndex : 0;
      focusOption(targetIndex);
    });
  }

  function toggleMenu() {
    if (state.isExporting) return;
    if (state.isMenuOpen) {
      closeMenu();
    } else {
      openMenu();
    }
  }

  function handleTriggerKeydown(event) {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      if (!state.isMenuOpen) {
        openMenu(0);
      } else {
        focusOption(state.focusIndex + 1);
      }
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      if (!state.isMenuOpen) {
        const lastIndex = Math.max(options.length - 1, 0);
        openMenu(lastIndex);
      } else {
        focusOption(state.focusIndex - 1);
      }
    }
  }

  function handleDocumentClick(event) {
    if (!dropdown || !dropdown.contains(event.target)) {
      closeMenu();
    }
  }

  function handleMenuKeydown(event) {
    if (!state.isMenuOpen) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      closeMenu({ focusTrigger: true });
      return;
    }

    if (event.key === 'ArrowDown') {
      event.preventDefault();
      focusOption(state.focusIndex + 1);
      return;
    }

    if (event.key === 'ArrowUp') {
      event.preventDefault();
      focusOption(state.focusIndex - 1);
      return;
    }

    if (event.key === 'Home') {
      event.preventDefault();
      focusOption(0);
      return;
    }

    if (event.key === 'End') {
      event.preventDefault();
      focusOption(options.length - 1);
      return;
    }

    if (event.key === 'Tab') {
      closeMenu();
    }
  }

  function setBusy(formatKey) {
    if (!button) return;
    state.isExporting = true;
    const label = FORMAT_CONFIG[formatKey]?.label || '';
    button.disabled = true;
    button.textContent = label ? `Exporting ${label}…` : 'Exporting…';
    updateOptionDisabled(true);
  }

  function clearBusy() {
    if (!button) return;
    state.isExporting = false;
    button.disabled = false;
    button.textContent = state.originalLabel;
    updateOptionDisabled(false);
  }

  async function handleSelection(formatKey) {
    closeMenu();
    if (!formatKey || state.isExporting) return;

    setBusy(formatKey);
    try {
      const message = await requestExport(elements, filterController, formatKey);
      notifySuccess(message);
    } catch (error) {
      const fallback = 'Failed to create export.';
      notifyError(error instanceof Error ? error.message : fallback);
    } finally {
      clearBusy();
    }
  }

  function handleOptionClick(event) {
    event.preventDefault();
    const formatKey = (event.currentTarget.dataset.exportFormat || '').toLowerCase();
    handleSelection(formatKey);
  }

  function register() {
    if (!button) return;
    state.originalLabel = button.textContent?.trim() || state.originalLabel;
    if (menu) {
      menu.hidden = true;
    }
    button.addEventListener('click', toggleMenu);
    button.addEventListener('keydown', handleTriggerKeydown);
    options.forEach((option, index) => {
      option.addEventListener('click', handleOptionClick);
      option.addEventListener('focus', () => {
        state.focusIndex = index;
      });
    });
  }

  return { register };
}

