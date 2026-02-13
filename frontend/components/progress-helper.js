/**
 * Progress Overlay Helper Functions
 * Zentrale Helper für Progress-Anzeige mit gecachten DOM-Referenzen
 *
 * Zwei Modi:
 * - Simple:         showProgress('Text', 50)   → setzt festen Prozentwert
 * - Auto-Increment: showProgress('Text')       → inkrementiert automatisch bis 90%
 *
 * Usage (Auto-Increment, für temu.js / pdf.js):
 *   showProgress('Starte Sync...');
 *   updateProgress(100, 'Fertig!');
 *   hideProgress();
 *
 * Usage (Simple, für csv.script.js):
 *   showProgress('Lade Datei...', 0);
 *   updateProgress(50);
 *   updateProgressText('Fast fertig...');
 *   hideProgress();
 */

const ProgressOverlay = (() => {
    // Cached DOM references (lazy-initialized)
    let _overlay = null;
    let _text = null;
    let _fill = null;
    let _percent = null;

    // Auto-increment state
    let _interval = null;
    let _currentProgress = 0;

    function getElements() {
        if (!_overlay) {
            _overlay = document.getElementById('progress-overlay');
            _text = document.getElementById('progress-text');
            _fill = document.getElementById('progress-fill');
            _percent = document.getElementById('progress-percent');
        }
        return { overlay: _overlay, text: _text, fill: _fill, percent: _percent };
    }

    /** Reset cached refs (e.g. after DOM changes) */
    function resetCache() {
        _overlay = _text = _fill = _percent = null;
    }

    /** Stop auto-increment interval */
    function stopAutoIncrement() {
        if (_interval) {
            clearInterval(_interval);
            _interval = null;
        }
    }

    /** Start auto-increment: ticks progress randomly up to 90% */
    function startAutoIncrement() {
        stopAutoIncrement();
        _interval = setInterval(() => {
            if (_currentProgress < 90) {
                _currentProgress += Math.random() * 10;
                if (_currentProgress > 90) _currentProgress = 90;
                const { fill, percent } = getElements();
                if (fill) fill.style.width = _currentProgress + '%';
                if (percent) percent.textContent = Math.round(_currentProgress) + '%';
            }
        }, 200);
    }

    function setProgress(value) { _currentProgress = value; }
    function getProgress() { return _currentProgress; }

    return { getElements, resetCache, startAutoIncrement, stopAutoIncrement, setProgress, getProgress };
})();

/**
 * Show progress overlay
 * @param {string} text - Display text
 * @param {number} [percentOrUndefined] - If number: set fixed percent (simple mode).
 *                                         If omitted: start auto-increment to 90%.
 */
function showProgress(text = 'Verarbeite...', percentOrUndefined) {
    const { overlay, text: textEl, fill, percent: percentEl } = ProgressOverlay.getElements();

    if (!overlay) {
        console.error('Progress overlay not found');
        return;
    }

    const useAutoIncrement = typeof percentOrUndefined !== 'number';
    const initialPercent = useAutoIncrement ? 0 : percentOrUndefined;

    ProgressOverlay.setProgress(initialPercent);
    if (textEl) textEl.textContent = text;
    if (fill) fill.style.width = initialPercent + '%';
    if (percentEl) percentEl.textContent = initialPercent + '%';
    overlay.classList.add('active');

    if (useAutoIncrement) {
        ProgressOverlay.startAutoIncrement();
    }
}

/**
 * Update progress percent and optionally text
 * @param {number} percent - Progress value (0-100)
 * @param {string} [text] - Optional new display text
 */
function updateProgress(percent, text) {
    const { fill, percent: percentEl, text: textEl } = ProgressOverlay.getElements();

    ProgressOverlay.setProgress(percent);
    if (fill) fill.style.width = percent + '%';
    if (percentEl) percentEl.textContent = Math.round(percent) + '%';
    if (text && textEl) textEl.textContent = text;
}

/**
 * Update only the progress text
 * @param {string} text - New display text
 */
function updateProgressText(text) {
    const { text: textEl } = ProgressOverlay.getElements();
    if (textEl) textEl.textContent = text;
}

/**
 * Hide progress overlay and stop any auto-increment
 */
function hideProgress() {
    ProgressOverlay.stopAutoIncrement();
    const { overlay } = ProgressOverlay.getElements();
    if (overlay) overlay.classList.remove('active');
    ProgressOverlay.setProgress(0);
}

// ═══ Step-based Simulation (für csv.script.js) ═══

const DEFAULT_PROGRESS_STEPS = [
    { text: 'Starte...', percent: 0, delay: 100 },
    { text: 'Lade Datei...', percent: 25, delay: 500 },
    { text: 'Verarbeite...', percent: 50, delay: 1000 },
    { text: 'Fast fertig...', percent: 75, delay: 800 },
    { text: 'Fertig!', percent: 100, delay: 300 }
];

/**
 * Simulate progress with configurable steps
 * @param {Array<{text: string, percent: number, delay: number}>} steps
 * @returns {Promise<void>}
 */
function simulateProgress(steps = DEFAULT_PROGRESS_STEPS) {
    return new Promise((resolve) => {
        let index = 0;

        function nextStep() {
            if (index >= steps.length) {
                setTimeout(() => {
                    hideProgress();
                    resolve();
                }, 500);
                return;
            }

            const step = steps[index];
            updateProgressText(step.text);
            updateProgress(step.percent);

            index++;
            setTimeout(nextStep, step.delay);
        }

        showProgress(steps[0].text, steps[0].percent);
        setTimeout(nextStep, steps[0].delay);
    });
}
