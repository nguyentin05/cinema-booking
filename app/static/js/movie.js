const movie_id = window.location.pathname.split('/').filter(Boolean).pop();
let currentSelectedDate = formatToYYYYMMDD(new Date());
const dateContainer = document.getElementById('date-container')
const dayNames = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

const prevBtn = document.createElement('button')
prevBtn.className = "btn btn-outline-secondary d-flex flex-column align-items-center justify-content-center py-2 me-2"
prevBtn.style.minWidth = "85px"
prevBtn.style.borderRadius = "10px"
prevBtn.innerHTML = `<span class="small fw-bold">Prev week</span><span class="fs-5">«</span>`


const nextBtn = document.createElement('button')
nextBtn.className = "btn btn-outline-secondary d-flex flex-column align-items-center justify-content-center py-2 ms-2"
nextBtn.style.minWidth = "85px"
nextBtn.style.borderRadius = "10px"
nextBtn.innerHTML = `<span class="small fw-bold">Next week</span><span class="fs-5">»</span>`

function formatToYYYYMMDD(dateObj) {
    let y = dateObj.getFullYear();
    let m = (dateObj.getMonth() + 1).toString().padStart(2, '0');
    let d = dateObj.getDate().toString().padStart(2, '0');
    return `${y}-${m}-${d}`;
}

async function renderShowtimes(movie_id, date) {
    const container = document.getElementById('showtime-container');

     if (container) {
        container.innerHTML = '<p class="text-center w-100 text-muted">Đang tải suất chiếu...</p>';
    }

    let showtimes = null
    try {
        const url = `/api/showtimes?movie_id=${movie_id}&date=${date}`;
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || "Có lỗi xảy ra khi lấy suất chiếu.");
        }
        showtimes = await response.json();
    } catch (error) {
        console.error("Lỗi fetchShowtimes:", error);

        if (container) {
            container.innerHTML = `<p class="text-danger w-100 text-center">Lỗi: ${error.message}</p>`;
        }
    }

    container.innerHTML = '';

    if (!showtimes || showtimes.length === 0) {
        container.innerHTML = '<p class="text-muted w-100 text-center">Không có suất chiếu nào cho ngày này.</p>';
        return;
    }

    let htmlContent = '';
    showtimes.forEach(st => {
        const start_at = new Date(st.start_at)
        const start_at_str = start_at.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });

        htmlContent += `
            <div class="text-center">
                <a href="/booking/${st.id}" class="btn showtime-btn">
                    ${start_at_str}
                </a>
            </div>
        `;
    });

    container.innerHTML = htmlContent;
}

renderShowtimes(movie_id, currentSelectedDate)
renderDates(new Date());


function renderDates(startDateStrOrObj) {
    let startDate = new Date(startDateStrOrObj);
    startDate.setHours(0, 0, 0, 0);

    let today = new Date();
    today.setHours(0, 0, 0, 0);

    if (startDate < today) {
        startDate = new Date(today);
    }

    dateContainer.innerHTML = '';

    if (startDate > today) {

        prevBtn.onclick = function() {
            let prevDate = new Date(startDate);
            prevDate.setDate(startDate.getDate() - 7);

            if (prevDate < today) {
                prevDate = new Date(today);
            }
            renderDates(prevDate);
        };
        dateContainer.appendChild(prevBtn);
    }

    let dayOfWeek = startDate.getDay();
    let daysToSunday = dayOfWeek === 0 ? 0 : 7 - dayOfWeek;

    for (let i = 0; i <= daysToSunday; i++) {
        let d = new Date(startDate);
        d.setDate(startDate.getDate() + i);

        let dateStr = formatToYYYYMMDD(d);
        let displayDate = `${d.getDate().toString().padStart(2, '0')}/${(d.getMonth() + 1).toString().padStart(2, '0')}`;

        let isToday = dateStr === formatToYYYYMMDD(today);
        let label = isToday ? "Today" : dayNames[d.getDay()];

        let activeClass = (dateStr === currentSelectedDate) ? "active" : "";

        let html = `
            <button class="btn date-btn ${activeClass} d-flex flex-column align-items-center py-2 text-decoration-none"
                    style="min-width: 100px;" date="${dateStr}">
                <span class="small mb-1 fw-bold">${label}</span>
                <span class="fs-5 fw-bold">${displayDate}</span>
            </button>
        `;

        dateContainer.insertAdjacentHTML('beforeend', html);
    }

    let nextMonday = new Date(startDate);
    nextMonday.setDate(startDate.getDate() + daysToSunday + 1);

    nextBtn.onclick = function() {
        renderDates(nextMonday);
    };

    dateContainer.appendChild(nextBtn);
}

dateContainer.addEventListener('click', function(event) {
    const clickedButton = event.target.closest('.date-btn');

    if (clickedButton) {
        currentSelectedDate = clickedButton.getAttribute('date');

        const allButtons = dateContainer.querySelectorAll('.date-btn');
        allButtons.forEach(btn => {
            btn.classList.remove('active');
        });

        clickedButton.classList.add('active');

        renderShowtimes(movie_id, currentSelectedDate)
    }
});