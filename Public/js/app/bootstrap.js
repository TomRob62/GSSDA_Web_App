import { registerLogout } from './auth.js';
import { createToastController } from './toast.js';
import { createFilterController } from './filterControls.js';
import { createModal } from '../components/modal/index.js';
import { calculateDurationMinutes, normalizeDuration, toLocalDateTime } from '../components/datetime.js';
import { getRooms, getCallers, setTimezone } from './state.js';
import { createCacheController } from './controllers/cacheController.js';
import { createModalController } from './controllers/modalController.js';
import { createListController } from './controllers/listController.js';
import { createFilterInputBinder } from './filterInputBinder.js';
import { registerListeners } from './listeners.js';
import { createExportController } from './controllers/exportController.js';
import { detectBrowserTimezone } from './timezone.js';
import { applyRoleVisibility } from '../components/navVisibility.js';

export async function bootstrapApp({ elements, sessionManager }) {
  try {
    await sessionManager.loadSession();
  } catch (error) {
    console.error('Failed to establish session', error);
    localStorage.removeItem('token');
    window.location.href = '/login';
    return;
  }

  registerLogout(elements.logoutLink);
  applyRoleVisibility(sessionManager.getUser());

  const timezone = detectBrowserTimezone();
  setTimezone(timezone);

  const toast = createToastController(elements.toast);
  const filterController = createFilterController({
    sortSelect: elements.sortSelect,
    filterSelect: elements.filterSelect,
    filterValueContainer: elements.filterValueContainer,
  });

  const permissions = { canModify: () => sessionManager.canModify() };

  const modal = createModal({
    modalForm: elements.modalForm,
    modalOverlay: elements.modalOverlay,
    modalTitle: elements.modalTitle,
    submitBtn: elements.submitBtn,
    caches: {
      get rooms() {
        return getRooms();
      },
      get callers() {
        return getCallers();
      },
    },
    utils: { toLocalDateTime, calculateDurationMinutes, normalizeDuration },
  });

  const bindFilterInput = createFilterInputBinder(filterController);

  const cacheController = createCacheController(
    filterController,
    () => bindFilterInput(loadList),
    (message) => {
      toast.show(message, true);
    },
  );

  const modalController = createModalController(
    modal,
    elements,
    (message) => toast.show(message),
    (message) => toast.show(message, true),
    () => cacheController.refreshCaches(),
    () => loadList(),
    permissions,
  );

  const listController = createListController(
    elements,
    filterController,
    {
      onEdit: (item, view) => modalController.openEdit(view, item),
      onSuccess: (message) => toast.show(message),
      onError: (message) => toast.show(message, true),
      refreshCaches: () => cacheController.refreshCaches(),
    },
    permissions,
  );

  const { loadList } = listController;

  const exportController = createExportController(elements, filterController, {
    notifySuccess: (message) => toast.show(message),
    notifyError: (message) => toast.show(message, true),
  });

  exportController.register();

  registerListeners({
    elements,
    filterController,
    modalController,
    modal,
    loadList,
    bindFilterInput,
    permissions,
  });

  if (elements.createBtn) {
    elements.createBtn.hidden = !permissions.canModify();
  }

  await cacheController.refreshCaches();
  const initialView = elements.getActiveView();
  filterController.applyView(initialView);
  bindFilterInput(loadList);
  await loadList();
}
