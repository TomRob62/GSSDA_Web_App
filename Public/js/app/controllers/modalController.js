import { buildPayload } from '../formTransforms.js';
import { submitItem } from '../dataService.js';
import { toLocalDateTime } from '../../components/datetime.js';

export function createModalController(modal, elements, notifySuccess, notifyError, refreshCaches, loadList, permissions) {
  const canModify = permissions?.canModify ? permissions.canModify : () => true;

  function ensureCanModify() {
    if (canModify()) return true;
    notifyError('You do not have permission to modify data.');
    return false;
  }

  async function handleSubmit() {
    if (!ensureCanModify()) return;
    const { submitBtn, submitSpinner } = elements;
    if (submitBtn?.dataset.loading === 'true') return;
    const { type, mode, id } = submitBtn.dataset;
    if (submitBtn) {
      submitBtn.dataset.loading = 'true';
      submitBtn.disabled = true;
      submitBtn.setAttribute('aria-busy', 'true');
    }
    if (submitSpinner) {
      submitSpinner.hidden = false;
      submitSpinner.setAttribute('aria-hidden', 'false');
    }
    try {
      const { payload, nextStart, isMultipart } = buildPayload(type, elements.modalForm);
      await submitItem(type, mode, payload, id, { isMultipart });
      notifySuccess(mode === 'edit' ? 'Updated successfully' : 'Created successfully');
      await refreshCaches();
      await loadList();
      if (mode === 'create' && nextStart) {
        const startInput = elements.modalForm.querySelector('input[name="start"]');
        if (startInput) startInput.value = toLocalDateTime(nextStart.toISOString());
        return;
      }
      modal.closeModal();
    } catch (error) {
      notifyError(error.message);
    } finally {
      if (submitSpinner) {
        submitSpinner.hidden = true;
        submitSpinner.setAttribute('aria-hidden', 'true');
      }
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.removeAttribute('aria-busy');
        delete submitBtn.dataset.loading;
      }
    }
  }

  function openCreate(type) {
    if (!type) return;
    if (!ensureCanModify()) return;
    modal.openModal(type, 'create');
  }

  function openEdit(type, item) {
    if (!ensureCanModify()) return;
    modal.openModal(type, 'edit', item);
  }

  return { handleSubmit, openCreate, openEdit };
}
