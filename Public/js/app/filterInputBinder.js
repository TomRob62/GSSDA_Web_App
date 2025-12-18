export function createFilterInputBinder(filterController) {
  return function bind(loadList) {
    const input = filterController.activeInput;
    if (!input) return;
    if (input.tagName === 'SELECT') {
      input.addEventListener('change', () => loadList());
      return;
    }
    input.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter') return;
      event.preventDefault();
      loadList();
    });
  };
}
