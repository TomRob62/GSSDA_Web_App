import { createLabel, createTextarea } from '../primitives.js';
import { resolveProfileImageUrl } from '../../../app/profileImageService.js';

const DESCRIPTION_PLACEHOLDER = 'Description';

function appendCallerAndAdvertisementRow(form, callers, data) {
  const row = document.createElement('div');
  row.className = 'profile-form-grid';

  const callerField = document.createElement('div');
  callerField.className = 'profile-form-field';

  const callerLabel = createLabel('Caller');
  callerLabel.classList.add('profile-form-label');
  callerLabel.htmlFor = 'callerSelect';
  callerField.appendChild(callerLabel);

  const callerSelect = document.createElement('select');
  callerSelect.name = 'caller_cuer_id';
  callerSelect.id = 'callerSelect';
  callerSelect.className = 'profile-form-select';
  callerSelect.appendChild(new Option('-- Select Caller --', ''));

  const sorted = callers.slice().sort((a, b) => {
    const left = `${a.last_name} ${a.first_name}`.toLowerCase();
    const right = `${b.last_name} ${b.first_name}`.toLowerCase();
    return left.localeCompare(right);
  });
  sorted.forEach((caller) => {
    const option = document.createElement('option');
    option.value = caller.id;
    const suffix = caller.suffix ? ` ${caller.suffix}` : '';
    option.textContent = `${caller.first_name} ${caller.last_name}${suffix}`.trim();
    option.selected = data?.caller_cuer_id === caller.id || data?.caller?.id === caller.id;
    callerSelect.appendChild(option);
  });
  if (!callerSelect.value && data?.caller_cuer_id) {
    callerSelect.value = String(data.caller_cuer_id);
  }
  callerField.appendChild(callerSelect);

  const advertisementField = document.createElement('div');
  advertisementField.className = 'profile-form-field profile-form-field--compact';

  const advertisementLabel = createLabel('Advertisement');
  advertisementLabel.classList.add('profile-form-label');
  advertisementLabel.htmlFor = 'advertisementSelect';
  advertisementField.appendChild(advertisementLabel);

  const advertisementSelect = document.createElement('select');
  advertisementSelect.name = 'advertisement';
  advertisementSelect.id = 'advertisementSelect';
  advertisementSelect.className = 'profile-form-select';
  advertisementSelect.appendChild(new Option('No', 'false'));
  advertisementSelect.appendChild(new Option('Yes', 'true'));
  advertisementSelect.value = data?.advertisement ? 'true' : 'false';
  advertisementField.appendChild(advertisementSelect);

  row.appendChild(callerField);
  row.appendChild(advertisementField);
  form.appendChild(row);

  const helper = document.createElement('p');
  helper.className = 'form-hint profile-advertisement-hint';
  helper.textContent = 'Advertisements rotate on presentation screens when no caller profile is available.';
  form.appendChild(helper);

  let previousValue = callerSelect.value;
  function syncCallerState() {
    const isAdvertisement = advertisementSelect.value === 'true';
    if (isAdvertisement) {
      previousValue = callerSelect.value || previousValue;
      callerSelect.value = '';
      callerSelect.disabled = true;
      callerSelect.classList.add('is-disabled');
    } else {
      callerSelect.disabled = false;
      callerSelect.classList.remove('is-disabled');
      if (!callerSelect.value && previousValue) {
        const option = callerSelect.querySelector(`option[value="${previousValue}"]`);
        if (option) callerSelect.value = previousValue;
      }
    }
  }

  syncCallerState();
  advertisementSelect.addEventListener('change', syncCallerState);
}

function appendImageField(form, data) {
  const section = document.createElement('div');
  section.className = 'profile-form-section';

  const label = createLabel('Profile Image');
  label.classList.add('profile-form-label');
  label.htmlFor = 'profileImageInput';
  section.appendChild(label);

  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.name = 'image_file';
  fileInput.accept = 'image/*';
  fileInput.id = 'profileImageInput';
  fileInput.className = 'profile-form-file';
  section.appendChild(fileInput);

  const helper = document.createElement('p');
  helper.className = 'form-hint profile-form-hint';
  helper.textContent = 'Upload JPG or PNG files up to 10 MB.';
  section.appendChild(helper);

  if (data?.image_path) {
    const preview = document.createElement('div');
    preview.className = 'profile-image-preview profile-form-preview';
    const link = document.createElement('a');
    // Set a safe placeholder href while we asynchronously resolve a SAS token.
    link.href = '#';
    link.target = '_blank';
    link.rel = 'noopener';
    link.textContent = 'View current image';
    preview.appendChild(link);
    section.appendChild(preview);

    // Try to resolve a SAS-protected URL; update the link when available.
    // We don't await here to keep the builder synchronous; update DOM when ready.
    try {
      resolveProfileImageUrl(data.image_path)
        .then((href) => {
          if (href) link.href = href;
        })
        .catch(() => {
          // Leave the placeholder href; clicking will open a new tab to the raw URL
          // which may be blocked if SAS is required.
        });
    } catch (err) {
      // If resolving the SAS throws synchronously for any reason, ignore it.
    }

    const removeWrapper = document.createElement('div');
    removeWrapper.className = 'profile-remove-image profile-form-checkbox';

    const removeInput = document.createElement('input');
    removeInput.type = 'checkbox';
    removeInput.id = 'removeImageCheckbox';
    removeInput.name = 'remove_image';
    removeWrapper.appendChild(removeInput);

    const removeLabel = createLabel('Remove current image');
    removeLabel.htmlFor = 'removeImageCheckbox';
    removeWrapper.appendChild(removeLabel);

    section.appendChild(removeWrapper);
  }

  form.appendChild(section);
}

function appendContentField(form, data) {
  const section = document.createElement('div');
  section.className = 'profile-form-section';

  const textarea = createTextarea({
    name: 'content',
    value: data?.content || '',
    rows: 8,
    placeholder: DESCRIPTION_PLACEHOLDER,
  });
  textarea.id = 'profileDescription';
  textarea.className = 'profile-form-textarea';
  textarea.setAttribute('aria-label', 'Profile Description');
  section.appendChild(textarea);

  form.appendChild(section);
}

export function buildProfileForm(form, data, caches) {
  appendCallerAndAdvertisementRow(form, caches.callers, data);
  appendImageField(form, data);
  appendContentField(form, data);
}
