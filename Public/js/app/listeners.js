export function registerListeners({ elements, filterController, modalController, modal, loadList, bindFilterInput, permissions }) {
  const canModify = permissions?.canModify ? permissions.canModify : () => true;

  elements.cancelBtn.addEventListener('click', () => modal.closeModal());
  elements.submitBtn.addEventListener('click', () => modalController.handleSubmit());

  const viewLabelMap = {
    rooms: 'Create Room',
    caller_cuers: 'Create Caller/Cuer',
    events: 'Create Event',
    mcs: 'Create MC',
    profiles: 'Create Profile',
  };

  function updateCreateButton(view) {
    if (!elements.createBtn) return;
    if (!canModify()) {
      elements.createBtn.hidden = true;
      return;
    }
    elements.createBtn.hidden = false;
    elements.createBtn.textContent = viewLabelMap[view] || 'Create';
  }

  function handleViewChange(view) {
    elements.setActiveView(view);
    elements.searchInput.value = '';
    filterController.applyView(view);
    bindFilterInput(loadList);
    loadList();
    updateCreateButton(view);
  }

  elements.viewTabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      const view = tab.dataset.view;
      if (!view) return;
      if (view === elements.getActiveView()) return;
      handleViewChange(view);
    });

    tab.addEventListener('keydown', (event) => {
      if (!['Enter', ' ', 'Space'].includes(event.key)) return;
      event.preventDefault();
      const view = tab.dataset.view;
      if (!view) return;
      if (view === elements.getActiveView()) return;
      handleViewChange(view);
    });
  });

  updateCreateButton(elements.getActiveView());

  if (elements.createBtn) {
    elements.createBtn.addEventListener('click', () => {
      if (!canModify()) return;
      modalController.openCreate(elements.getActiveView());
    });
  }

  elements.sortSelect.addEventListener('change', () => loadList());

  elements.filterSelect.addEventListener('change', () => {
    const definition = filterController.getDefinition(elements.getActiveView(), elements.filterSelect.value);
    filterController.renderInput(definition, false);
    bindFilterInput(loadList);
  });

  elements.applyFiltersBtn.addEventListener('click', () => loadList());

  elements.clearFiltersBtn.addEventListener('click', () => {
    elements.searchInput.value = '';
    const view = elements.getActiveView();
    filterController.applyView(view);
    bindFilterInput(loadList);
    loadList();
  });

  elements.searchInput.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter') return;
    event.preventDefault();
    loadList();
  });
}
