const refreshSelect = document.getElementById("refresh-interval");
const countdownEl = document.getElementById("refresh-countdown");

let refreshTimer = null;
let countdown = 0;

// Load saved setting
const savedInterval = localStorage.getItem("autoRefreshInterval");
if (savedInterval) {
    refreshSelect.value = savedInterval;
    startRefresh(savedInterval);
}

refreshSelect.addEventListener("change", () => {
    const interval = parseInt(refreshSelect.value);
    localStorage.setItem("autoRefreshInterval", interval);
    startRefresh(interval);
});

function startRefresh(interval) {
    if (refreshTimer) clearInterval(refreshTimer);

    if (interval > 0) {
        countdown = interval;
        countdownEl.textContent = `(${countdown}s)`;

        refreshTimer = setInterval(() => {
            countdown--;
            countdownEl.textContent = `(${countdown}s)`;

            if (countdown <= 0) {
                location.reload();
            }
        }, 1000);
    } else {
        countdownEl.textContent = "--";
    }
}