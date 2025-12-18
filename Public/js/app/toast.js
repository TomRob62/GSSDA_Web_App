export function createToastController(toastElement) {
  function show(message, isError = false) {
    toastElement.textContent = message;
    toastElement.classList.toggle('error', isError);
    toastElement.classList.add('show');
    setTimeout(() => {
      toastElement.classList.remove('show');
    }, 3000);
  }

  return { show };
}
