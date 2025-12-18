const ROLE_ATTR = 'visibleFor';
const ROLE_ATTR_NAME = 'visible-for';

function parseRoleList(value) {
  if (!value) return [];
  return value
    .split(',')
    .map((role) => role.trim())
    .filter(Boolean);
}

export function applyRoleVisibility(user) {
  const role = user?.role || '';
  const targets = document.querySelectorAll(`[data-${ROLE_ATTR_NAME}]`);
  targets.forEach((element) => {
    const allowed = parseRoleList(element.dataset[ROLE_ATTR]);
    if (!allowed.length || allowed.includes(role)) {
      element.hidden = false;
      return;
    }
    element.hidden = true;
  });
}

export function enforceRoleAccess(user, allowedRoles, fallback = '/static/index.html') {
  const role = user?.role;
  if (!role || !allowedRoles.includes(role)) {
    window.location.href = fallback;
    return false;
  }
  return true;
}
