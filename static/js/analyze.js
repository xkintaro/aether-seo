document.getElementById('analyzeForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const input = document.getElementById('urlInput');
    const url = input.value.trim();

    if (url) {
        const modal = document.getElementById('loadingModal');
        const logContainer = document.getElementById('loadingLog');
        const statusText = document.getElementById('loadingStatus');

        modal.classList.remove('hidden');
        logContainer.innerHTML = '';

        const eventSource = new EventSource('/api/stream_analyze?url=' + encodeURIComponent(url));

        eventSource.onmessage = function (event) {
            const data = JSON.parse(event.data);

            if (data.msg) {
                const logItem = document.createElement('div');
                logItem.className = 'typewriter-item text-gray-300';
                logItem.innerHTML = `<span class="text-neon-pink">>></span> ${data.msg}`;
                logContainer.appendChild(logItem);
                logContainer.scrollTop = logContainer.scrollHeight;
                statusText.textContent = data.msg;
            }

            if (data.redirect) {
                eventSource.close();
                statusText.textContent = "REPORT GENERATED. REDIRECTING...";
                statusText.className = "text-neon-green font-mono text-lg animate-pulse";
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 800);
            }

            if (data.error) {
                eventSource.close();
                statusText.textContent = "ERROR: " + data.error;
                statusText.className = "text-red-500 font-bold text-lg";
                const logItem = document.createElement('div');
                logItem.className = 'typewriter-item text-red-500 font-bold';
                logItem.innerHTML = `<span class="text-red-500">!!</span> CRITICAL ERROR: ${data.error}`;
                logContainer.appendChild(logItem);
            }
        };

        eventSource.onerror = function () {
            eventSource.close();
            statusText.textContent = "Connection lost, please try again.";
            statusText.className = "text-red-500 font-bold text-lg";
            const logItem = document.createElement('div');
            logItem.className = 'typewriter-item text-red-500 font-bold';
            logItem.innerHTML = `<span class="text-red-500">!!</span> Server connection lost.`;
            logContainer.appendChild(logItem);
        };
    }
});

document.getElementById('urlInput').addEventListener('input', function (e) {
    let value = e.target.value;
    value = value.replace(/^https?:\/\//i, '');
    e.target.value = value;
});
