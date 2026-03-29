const showtime_id = window.location.pathname.split('/').filter(Boolean).pop();
const selectedSeats = [];
const el = document.getElementById('already_booked_seats');
let selectedSeatsCount = 0;
if (el) {
    selectedSeatsCount = parseInt(el.textContent, 10) || 0;
}

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
        selectedSeatsCount--;

        seatEl.classList.remove('bg-primary', 'opacity-50');
        const bgClasses = originalBg.split(' ');
        seatEl.classList.add(...bgClasses);
    } else {
        if (selectedSeatsCount >= 8) {
            alert("You can only book a maximum of 8 seats per showtime.")
        } else {
            selectedSeats.push({
                id: seatId,
                name: seatName,
                type: seatType,
                price: parseFloat(seatPrice)
            });
             selectedSeatsCount++;

            const bgClasses = originalBg.split(' ');
            seatEl.classList.remove(...bgClasses);
            seatEl.classList.add('bg-primary', 'opacity-50');
        }
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
        <button onclick="submitBooking()" class="btn btn-success w-100 py-3 fw-bold rounded-3">
            TIẾP TỤC
        </button>
    `;
}

async function submitBooking() {
    if (!selectedSeats || selectedSeats.length === 0) {
        alert("Vui lòng chọn ít nhất 1 ghế trước khi đặt!");
        return;
    }

    try {
        const response = await fetch("/api/bookings", {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                showtime_id: showtime_id,
                seat_ids: selectedSeats.map(s => s.id)
            })
        });
        const data = await response.json();

        if (!response.ok) {
            const errorMessage = data.message || data.error || "Có lỗi xảy ra từ máy chủ.";
            throw new Error(errorMessage);
        }

        alert(data.message);
        location.reload();

    } catch (err) {
        console.error("Lỗi đặt vé:", err);
        alert(err.message || "Không thể kết nối đến máy chủ. Vui lòng kiểm tra lại mạng!");
    }
}

renderSidebar();