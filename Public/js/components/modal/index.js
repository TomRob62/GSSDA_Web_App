import { buildRoomsForm } from './builders/roomsFormBuilder.js';
import { buildCallerForm } from './builders/callerFormBuilder.js';
import { buildEventForm } from './builders/eventFormBuilder.js';
import { buildMcForm } from './builders/mcFormBuilder.js';
import { buildProfileForm } from './builders/profileFormBuilder.js';

const FORM_BUILDERS = {
  rooms: buildRoomsForm,
  caller_cuers: buildCallerForm,
  events: buildEventForm,
  mcs: buildMcForm,
  profiles: buildProfileForm,
};

function formatTitle(type, mode) {
  const label = type.replace('_', ' ');
  const capitalized = label.replace(/\b\w/g, (c) => c.toUpperCase());
  const prefix = mode === 'edit' ? 'Edit' : 'Create';
  return `${prefix} ${capitalized}`;
}

function setSubmitMetadata(button, type, mode, data) {
  button.dataset.type = type;
  button.dataset.mode = mode;
  if (data?.id) {
    button.dataset.id = data.id;
    return;
  }
  delete button.dataset.id;
}

function buildFormContent(type, form, data, caches, utils) {
  const builder = FORM_BUILDERS[type];
  if (!builder) throw new Error(`Unknown form type: ${type}`);
  builder(form, data, caches, utils);
}

export function createModal({ modalForm, modalOverlay, modalTitle, submitBtn, caches, utils }) {
  function closeModal() {
    if (modalForm.__descriptionManager?.modal) {
      modalForm.__descriptionManager.modal.close();
    }
    delete modalForm.__descriptionManager;
    modalOverlay.style.display = 'none';
    modalForm.innerHTML = '';
  }

  function openModal(type, mode, data) {
    modalForm.innerHTML = '';
    delete modalForm.__descriptionManager;
    modalTitle.textContent = formatTitle(type, mode);
    setSubmitMetadata(submitBtn, type, mode, data);
    buildFormContent(type, modalForm, data, caches, utils);
    modalOverlay.style.display = 'flex';
  }

  return { openModal, closeModal };
}
