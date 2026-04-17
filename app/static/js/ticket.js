const qrModal     = new bootstrap.Modal(document.getElementById('qrModal'));
const cancelModal = new bootstrap.Modal(document.getElementById('cancelModal'));
const toastEl     = new bootstrap.Toast(document.getElementById('toast'), { delay: 3500 });

let currentFilter = 'ACTIVE';
let pendingTicketId = null;
let tickets = [];

// ── Helpers ────────────────────────────────────────────────
function formatDateTime(iso) {
	const d = new Date(iso);
	return d.toLocaleString('vi-VN', {
	  hour: '2-digit', minute: '2-digit',
	  day: '2-digit', month: '2-digit', year: 'numeric'
	});
}

function formatCurrency(amount) {
	return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount);
}

function showToast(message, type = 'success') {
	const el = document.getElementById('toast');
	el.className = `toast text-white border-0 bg-${type}`;
	document.getElementById('toast-msg').textContent = message;
	toastEl.show();
}

// ── Render ─────────────────────────────────────────────────
function actionButtonsHTML(ticket) {
	if (ticket.status !== 'ACTIVE') return '';
	return `
	  <div class="d-flex gap-2 mt-2">
		<button class="btn btn-sm btn-outline-primary" onclick="showQR(${ticket.id})">
		  Mã QR
		</button>
		<button class="btn btn-sm btn-outline-danger"
				onclick="openCancelModal(${ticket.id}, '${ticket.showtime.movie_title}', '${ticket.seat.name}')">
		  Hủy vé
		</button>
	  </div>`;
}

function statusBadge(status) {
	const map = {
	  ACTIVE:    ['bg-success-subtle text-success border-success-subtle',   'Sắp chiếu'],
	  USED:      ['bg-secondary-subtle text-secondary border-secondary-subtle', 'Đã xem'],
	  CANCELLED: ['bg-danger-subtle text-danger border-danger-subtle',       'Đã hủy'],
	};
	const [cls, label] = map[status] || ['bg-light text-muted', status];
	return `<span class="badge rounded-pill border ${cls}">${label}</span>`;
}

function renderTicket(ticket) {
return `
  <div class="card border-0 shadow-sm ticket-card"
	   data-status="${ticket.status}"
	   data-ticket-id="${ticket.id}"
	   style="opacity: ${ticket.status === 'CANCELLED' ? '0.6' : '1'}">
	<div class="card-body p-0">
	  <div class="row g-0">

		<div class="col-auto">
		  <img src="${ticket.showtime.movie_poster_url || 'https://placehold.co/90x130/1a1a2e/white?text=No+Poster'}"
			   alt="Poster"
			   class="rounded-start object-fit-cover"
			   style="width:90px; height:100%; min-height:130px">
		</div>

		<div class="col p-3 d-flex flex-column justify-content-between">
		  <div>
			<div class="d-flex justify-content-between align-items-start gap-2 mb-1">
			  <h6 class="fw-semibold mb-0 lh-sm">${ticket.showtime.movie_title}</h6>
			  ${statusBadge(ticket.status)}
			</div>
			<p class="text-muted small mb-1">
			  <strong>Phòng:</strong> ${ticket.showtime.room_name}<br>
			  <strong>Ghế:</strong> ${ticket.seat.name} (${ticket.seat.type})<br>
			  <strong>Giờ chiếu:</strong> ${formatDateTime(ticket.showtime.start_at)}
			</p>
		  </div>
		  <div class="d-flex align-items-center justify-content-between flex-wrap gap-2">
			<span class="fw-semibold text-primary">${formatCurrency(ticket.price)}</span>
			${actionButtonsHTML(ticket)}
		  </div>
		</div>

	  </div>
	</div>
  </div>`;
}

function renderList() {
	const list = document.getElementById('ticketList');
	if (!tickets || tickets.length === 0) {
	  list.innerHTML = `
		<div class="text-center py-5 text-muted">
		  <p class="mb-0">Không có vé nào trong mục này.</p>
		</div>`;
	  return;
	}
	list.innerHTML = tickets.map(renderTicket).join('');
}

// ── Filter buttons ─────────────────────────────────────────
document.getElementById('filterContainer').addEventListener('click', e => {
    const btn = e.target.closest('[data-filter]');
    if (!btn) return;

    if (currentFilter === btn.dataset.filter) return;

    currentFilter = btn.dataset.filter;

    document.querySelectorAll('#filterContainer [data-filter]').forEach(b => {
      b.className = b.dataset.filter === currentFilter
       ? 'btn btn-primary btn-sm'
       : 'btn btn-outline-secondary btn-sm';
    });

    loadTickets(currentFilter);
});

// ── QR Modal ───────────────────────────────────────────────
window.showQR = function(ticketId) {
	const ticket = tickets.find(t => t.id === ticketId);
	if (!ticket) return;
	document.getElementById('qr-img-wrapper').innerHTML =
	  `<img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(ticket.qr_payload)}"
			class="img-fluid rounded" alt="QR">`;
	document.getElementById('qr-seat-label').textContent =
	  `${ticket.showtime.movie_title} · Ghế ${ticket.seat.name}`;
	qrModal.show();
};

// ── Cancel Modal ───────────────────────────────────────────
window.openCancelModal = function(ticketId, movie, seat) {
	pendingTicketId = ticketId;
	document.getElementById('modal-movie').textContent = movie;
	document.getElementById('modal-seat').textContent  = seat;
	cancelModal.show();
};

document.getElementById('confirm-cancel-btn').addEventListener('click', async () => {
	if (!pendingTicketId) return;
	const spinner    = document.getElementById('cancel-spinner');
	const confirmBtn = document.getElementById('confirm-cancel-btn');
	spinner.classList.remove('d-none');
	confirmBtn.disabled = true;

	try {
	  const res  = await fetch(`/api/tickets/${pendingTicketId}/cancel`, { method: 'PUT' });
	  const data = await res.json();

	  if (res.ok) {
		tickets = tickets.filter(t => t.id !== pendingTicketId);
		renderList();
		showToast('Hủy vé thành công. Tiền hoàn trong 5–10 ngày.', 'success');
	  } else {
		showToast(data.error || 'Hủy vé thất bại.', 'danger');
	  }
	} catch (error) {
		console.log(error)
	  showToast(error.response?.data?.error || 'Lỗi kết nối, vui lòng thử lại.', 'danger');
	} finally {
	  spinner.classList.add('d-none');
	  confirmBtn.disabled = false;
	  cancelModal.hide();
	  pendingTicketId = null;
	}
});

// ── Load data ──────────────────────────────────────────────
async function loadTickets(status) {
    const list = document.getElementById('ticketList');

    list.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Đang tải...</span>
            </div>
        </div>`;

    try {
      const res = await fetch(`/api/tickets/me?status=${status}`);
      if (!res.ok) throw new Error('API Error');

      tickets = await res.json();
      renderList();
    } catch {
      list.innerHTML =
        `<div class="alert alert-danger m-3">Không thể tải dữ liệu vé. Vui lòng kiểm tra lại kết nối.</div>`;
    }
}

loadTickets(currentFilter);