const App = {
  csrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.content : '';
  },

  formatMoney(val) {
    if (val === null || val === undefined || val === '') return '0,00 ₺';
    return new Intl.NumberFormat('tr-TR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(parseFloat(val)) + ' ₺';
  },

  parseMoney(str) {
    if (!str) return 0;
    return parseFloat(String(str).replace(/\./g, '').replace(',', '.')) || 0;
  },

  async post(url, data) {
    const resp = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': this.csrfToken()
      },
      body: JSON.stringify(data)
    });
    return resp.json();
  },

  async get(url) {
    const resp = await fetch(url);
    return resp.json();
  },

  showToast(msg, type = 'success') {
    const container = document.getElementById('toast-container') || (() => {
      const d = document.createElement('div');
      d.id = 'toast-container';
      d.className = 'position-fixed bottom-0 end-0 p-3';
      d.style.zIndex = 9999;
      document.body.appendChild(d);
      return d;
    })();

    const id = 'toast-' + Date.now();
    container.insertAdjacentHTML('beforeend', `
      <div id="${id}" class="toast align-items-center text-bg-${type} border-0" role="alert">
        <div class="d-flex">
          <div class="toast-body">${msg}</div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
      </div>
    `);
    const el = document.getElementById(id);
    new bootstrap.Toast(el, { delay: 3000 }).show();
    el.addEventListener('hidden.bs.toast', () => el.remove());
  },

  confirmDelete(msg) {
    return confirm(msg || 'Bu kaydı silmek istediğinizden emin misiniz?');
  }
};

// Auto-dismiss alerts after 5s
document.querySelectorAll('.alert').forEach(el => {
  setTimeout(() => {
    const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
    if (bsAlert) bsAlert.close();
  }, 5000);
});
