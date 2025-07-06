    function updateClock() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString('en-GB', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false,
            timeZone: 'UTC'
        });
        document.getElementById('currentTime').textContent = `🕒 UTC ${timeStr}`;
    }

    setInterval(updateClock, 1000);
    updateClock();