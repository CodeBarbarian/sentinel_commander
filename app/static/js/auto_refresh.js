const refreshSelect = document.getElementById("refresh-interval");
const countdownEl = document.getElementById("refresh-countdown");

let refreshTimer = null;
let countdown = 0;

// Ensure only one listener ever binds
refreshSelect.addEventListener("change", handleIntervalChange);

// On load, initialize saved setting
(function initAutoRefresh() {
    const savedInterval = parseInt(localStorage.getItem("autoRefreshInterval"));
    if (!isNaN(savedInterval)) {
        refreshSelect.value = savedInterval;
        startRefresh(savedInterval);
    }
})();

function handleIntervalChange() {
    const interval = parseInt(refreshSelect.value);
    if (isNaN(interval) || interval < 0 || interval > 3600) { // optional upper bound
        alert("Invalid refresh interval");
        return;
    }

    localStorage.setItem("autoRefreshInterval", interval);
    startRefresh(interval);
}

function startRefresh(interval) {
    if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
    }

    if (interval > 0) {
        countdown = interval;
        updateCountdownDisplay();

        refreshTimer = setInterval(() => {
            countdown--;
            updateCountdownDisplay();

            if (countdown <= 0) {
                clearInterval(refreshTimer);
                refreshTimer = null;
                location.reload();
            }
        }, 1000);
    } else {
        countdownEl.textContent = "--";
    }
}

function updateCountdownDisplay() {
    countdownEl.textContent = `(${countdown}s)`;
}
