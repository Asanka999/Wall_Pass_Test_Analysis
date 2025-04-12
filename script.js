const videoFile = document.getElementById('videoFile');
const videoFeed = document.getElementById('videoFeed');
const videoPlaceholder = document.querySelector('.video-placeholder');
const notification = document.getElementById('notification');
const passCountElement = document.getElementById('passCount');
const timerElement = document.getElementById('timer');
const passFPSElement = document.getElementById('passFPS');
const trajectoryPath = document.getElementById('trajectoryPath');
const ballPosition = document.getElementById('ballPosition');
const settingsModal = document.getElementById('settingsModal');
const closeModal = document.getElementById('closeModal');
const saveSettings = document.getElementById('saveSettings');

// State variables
let isRunning = false;
let passCount = 0;
let startTime = null;
let timerInterval = null;
let trajectoryPoints = [];
let chart = null;
let audioEnabled = false;
let passSound = null;

// Initialize Charts
function initializeChart() {
    const ctx = document.createElement('canvas');
    document.getElementById('passGraph').appendChild(ctx);
   
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Passes Over Time',
                data: [],
                backgroundColor: 'rgba(52, 152, 219, 0.2)',
                borderColor: 'rgba(52, 152, 219, 1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#ecf0f1'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#ecf0f1'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#ecf0f1'
                    }
                }
            }
        }
    });
}

// Show notification
function showNotification(message) {
    notification.textContent = message;
    notification.classList.add('show');
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Update timer
function updateTimer() {
    const now = Date.now();
    const elapsed = Math.floor((now - startTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    timerElement.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

// Reset stats
function resetStats() {
    passCount = 0;
    passCountElement.textContent = '0';
    passFPSElement.textContent = '0';
    clearInterval(timerInterval);
    timerElement.textContent = '00:00';
    startTime = null;
    trajectoryPoints = [];
    chart.data.labels = [];
    chart.data.datasets[0].data = [];
    chart.update();
    showNotification('Stats reset successfully!');
}

// Toggle detection
function toggleDetection() {
    if (isRunning) {
        // Stop detection
        isRunning = false;
        startButton.textContent = 'Start Detection';
        startButton.classList.add('pulse');
        clearInterval(timerInterval);
        videoFeed.pause();
        videoPlaceholder.style.display = 'flex';
        videoFeed.style.display = 'none';
        showNotification('Detection stopped.');
    } else {
        // Start detection
        isRunning = true;
        startButton.textContent = 'Stop Detection';
        startButton.classList.remove('pulse');
        startTime = Date.now();
        timerInterval = setInterval(updateTimer, 1000);
        videoFeed.style.display = 'block';
        videoPlaceholder.style.display = 'none';
        showNotification('Detection started.');
    }
}

// Populate camera list
async function populateCameraList() {
    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const cameras = devices.filter(device => device.kind === 'videoinput');
        cameraSelect.innerHTML = cameras.map((camera, index) => `
            <option value="${index}">${camera.label || `Camera ${index + 1}`}</option>
        `).join('');
    } catch (error) {
        console.error('Error accessing cameras:', error);
    }
}

// Initialize the application
function init() {
    // Populate camera list
    populateCameraList();
   
    // Initialize chart
    initializeChart();
   
    // Event listeners
    videoSourceSelect.addEventListener('change', function() {
        if (this.value === 'file') {
            fileUploadGroup.style.display = 'block';
            webcamSelectGroup.style.display = 'none';
        } else {
            fileUploadGroup.style.display = 'none';
            webcamSelectGroup.style.display = 'block';
        }
    });
   
    startButton.addEventListener('click', toggleDetection);
    resetButton.addEventListener('click', resetStats);
    settingsButton.addEventListener('click', () => settingsModal.style.display = 'flex');
    closeModal.addEventListener('click', () => settingsModal.style.display = 'none');
    saveSettings.addEventListener('click', () => {
        settingsModal.style.display = 'none';
        showNotification('Settings saved successfully!');
    });
   
    // Close modal if clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === settingsModal) {
            settingsModal.style.display = 'none';
        }
    });
}

// Initialize the app
init();