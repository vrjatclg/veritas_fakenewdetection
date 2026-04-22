document.addEventListener('DOMContentLoaded', () => {
    const analyseBtn = document.getElementById('analyse-btn');
    const claimInput = document.getElementById('claim-input');
    const inputSection = document.getElementById('input-section');
    const loadingSection = document.getElementById('loading-section');
    const resultsSection = document.getElementById('results-section');
    const newAnalysisBtn = document.getElementById('new-analysis-btn');
    const modeToggleInput = document.getElementById('mode-toggle-input');
    const modeDisplay = document.getElementById('mode-display');

    // Result elements
    const verdictText = document.getElementById('verdict-text');
    const verdictBox = document.getElementById('verdict-display');
    const explainabilityText = document.getElementById('explainability-text');
    const intelligenceFeed = document.getElementById('intelligence-feed');
    const metaSources = document.getElementById('meta-sources');
    const metaEngine = document.getElementById('meta-engine');

    // Load initial config
    loadConfig();

    // Toggle mode handler
    modeToggleInput.addEventListener('change', async () => {
        const useLocal = modeToggleInput.checked;
        modeDisplay.textContent = useLocal ? 'LOCAL' : 'API';
        try {
            const response = await fetch(`/config/toggle?use_local=${useLocal}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            if (data.status === 'success') {
                console.log(`Switched to ${useLocal ? 'Local Model' : 'API'}`);
            }
        } catch (error) {
            console.error('Failed to toggle mode:', error);
            modeToggleInput.checked = !useLocal; // Revert on error
            modeDisplay.textContent = useLocal ? 'API' : 'LOCAL';
        }
    });

    async function loadConfig() {
        try {
            const response = await fetch('/config');
            const config = await response.json();
            modeToggleInput.checked = config.use_local_model;
            modeDisplay.textContent = config.use_local_model ? 'LOCAL' : 'API';
        } catch (error) {
            console.error('Failed to load config:', error);
        }
    }

    analyseBtn.addEventListener('click', async () => {
        const claim = claimInput.value.trim();
        if (!claim) {
            alert('Please enter a claim to analyze.');
            return;
        }

        // Switch to loading state
        inputSection.classList.add('hidden');
        loadingSection.classList.remove('hidden');

        try {
            const useLocal = modeToggleInput.checked;
            console.log(`[JS] Toggle checked: ${modeToggleInput.checked} | useLocal: ${useLocal}`);
            
            const payload = { claim, use_local: useLocal };
            console.log(`[JS] Sending payload:`, JSON.stringify(payload));
            
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error('Analysis failed');

            const data = await response.json();
            console.log(`[JS] Received result - Engine: ${data.engine} | Verdict: ${data.verdict}`);
            displayResults(data);
        } catch (error) {
            console.error(error);
            alert('An error occurred during analysis.');
            loadingSection.classList.add('hidden');
            inputSection.classList.remove('hidden');
        }
    });

    newAnalysisBtn.addEventListener('click', () => {
        resultsSection.classList.add('hidden');
        inputSection.classList.remove('hidden');
        claimInput.value = '';
    });

    function displayResults(data) {
        // Update Verdict
        verdictText.textContent = data.verdict;
        verdictBox.className = 'verdict-box'; // reset
        
        const verdictLower = data.verdict.toLowerCase();
        if (verdictLower.includes('fake')) verdictBox.classList.add('fake');
        else if (verdictLower.includes('real')) verdictBox.classList.add('real');
        else verdictBox.classList.add('unverified');

        explainabilityText.textContent = data.explainability;
        metaSources.textContent = data.sources.length;
        metaEngine.textContent = data.engine;

        // Populate Feed
        intelligenceFeed.innerHTML = '';
        data.sources.forEach(source => {
            const node = document.createElement('div');
            node.className = 'node-card';
            
            const statusClass = `status-${source.status.toLowerCase()}`;
            
            node.innerHTML = `
                <div class="node-header">
                    <span class="node-source">${source.source}</span>
                    <span class="node-status ${statusClass}">${source.status}</span>
                </div>
                <p class="node-explanation">${source.explanation}</p>
                <div class="confidence-section">
                    <span>Confidence ${source.confidence}%</span>
                    <div class="progress-container">
                        <div class="progress-bar" style="width: 0%"></div>
                    </div>
                </div>
            `;
            intelligenceFeed.appendChild(node);
            
            // Animate progress bar
            setTimeout(() => {
                const bar = node.querySelector('.progress-bar');
                bar.style.width = `${source.confidence}%`;
            }, 100);
        });

        // Show results
        loadingSection.classList.add('hidden');
        resultsSection.classList.remove('hidden');
    }
});
