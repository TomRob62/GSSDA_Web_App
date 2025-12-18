const SCROLL_MIN_DISTANCE = 32;

function applyScrolling(contentEl) {
  if (!contentEl) return;
  contentEl.classList.remove('profile-content--scrolling');
  contentEl.style.removeProperty('--profile-scroll-distance');
  contentEl.style.removeProperty('--profile-scroll-duration');
  const wrapper = contentEl.parentElement;
  if (!wrapper) return;
  const distance = contentEl.scrollHeight - wrapper.clientHeight;
  if (distance <= SCROLL_MIN_DISTANCE) {
    contentEl.style.transform = 'translateY(0)';
    return;
  }
  const duration = Math.min(Math.max(distance / 15, 30), 120);
  contentEl.style.setProperty('--profile-scroll-distance', `${distance}px`);
  contentEl.style.setProperty('--profile-scroll-duration', `${duration}s`);
  void contentEl.offsetWidth; // restart animation
  contentEl.classList.add('profile-content--scrolling');
}

function resetScrolling(contentEl) {
  if (!contentEl) return;
  contentEl.classList.remove('profile-content--scrolling');
  contentEl.style.removeProperty('--profile-scroll-distance');
  contentEl.style.removeProperty('--profile-scroll-duration');
  contentEl.style.transform = 'translateY(0)';
}

function updateImage(elements, profile) {
  const { profileImage, profileImageWrapper } = elements;
  if (!profileImage || !profileImageWrapper) return;
  const hasImage = Boolean(profile?.image_path);
  if (hasImage) {
    profileImage.src = profile.image_path;
    const callerName = `${profile.caller?.first_name || ''} ${profile.caller?.last_name || ''}`.trim();
    if (profile.advertisement && callerName) {
      profileImage.alt = `${callerName} advertisement`;
    } else if (callerName) {
      profileImage.alt = `${callerName} profile`;
    } else {
      profileImage.alt = 'Profile image';
    }
    profileImage.hidden = false;
    profileImageWrapper.classList.remove('profile-image-wrapper--empty');
  } else {
    profileImage.removeAttribute('src');
    profileImage.hidden = true;
    profileImage.alt = '';
    profileImageWrapper.classList.add('profile-image-wrapper--empty');
  }
}

export function renderProfile(elements, profile) {
  if (!profile) {
    clearProfile(elements);
    return;
  }
  elements.profilePanel.hidden = false;
  elements.presentationContainer.classList.add('has-profile');
  // Do not display the caller name on the presentation page. Keep the
  // DOM element cleared and hidden so it doesn't appear in the UI.
  if (elements.profileCallerName) {
    elements.profileCallerName.textContent = '';
    elements.profileCallerName.hidden = true;
  }
  const content = typeof profile.content === 'string' ? profile.content.trim() : '';
  const hasContent = content.length > 0;
  if (elements.profileContentWrapper) {
    elements.profileContentWrapper.hidden = !hasContent;
  }
  elements.profileContent.textContent = hasContent ? content : '';
  if (hasContent) {
    applyScrolling(elements.profileContent);
  } else {
    resetScrolling(elements.profileContent);
  }
  updateImage(elements, profile);
}

export function clearProfile(elements) {
  elements.profilePanel.hidden = true;
  elements.presentationContainer.classList.remove('has-profile');
  elements.profileCallerName.textContent = '';
  elements.profileCallerName.hidden = true;
  elements.profileContent.textContent = '';
  if (elements.profileContentWrapper) {
    elements.profileContentWrapper.hidden = true;
  }
  resetScrolling(elements.profileContent);
  if (elements.profileImage) {
    elements.profileImage.removeAttribute('src');
    elements.profileImage.hidden = true;
    elements.profileImage.alt = '';
  }
  if (elements.profileImageWrapper) {
    elements.profileImageWrapper.classList.add('profile-image-wrapper--empty');
  }
}

export function syncScrolling(elements) {
  applyScrolling(elements.profileContent);
}
