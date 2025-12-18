export function createCell(content, { className, html } = {}) {
  const cell = document.createElement('td');
  if (className) cell.className = className;
  if (html) {
    cell.innerHTML = html;
  } else if (content instanceof Node) {
    cell.appendChild(content);
  } else {
    cell.textContent = content;
  }
  return cell;
}

export function createRow(cells) {
  const row = document.createElement('tr');
  cells.forEach((cell) => row.appendChild(cell));
  return row;
}

export function createActionsCell(onEdit, onDelete) {
  const cell = document.createElement('td');
  cell.className = 'actions-cell';
  const wrapper = document.createElement('div');
  wrapper.className = 'actions';
  const edit = document.createElement('button');
  edit.className = 'secondary';
  edit.textContent = 'Edit';
  edit.addEventListener('click', onEdit);
  const del = document.createElement('button');
  del.className = 'danger';
  del.textContent = 'Delete';
  del.addEventListener('click', onDelete);
  wrapper.appendChild(edit);
  wrapper.appendChild(del);
  cell.appendChild(wrapper);
  return cell;
}
