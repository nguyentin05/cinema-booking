const showtime_id = window.location.pathname.split('/').filter(Boolean).pop();
const selectedSeats = [];

document.querySelector('.seating-wrapper').addEventListener('click', function(e) {
    const seatEl = e.target.closest('.available-seat');
    if (!seatEl) return;

    const seatId = seatEl.getAttribute('data-seat-id');
    const seatName = seatEl.getAttribute('data-seat-name');
    const seatType = seatEl.getAttribute('data-seat-type');
    const originalBg = seatEl.getAttribute('data-original-bg');
    const seatPrice = seatEl.getAttribute('data-seat-price');

    const seatIndex = selectedSeats.findIndex(s => s.id === seatId);

    if (seatIndex > -1) {
        selectedSeats.splice(seatIndex, 1);

        seatEl.classList.remove('bg-primary', 'opacity-50');
        const bgClasses = originalBg.split(' ');
        seatEl.classList.add(...bgClasses);
    } else {
        selectedSeats.push({
            id: seatId,
            name: seatName,
            type: seatType,
            price: parseFloat(seatPrice)
        });

        const bgClasses = originalBg.split(' ');
        seatEl.classList.remove(...bgClasses);
        seatEl.classList.add('bg-primary', 'opacity-50');
    }

    renderSidebar();
});

function renderSidebar() {
    const sidebar = document.getElementById('selected_seat');

    if (selectedSeats.length === 0) {
        sidebar.innerHTML = `
            <div class="text-center text-muted my-5">
                <p>Vui lòng chọn ghế trong sơ đồ.</p>
            </div>
        `;
        return;
    }

    let ticketsHtml = '';
    let totalPrice = 0;
    const groupedSeats = {};

    selectedSeats.forEach(seat => {
        totalPrice += seat.price;

        if (!groupedSeats[seat.type]) {
            groupedSeats[seat.type] = {
                count: 0,
                names: [],
                totalPriceForType: 0
            };
        }

        groupedSeats[seat.type].count += 1;
        groupedSeats[seat.type].names.push(seat.name);
        groupedSeats[seat.type].totalPriceForType += seat.price;
    });

    for (const [type, data] of Object.entries(groupedSeats)) {
        ticketsHtml += `
            <div class="d-flex justify-content-between align-items-center mb-3">
                <div>
                    <div class="fw-bold small">${data.count} x Adult-${type}</div>
                    <div class="text-muted small">Ghế: <span class="fw-bold text-dark">${data.names.join(', ')}</span></div>
                </div>
                <div class="fw-bold small">${data.totalPriceForType.toLocaleString('vi-VN')} VND</div>
            </div>
        `;
    }

    sidebar.innerHTML = `
        <h5 class="fw-bold mb-4">Ghế đã chọn (${selectedSeats.length})</h5>
        <div id="tickets-list">
            ${ticketsHtml}
        </div>
        <div class="border-bottom border-dashed my-3"></div>
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h5 class="fw-bold mb-0">Tổng tiền</h5>
            <h4 class="fw-bold mb-0 text-dark">${totalPrice.toLocaleString('vi-VN')} VND</h4>
        </div>
        <button onclick="proceedToCheckout()" class="btn btn-success w-100 py-3 fw-bold rounded-3">
            TIẾP TỤC
        </button>
    `;
}

function proceedToCheckout() {
    const seatIds = selectedSeats.map(s => s.id);
    console.log("Chuẩn bị gọi API giữ chỗ cho các ghế ID:", seatIds);
    // Chuyển trang hoặc gọi API giữ chỗ (HOLDING) ở đây...
}

renderSidebar();