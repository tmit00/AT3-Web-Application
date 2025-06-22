// Popout Pomodoro Timer - Persistent across routes
(function() {
    'use strict';

    // Default settings (should match main pomodoro.js)
    const DEFAULTS = {
        work: 25,
        shortBreak: 5,
        longBreak: 15,
        cyclesBeforeLong: 4,
        sound: "bell"
    };

    let settings = {...DEFAULTS};
    let popoutTimer = null;
    let isRunning = false;
    let isPaused = false;
    let mode = "work";
    let cycle = 1;
    let timeLeft = settings.work * 60;
    let totalTime = settings.work * 60;
    let selectedTaskId = null;
    let selectedTaskName = "No task selected";
    let isDragging = false;
    let dragOffset = { x: 0, y: 0 };

    // DOM Elements
    const popoutContainer = document.getElementById('popout-pomodoro-timer');
    const popoutContent = document.getElementById('popout-content');
    const popoutMinimized = document.getElementById('popout-minimized');
    const popoutProgressBar = document.getElementById('popout-progress-bar');
    const popoutProgressRing = document.getElementById('popout-progress-ring');
    const popoutTimerTime = document.getElementById('popout-timer-time');
    const popoutTimerMode = document.getElementById('popout-timer-mode');
    const popoutMiniTime = document.getElementById('popout-mini-time');
    const popoutMiniMode = document.getElementById('popout-mini-mode');
    const popoutCycleText = document.getElementById('popout-cycle-text');
    const popoutTaskInfo = document.getElementById('popout-task-info');
    const popoutTaskName = document.getElementById('popout-task-name');

    // Control buttons
    const startBtn = document.getElementById('popout-start-btn');
    const pauseBtn = document.getElementById('popout-pause-btn');
    const resetBtn = document.getElementById('popout-reset-btn');
    const gamesBtn = document.getElementById('popout-games-btn');
    const expandBtn = document.getElementById('popout-expand-btn');
    const minimizeBtn = document.getElementById('popout-minimize-btn');
    const closeBtn = document.getElementById('popout-close-btn');
    const dragHandle = document.querySelector('.popout-drag-handle');

    // Progress ring setup
    const RADIUS = 35;
    const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
    if (popoutProgressBar) {
        popoutProgressBar.setAttribute('stroke-dasharray', CIRCUMFERENCE);
        popoutProgressBar.setAttribute('stroke-dashoffset', CIRCUMFERENCE);
        popoutProgressBar.style.transform = 'rotate(-90deg)';
        popoutProgressBar.style.transformOrigin = 'center';
    }

    // Load settings from localStorage
    function loadSettings() {
        const saved = localStorage.getItem('pomodoroSettings');
        if (saved) {
            try {
                settings = {...settings, ...JSON.parse(saved)};
            } catch (e) {
                console.warn('Failed to load settings:', e);
            }
        }
    }

    // Load timer state from localStorage
    function loadTimerState() {
        const stateStr = localStorage.getItem('pomodoroTimerState');
        if (!stateStr) return false;
        
        try {
            const state = JSON.parse(stateStr);
            mode = state.mode || "work";
            cycle = state.cycle || 1;
            totalTime = state.totalTime || (settings.work * 60);
            selectedTaskId = state.selectedTaskId || null;
            isRunning = !!state.running;
            isPaused = !!state.paused;
            
            // Adjust timeLeft if timer was running and not paused
            if (state.running && !state.paused && state.timestamp) {
                const elapsed = Math.floor((Date.now() - state.timestamp) / 1000);
                timeLeft = Math.max(0, (state.timeLeft || totalTime) - elapsed);
            } else {
                timeLeft = state.timeLeft || totalTime;
            }
            
            // Load task name
            selectedTaskName = state.selectedTaskName || "No task selected";
            
            return true;
        } catch (e) {
            console.warn('Failed to load timer state:', e);
            return false;
        }
    }

    // Save timer state to localStorage
    function saveTimerState() {
        const state = {
            mode,
            cycle,
            timeLeft,
            totalTime,
            running: isRunning,
            paused: isPaused,
            selectedTaskId,
            selectedTaskName,
            timestamp: Date.now()
        };
        localStorage.setItem('pomodoroTimerState', JSON.stringify(state));
    }

    // Update the display
    function updateDisplay() {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        const timeStr = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        
        // Update timer displays
        if (popoutTimerTime) popoutTimerTime.textContent = timeStr;
        if (popoutMiniTime) popoutMiniTime.textContent = timeStr;
        
        // Update mode displays
        let modeText = mode === "work" ? "Work" : 
                     mode === "shortBreak" ? "Break" : "Long Break";
        if (popoutTimerMode) popoutTimerMode.textContent = modeText;
        if (popoutMiniMode) popoutMiniMode.textContent = modeText;
        
        // Update cycle info
        if (popoutCycleText) {
            popoutCycleText.textContent = mode === "work" 
                ? `Pomodoro ${cycle} of ${settings.cyclesBeforeLong}`
                : (mode === "shortBreak" ? "Short Break" : "Long Break");
        }
        
        // Update task info
        if (popoutTaskName) popoutTaskName.textContent = selectedTaskName;
        if (popoutTaskInfo) {
            popoutTaskInfo.style.display = selectedTaskId ? "block" : "none";
        }
        
        // Update progress ring
        updateProgressRing();
        
        // Update button states
        updateButtonStates();
    }

    // Update progress ring
    function updateProgressRing() {
        if (!popoutProgressBar) return;
        
        const progress = totalTime > 0 ? (timeLeft / totalTime) : 0;
        const offset = CIRCUMFERENCE * (1 - progress);
        popoutProgressBar.setAttribute('stroke-dashoffset', offset);
        
        // Change color based on mode
        const color = mode === "work" ? "#43e97b" : 
                     mode === "shortBreak" ? "#4f8cff" : "#ff9800";
        popoutProgressBar.setAttribute('stroke', color);
    }

    // Update button states
    function updateButtonStates() {
        if (!startBtn || !pauseBtn) return;
        
        if (isRunning && !isPaused) {
            startBtn.style.display = 'none';
            pauseBtn.style.display = 'inline-block';
        } else {
            startBtn.style.display = 'inline-block';
            pauseBtn.style.display = 'none';
        }
        
        // Update games button state
        updateGamesButtonState();
    }

    // Update games button state
    function updateGamesButtonState() {
        if (!gamesBtn) return;
        
        if (mode === "shortBreak" || mode === "longBreak") {
            gamesBtn.classList.remove('disabled');
            gamesBtn.style.pointerEvents = "auto";
            gamesBtn.style.opacity = "1";
            gamesBtn.title = "Play a game during your break!";
        } else {
            gamesBtn.classList.add('disabled');
            gamesBtn.style.pointerEvents = "none";
            gamesBtn.style.opacity = "0.5";
            gamesBtn.title = "Games are only available during breaks";
        }
    }

    // Expose function globally for synchronization with main timer
    window.updatePopoutGamesButtonState = function(newMode) {
        if (newMode !== mode) {
            mode = newMode;
            updateGamesButtonState();
        }
    };

    // Start timer
    function startTimer() {
        if (timeLeft <= 0) return;
        
        isRunning = true;
        isPaused = false;
        
        if (popoutTimer) clearInterval(popoutTimer);
        
        popoutTimer = setInterval(() => {
            if (timeLeft > 0) {
                timeLeft--;
                updateDisplay();
                saveTimerState();
            } else {
                // Timer finished
                clearInterval(popoutTimer);
                isRunning = false;
                isPaused = false;
                
                // Play sound if enabled
                playSound();
                
                // Auto-advance to next session
                advanceSession();
            }
        }, 1000);
        
        updateDisplay();
        saveTimerState();
    }

    // Pause timer
    function pauseTimer() {
        if (!isRunning) return;
        
        isPaused = true;
        clearInterval(popoutTimer);
        updateDisplay();
        saveTimerState();
    }

    // Reset timer
    function resetTimer() {
        clearInterval(popoutTimer);
        isRunning = false;
        isPaused = false;
        
        // Reset to current mode's duration
        if (mode === "work") {
            timeLeft = settings.work * 60;
            totalTime = settings.work * 60;
        } else if (mode === "shortBreak") {
            timeLeft = settings.shortBreak * 60;
            totalTime = settings.shortBreak * 60;
        } else {
            timeLeft = settings.longBreak * 60;
            totalTime = settings.longBreak * 60;
        }
        
        updateDisplay();
        saveTimerState();
    }

    // Advance to next session
    function advanceSession() {
        if (mode === "work") {
            // Work session finished, start break
            if (cycle >= settings.cyclesBeforeLong) {
                // Long break
                mode = "longBreak";
                timeLeft = settings.longBreak * 60;
                totalTime = settings.longBreak * 60;
                cycle = 1; // Reset cycle after long break
            } else {
                // Short break
                mode = "shortBreak";
                timeLeft = settings.shortBreak * 60;
                totalTime = settings.shortBreak * 60;
                cycle++; // Increment cycle
            }
        } else {
            // Break finished, start work
            mode = "work";
            timeLeft = settings.work * 60;
            totalTime = settings.work * 60;
        }
        
        updateDisplay();
        saveTimerState();
        
        // Auto-start next session after a brief pause, unless on games page
        if (!window.location.pathname.startsWith('/pomodoro/games')) {
            setTimeout(() => {
                startTimer();
            }, 1000);
        }
    }

    // Play notification sound
    function playSound() {
        if (settings.sound === "none") return;
        
        // Try to find audio element
        const audioId = "sound-" + settings.sound;
        let audio = document.getElementById(audioId);
        
        if (!audio) {
            // Create audio element if not found
            audio = document.createElement('audio');
            audio.id = audioId;
            const audioFiles = {
                bell: '/static/audio/bell-notification-337658.mp3',
                chime: '/static/audio/new-notification-03-323602.mp3',
                beep: '/static/audio/notification-beep-229154.mp3'
            };
            audio.src = audioFiles[settings.sound] || audioFiles.bell;
            document.body.appendChild(audio);
        }
        
        if (audio) {
            audio.currentTime = 0;
            audio.play().catch(e => console.warn('Could not play sound:', e));
        }
    }

    // Dragging functionality
    function initializeDragging() {
        if (!dragHandle || !popoutContainer) return;
        
        dragHandle.addEventListener('mousedown', startDrag);
        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', stopDrag);
    }

    function startDrag(e) {
        isDragging = true;
        const rect = popoutContainer.getBoundingClientRect();
        dragOffset.x = e.clientX - rect.left;
        dragOffset.y = e.clientY - rect.top;
        popoutContainer.style.cursor = 'grabbing';
        e.preventDefault();
    }

    function drag(e) {
        if (!isDragging) return;
        
        const x = e.clientX - dragOffset.x;
        const y = e.clientY - dragOffset.y;
        
        // Keep within viewport bounds
        const maxX = window.innerWidth - popoutContainer.offsetWidth;
        const maxY = window.innerHeight - popoutContainer.offsetHeight;
        
        const boundedX = Math.max(0, Math.min(x, maxX));
        const boundedY = Math.max(0, Math.min(y, maxY));
        
        popoutContainer.style.left = boundedX + 'px';
        popoutContainer.style.top = boundedY + 'px';
        popoutContainer.style.right = 'auto';
        popoutContainer.style.bottom = 'auto';
    }

    function stopDrag() {
        isDragging = false;
        popoutContainer.style.cursor = 'default';
    }

    // Show/hide popout timer
    function showPopoutTimer() {
        if (popoutContainer) {
            popoutContainer.style.display = 'block';
            localStorage.setItem('popoutTimerVisible', 'true');
        }
    }

    function hidePopoutTimer() {
        if (popoutContainer) {
            popoutContainer.style.display = 'none';
            localStorage.setItem('popoutTimerVisible', 'false');
        }
    }

    // Minimize/maximize
    function minimizePopout() {
        if (popoutContent && popoutMinimized) {
            popoutContent.style.display = 'none';
            popoutMinimized.style.display = 'block';
            popoutContainer.classList.add('minimized');
            localStorage.setItem('popoutTimerMinimized', 'true');
        }
    }

    function maximizePopout() {
        if (popoutContent && popoutMinimized) {
            popoutContent.style.display = 'block';
            popoutMinimized.style.display = 'none';
            popoutContainer.classList.remove('minimized');
            localStorage.setItem('popoutTimerMinimized', 'false');
        }
    }

    // Sync with main timer state
    function syncWithMainTimer() {
        loadSettings();
        if (loadTimerState()) {
            updateDisplay();
            
            // Restart timer if it was running
            if (isRunning && !isPaused && timeLeft > 0) {
                startTimer();
            }
        } else {
            resetTimer();
        }
    }

    // Event listeners
    function setupEventListeners() {
        if (startBtn) startBtn.addEventListener('click', startTimer);
        if (pauseBtn) pauseBtn.addEventListener('click', pauseTimer);
        if (resetBtn) resetBtn.addEventListener('click', resetTimer);
        if (gamesBtn) gamesBtn.addEventListener('click', () => {
            if (!gamesBtn.classList.contains('disabled')) {
                window.location.href = '/pomodoro/games';
            }
        });
        if (expandBtn) expandBtn.addEventListener('click', () => {
            window.location.href = '/pomodoro';
        });
        if (minimizeBtn) minimizeBtn.addEventListener('click', minimizePopout);
        if (closeBtn) closeBtn.addEventListener('click', hidePopoutTimer);
        
        // Click to maximize when minimized
        if (popoutMinimized) {
            popoutMinimized.addEventListener('click', maximizePopout);
        }
        
        // Listen for storage changes (sync between tabs)
        window.addEventListener('storage', (e) => {
            if (e.key === 'pomodoroTimerState' || e.key === 'pomodoroSettings') {
                syncWithMainTimer();
            }
        });
    }

    // Initialize popout timer
    function initializePopoutTimer() {
        loadSettings();
        syncWithMainTimer();
        setupEventListeners();
        initializeDragging();
        
        // Check if timer should be visible
        const isVisible = localStorage.getItem('popoutTimerVisible') !== 'false';
        const isMinimized = localStorage.getItem('popoutTimerMinimized') === 'true';
        
        if (timeLeft > 0 && isVisible) {
            showPopoutTimer();
            if (isMinimized) {
                minimizePopout();
            }
        }
        
        // Update every second
        setInterval(() => {
            if (!isRunning || isPaused) {
                // Still update display in case of external changes
                syncWithMainTimer();
            }
        }, 1000);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializePopoutTimer);
    } else {
        initializePopoutTimer();
    }

})();