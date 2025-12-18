function isFullscreenActive() {
  return Boolean(document.fullscreenElement);
}

function updateButton(button, activeClass) {
  if (!button) return;
  button.textContent = isFullscreenActive() ? 'Exit Fullscreen' : 'Enter Fullscreen';
  document.body.classList.toggle(activeClass, isFullscreenActive());
}

export function setupFullscreen(button, options = {}) {
  const { activeClass = 'presentation-fullscreen' } = options;
  if (!button) return;
  button.addEventListener('click', async () => {
    try {
      if (!isFullscreenActive()) {
        await document.documentElement.requestFullscreen();
      } else if (document.exitFullscreen) {
        await document.exitFullscreen();
      }
    } catch (error) {
      console.error('Unable to toggle fullscreen', error);
    } finally {
      updateButton(button, activeClass);
    }
  });

  const handleUpdate = () => updateButton(button, activeClass);
  document.addEventListener('fullscreenchange', handleUpdate);
  document.addEventListener('keydown', async (event) => {
    if (event.key !== 'Escape' || !isFullscreenActive()) return;
    try {
      if (document.exitFullscreen) await document.exitFullscreen();
    } catch (error) {
      console.error('Error exiting fullscreen via Escape', error);
    }
  });

  handleUpdate();
}
