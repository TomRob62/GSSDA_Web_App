import { fetchAdvancedList, removeItem } from '../dataService.js';
import { getRooms, getCallers } from '../state.js';
import { renderList } from '../renderers/index.js';
import { attachSasToProfiles } from '../profileImageService.js';
import { buildQueryString } from '../queryBuilder.js';

export function createListController(elements, filterController, callbacks, permissions) {
  const { onEdit, onSuccess, onError, refreshCaches } = callbacks;
  const canModify = permissions?.canModify ? permissions.canModify : () => true;

  async function loadList() {
    try {
      const view = elements.getActiveView();
      const query = buildQueryString(elements, filterController);
      let items = await fetchAdvancedList(query);
      // Some advanced lists can include profile objects with image_path set.
      // Ensure any returned items that reference Azure profile blobs get a SAS
      // token attached so the browser can request them when public access
      // is disabled on the storage account.
      if (view === 'profiles' || (Array.isArray(items) && items.some((it) => it && it.image_path))) {
        items = await attachSasToProfiles(items);
      }
      // Debug: log query and number of items returned so we can verify the response
      console.debug('[listController] loadList view=%s query=%s items=%o', view, query, Array.isArray(items) ? items.length : items);
      renderList(
        elements.listContainer,
        view,
        items,
        { rooms: getRooms(), callers: getCallers() },
        {
          onEdit: (item) => onEdit(item, view),
          onDelete: (item) => handleDelete(item, view),
        },
        { allowActions: canModify() },
      );
    } catch (error) {
      onError(error.message);
    }
  }

  async function handleDelete(item, view) {
    if (!canModify()) {
      onError('You do not have permission to delete items.');
      return;
    }
    if (!window.confirm('Are you sure you want to delete this item?')) return;
    try {
      await removeItem(view, item.id);
      onSuccess('Deleted successfully');
      await refreshCaches();
      await loadList();
    } catch (error) {
      onError(error.message);
    }
  }

  return { loadList };
}
