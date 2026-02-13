/**
 * Progress Overlay Helper Functions
 * Zentrale Helper für Progress-Anzeige
 * 
 * Usage:
 * showProgress('Verarbeite Daten...', 0);
 * updateProgress(50);
 * updateProgressText('Fast fertig...');
 * hideProgress();
 */

function showProgress(text = 'Verarbeite...', percent = 0) {
    const overlay = document.getElementById('progress-overlay');
    const progressText = document.getElementById('progress-text');
    const progressFill = document.getElementById('progress-fill');
    const progressPercent = document.getElementById('progress-percent');

    if (!overlay) {
        console.error('Progress overlay not found');
        return;
    }

    if (progressText) progressText.textContent = text;
    if (progressFill) progressFill.style.width = percent + '%';
    if (progressPercent) progressPercent.textContent = percent + '%';
    
    overlay.classList.add('active');
}

function updateProgress(percent) {
    const progressFill = document.getElementById('progress-fill');
    const progressPercent = document.getElementById('progress-percent');

    if (progressFill) progressFill.style.width = percent + '%';
    if (progressPercent) progressPercent.textContent = percent + '%';
}

function updateProgressText(text) {
    const progressText = document.getElementById('progress-text');
    if (progressText) progressText.textContent = text;
}

function hideProgress() {
    const overlay = document.getElementById('progress-overlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

// Simulate progress with steps
function simulateProgress(steps = [
    { text: 'Starte...', percent: 0, delay: 100 },
    { text: 'Lade Datei...', percent: 25, delay: 500 },
    { text: 'Verarbeite...', percent: 50, delay: 1000 },
    { text: 'Fast fertig...', percent: 75, delay: 800 },
    { text: 'Fertig!', percent: 100, delay: 300 }
]) {
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
