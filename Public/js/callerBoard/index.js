import { ensureAuthenticated, registerLogout } from '../app/auth.js';
import { createSessionManager } from '../app/session.js';
import { applyRoleVisibility, enforceRoleAccess } from '../components/navVisibility.js';
import { setupFullscreen } from '../presentation/fullscreen.js';
import { startClock } from '../presentation/time.js';
import { createScrollManager } from './scrollManager.js';
import { createBoardController } from './controller.js';

if (!ensureAuthenticated()) {
  throw new Error('Authentication required');
}

const elements = {
  list: document.getElementById('callerEventList'),
  currentTime: document.getElementById('currentTime'),
  fullscreenBtn: document.getElementById('fullscreenBtn'),
  logoutLink: document.getElementById('logoutLink'),
};

const sessionManager = createSessionManager();
const scrollManager = createScrollManager(elements.list);
const boardController = createBoardController(elements, scrollManager);

async function initialize() {
  let user;
  try {
    user = await sessionManager.loadSession();
  } catch (error) {
    console.error('Unable to load session', error);
    localStorage.removeItem('token');
    window.location.href = '/login';
    return;
  }

  if (!enforceRoleAccess(user, ['admin', 'caller'])) {
    return;
  }

  applyRoleVisibility(user);
  registerLogout(elements.logoutLink);
  setupFullscreen(elements.fullscreenBtn, { activeClass: 'caller-board-fullscreen' });
  startClock(elements.currentTime);

  try {
    await boardController.loadLookups();
  } catch (error) {
    console.error('Failed to load supporting data', error);
    if (elements.list) elements.list.innerHTML = '';
    // boardStatus removed: show a simple console error; page can display empty list
    return;
  }

  await boardController.refreshBoard({ showLoading: true });
  scrollManager.start();
  setInterval(() => boardController.refreshBoard(), 60000);
}

initialize();
