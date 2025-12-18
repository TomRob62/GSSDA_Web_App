import { ensureAuthenticated } from './auth.js';
import { getElements } from './elements.js';
import { createSessionManager } from './session.js';
import { bootstrapApp } from './bootstrap.js';

if (!ensureAuthenticated()) {
  throw new Error('Authentication required');
}

const sessionManager = createSessionManager();
const elements = getElements();

if (elements.createBtn) {
  elements.createBtn.hidden = true;
}

bootstrapApp({ elements, sessionManager }).catch((error) => {
  console.error('Application initialization failed', error);
});
