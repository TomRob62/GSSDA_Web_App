export function getElements() {
  const viewTabs = Array.from(document.querySelectorAll('[data-view]'));

  function getActiveView() {
    const activeTab = viewTabs.find((tab) => tab.classList.contains('tab-bar__tab--active'));
    if (activeTab) return activeTab.dataset.view;
    return viewTabs[0]?.dataset.view || 'rooms';
  }

  function setActiveView(view) {
    viewTabs.forEach((tab) => {
      const isActive = tab.dataset.view === view;
      tab.classList.toggle('tab-bar__tab--active', isActive);
      tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
      tab.setAttribute('tabindex', isActive ? '0' : '-1');
    });
  }

  if (viewTabs.length) {
    setActiveView(getActiveView());
  }

  return {
    viewTabs,
    getActiveView,
    setActiveView,
    createBtn: document.getElementById('createBtn'),
    sortSelect: document.getElementById('sortSelect'),
    filterSelect: document.getElementById('filterSelect'),
    filterValueContainer: document.getElementById('filterValueContainer'),
    applyFiltersBtn: document.getElementById('applyFiltersBtn'),
    clearFiltersBtn: document.getElementById('clearFiltersBtn'),
    exportBtn: document.getElementById('exportBtn'),
    exportDropdown: document.getElementById('exportDropdown'),
    exportMenu: document.getElementById('exportMenu'),
    exportOptions: Array.from(document.querySelectorAll('#exportMenu [data-export-format]')),
    searchInput: document.getElementById('searchInput'),
    listContainer: document.getElementById('listContainer'),
    modalOverlay: document.getElementById('modalOverlay'),
    modalTitle: document.getElementById('modalTitle'),
    modalForm: document.getElementById('modalForm'),
    submitBtn: document.getElementById('submitBtn'),
    submitSpinner: document.getElementById('submitSpinner'),
    cancelBtn: document.getElementById('cancelBtn'),
    toast: document.getElementById('toast'),
    logoutLink: document.getElementById('logoutLink'),
  };
}
