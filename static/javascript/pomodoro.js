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

// --- Timer State Persistence ---
function saveTimerState() {
    const state = {
        mode,
        cycle,
        timeLeft,
        totalTime,
        running,
        paused,
        selectedTaskId,
        timestamp: Date.now()
    };
    localStorage.setItem('pomodoroTimerState', JSON.stringify(state));
}
function loadTimerState() {
    const stateStr = localStorage.getItem('pomodoroTimerState');
    if (!stateStr) return false;
    try {
        const state = JSON.parse(stateStr);
        mode = state.mode || "work";
        cycle = state.cycle || 1;
        totalTime = state.totalTime || (settings.work * 60);
        selectedTaskId = state.selectedTaskId || null;
        running = !!state.running;
        paused = !!state.paused;
        // Adjust timeLeft if timer was running and not paused
        if (state.running && !state.paused && state.timestamp) {
            const elapsed = Math.floor((Date.now() - state.timestamp) / 1000);
            timeLeft = Math.max(0, (state.timeLeft || totalTime) - elapsed);
        } else {
            timeLeft = state.timeLeft || totalTime;
        }
        return true;
    } catch {
        return false;
    }
}
function clearTimerState() {
    localStorage.removeItem('pomodoroTimerState');
}

// --- UI Update ---
function updateDisplay() {
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    timerEl.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
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
    // Update Games button state if present
    if (typeof updateGamesButtonState === "function") {
        updateGamesButtonState(mode);
    }
    saveTimerState();
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
function startTimer(force) {
    if (timer && !force) return;
    clearInterval(timer);
    running = true;
    paused = false;
    
    // Store task name for popout timer
    const taskSelect = document.getElementById('pomodoro-task-select');
    if (taskSelect && taskSelect.selectedIndex >= 0) {
        const selectedOption = taskSelect.options[taskSelect.selectedIndex];
        const taskName = selectedOption.textContent;
        const state = JSON.parse(localStorage.getItem('pomodoroTimerState') || '{}');
        state.selectedTaskName = taskName;
        localStorage.setItem('pomodoroTimerState', JSON.stringify(state));
    }
    
    saveTimerState();
    
    // Show popout timer when starting
    localStorage.setItem('popoutTimerVisible', 'true');
    
    timer = setInterval(() => {
        if (paused) return;
        if (timeLeft > 0) {
            timeLeft--;
            updateDisplay();
            saveTimerState();
        } else {
            playSound();
            clearInterval(timer);
            running = false;
            saveTimerState();
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
    saveTimerState();
}

function resetTimer() {
    clearInterval(timer);
    timer = null;
    running = false;
    paused = false;
    mode = "work";
    cycle = 1;
    timeLeft = settings.work * 60;
    totalTime = settings.work * 60;
    const pauseBtn = document.getElementById('pause-btn');
    if (pauseBtn) pauseBtn.textContent = "Pause";
    updateDisplay();
    clearTimerState();
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
            cycle++;
        } else {
            mode = "longBreak";
            timeLeft = settings.longBreak * 60;
            totalTime = timeLeft;
            cycle = 1;
        }
        updateDisplay();
        // Always auto-start the break timer immediately, even if timer is already running
        startTimer(true);
    } else {
        // If timer ends during a break, set up work session but don't auto-start
        mode = "work";
        timeLeft = settings.work * 60;
        totalTime = settings.work * 60;
        updateDisplay();
        saveTimerState();
        
        // If on /pomodoro/games, let the games page handle the transition
        if (window.location.pathname.startsWith('/pomodoro/games')) {
            // Games page will detect break expiration and redirect
            return;
        } else {
            // Start work timer immediately only if on main pomodoro page
            startTimer(true);
        }
    }
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
    // Try to restore timer state
    if (loadTimerState()) {
        updateDisplay();
        // Set dropdown value if available
        const taskSelect = document.getElementById('pomodoro-task-select');
        if (taskSelect && selectedTaskId) {
            taskSelect.value = selectedTaskId;
        }
        if (running && !paused && timeLeft > 0) {
            startTimer();
        }
    } else {
        resetTimer();
        // Set dropdown value if available
        const taskSelect = document.getElementById('pomodoro-task-select');
        if (taskSelect && selectedTaskId) {
            taskSelect.value = selectedTaskId;
        }
    }
}
window.onload = initPomodoro;
