// --- Pomodoro Timer with Custom Durations, Auto-cycle, Progress Ring, and Sound ---

// Default settings
const DEFAULTS = {
    work: 25,
    shortBreak: 5,
    longBreak: 15,
    cyclesBeforeLong: 4,
    sound: "bell"
};

let settings = {...DEFAULTS};
let timer = null;
let running = false;
let paused = false;
let mode = "work"; // work, shortBreak, longBreak
let cycle = 1;
let timeLeft = settings.work * 60;
let totalTime = settings.work * 60;
let selectedTaskId = null;

// DOM elements
const timerEl = document.getElementById('timer');
const sessionLabel = document.getElementById('session-label');
const cycleInfo = document.getElementById('cycle-info');
const progressRing = document.getElementById('progress-ring-bar');
const settingsBtn = document.getElementById('settings-btn');
const modal = document.getElementById('pomodoro-settings-modal');
const closeModal = document.getElementById('close-settings');
const settingsForm = document.getElementById('pomodoro-settings-form');

// Progress ring setup
const RADIUS = 75;
const CIRCUM = 2 * Math.PI * RADIUS;
progressRing.setAttribute('stroke-dasharray', CIRCUM);
progressRing.setAttribute('stroke-dashoffset', CIRCUM);

// --- Settings Persistence ---
function loadSettings() {
    const saved = localStorage.getItem('pomodoroSettings');
    if (saved) {
        settings = {...settings, ...JSON.parse(saved)};
    }
}
function saveSettings() {
    localStorage.setItem('pomodoroSettings', JSON.stringify(settings));
}

// --- UI Update ---
function updateDisplay() {
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    timerEl.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    sessionLabel.textContent = mode === "work" ? "Work" : (mode === "shortBreak" ? "Short Break" : "Long Break");
    cycleInfo.textContent = mode === "work"
        ? `Pomodoro ${cycle} of ${settings.cyclesBeforeLong}`
        : (mode === "shortBreak"
            ? "Short Break"
            : "Long Break");
    updateProgressRing();

    // Show selected task in the dropdown if available
    const taskSelect = document.getElementById('pomodoro-task-select');
    if (taskSelect && selectedTaskId !== null) {
        taskSelect.value = selectedTaskId;
    }
}

function updateProgressRing() {
    let percent = 1 - (timeLeft / totalTime);
    let offset = CIRCUM * percent;
    progressRing.setAttribute('stroke-dashoffset', offset);
    // Color change for break
    if (mode === "work") {
        progressRing.setAttribute('stroke', '#43e97b');
    } else if (mode === "shortBreak") {
        progressRing.setAttribute('stroke', '#4f8cff');
    } else {
        progressRing.setAttribute('stroke', '#f7971e');
    }
}

// --- Timer Logic ---
function startTimer() {
    if (running) return;
    running = true;
    paused = false;
    timer = setInterval(() => {
        if (paused) return;
        if (timeLeft > 0) {
            timeLeft--;
            updateDisplay();
        } else {
            playSound();
            clearInterval(timer);
            running = false;
            nextSession();
        }
    }, 1000);
}

function pauseTimer() {
    paused = !paused;
    const pauseBtn = document.getElementById('pause-btn');
    if (paused) {
        pauseBtn.textContent = "Resume";
    } else {
        pauseBtn.textContent = "Pause";
    }
}

function resetTimer() {
    clearInterval(timer);
    running = false;
    paused = false;
    mode = "work";
    cycle = 1;
    timeLeft = settings.work * 60;
    totalTime = settings.work * 60;
    const pauseBtn = document.getElementById('pause-btn');
    if (pauseBtn) pauseBtn.textContent = "Pause";
    updateDisplay();
}

function nextSession() {
    if (mode === "work") {
        // Notify server of completed Pomodoro
        fetch('/api/pomodoro/complete', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded'},
            body: 'minutes=' + encodeURIComponent(settings.work)
        });
        if (cycle < settings.cyclesBeforeLong) {
            mode = "shortBreak";
            timeLeft = settings.shortBreak * 60;
            totalTime = timeLeft;
            cycleInfo.textContent = `Short Break`;
            cycle++;
        } else {
            mode = "longBreak";
            timeLeft = settings.longBreak * 60;
            totalTime = timeLeft;
            cycleInfo.textContent = `Long Break`;
            cycle = 1;
        }
    } else {
        mode = "work";
        timeLeft = settings.work * 60;
        totalTime = timeLeft;
        cycleInfo.textContent = `Pomodoro ${cycle} of ${settings.cyclesBeforeLong}`;
    }
    updateDisplay();
    setTimeout(() => { startTimer(); }, 800); // auto-start next session
}

// --- Sound ---
function playSound() {
    if (settings.sound === "none") return;
    let audioId = "sound-" + settings.sound;
    let audio = document.getElementById(audioId);
    if (audio) {
        audio.currentTime = 0;
        audio.play();
    }
}

// --- Settings Modal Logic ---
settingsBtn.onclick = function() {
    // Populate form with current settings
    document.getElementById('work-duration').value = settings.work;
    document.getElementById('short-break-duration').value = settings.shortBreak;
    document.getElementById('long-break-duration').value = settings.longBreak;
    document.getElementById('cycles-before-long').value = settings.cyclesBeforeLong;
    document.getElementById('sound-select').value = settings.sound;
    modal.style.display = "flex";
};
closeModal.onclick = function() {
    modal.style.display = "none";
};
window.onclick = function(event) {
    if (event.target === modal) modal.style.display = "none";
};
settingsForm.onsubmit = function(e) {
    e.preventDefault();
    settings.work = Math.max(1, parseInt(document.getElementById('work-duration').value));
    settings.shortBreak = Math.max(1, parseInt(document.getElementById('short-break-duration').value));
    settings.longBreak = Math.max(1, parseInt(document.getElementById('long-break-duration').value));
    settings.cyclesBeforeLong = Math.max(1, parseInt(document.getElementById('cycles-before-long').value));
    settings.sound = document.getElementById('sound-select').value;
    saveSettings();
    resetTimer();
    modal.style.display = "none";
};

// --- Default Button Logic ---
document.getElementById('default-settings-btn').onclick = function() {
    settings = {...DEFAULTS};
    saveSettings();
    // Update form fields to default values
    document.getElementById('work-duration').value = settings.work;
    document.getElementById('short-break-duration').value = settings.shortBreak;
    document.getElementById('long-break-duration').value = settings.longBreak;
    document.getElementById('cycles-before-long').value = settings.cyclesBeforeLong;
    document.getElementById('sound-select').value = settings.sound;
};

// --- Task Selection Logic ---
const taskSelect = document.getElementById('pomodoro-task-select');
if (taskSelect) {
    taskSelect.addEventListener('change', function() {
        selectedTaskId = this.value;
        localStorage.setItem('pomodoroSelectedTask', selectedTaskId);
    });
}

// --- Init ---
function initPomodoro() {
    loadSettings();
    // Restore selected task from localStorage
    selectedTaskId = localStorage.getItem('pomodoroSelectedTask') || null;
    resetTimer();
    // Set dropdown value if available
    const taskSelect = document.getElementById('pomodoro-task-select');
    if (taskSelect && selectedTaskId) {
        taskSelect.value = selectedTaskId;
    }
}
window.onload = initPomodoro;
