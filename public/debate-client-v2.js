/**
 * AI Debate Arena v2 - Multi-Debater Client
 * "Me fail debate? That's unpossible!" - Ralph Wiggum
 */

class DebateArenaV2 {
    constructor() {
        this.ws = null;
        this.debateId = null;
        this.debaters = [];
        this.debaterIndexMap = {};
        this.selectedTemplate = null;
        this.isRunning = false;
        this.customDebaters = [];

        // Browser TTS support
        this.ttsEnabled = 'speechSynthesis' in window;
        this.ttsQueue = [];
        this.isSpeaking = false;
        this.voices = [];
        this.voiceMap = {}; // Map debater IDs to voices

        this.initElements();
        this.initEventListeners();
        this.loadTemplates();
        this.connectWebSocket();
        this.initCustomDebaters();
        this.initTTS();
    }

    initTTS() {
        if (!this.ttsEnabled) {
            console.log('Browser TTS not available');
            return;
        }

        // Load voices when available
        const loadVoices = () => {
            this.voices = speechSynthesis.getVoices();
            console.log(`Loaded ${this.voices.length} TTS voices`);
        };

        loadVoices();
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = loadVoices;
        }
    }

    getVoiceForDebater(debaterId, index) {
        if (!this.ttsEnabled || this.voices.length === 0) return null;

        // Cache voice assignment
        if (this.voiceMap[debaterId]) {
            return this.voiceMap[debaterId];
        }

        // Try to get varied voices - prefer English voices
        const englishVoices = this.voices.filter(v => v.lang.startsWith('en'));
        const voicePool = englishVoices.length > 0 ? englishVoices : this.voices;

        // Assign different voice based on index
        const voice = voicePool[index % voicePool.length];
        this.voiceMap[debaterId] = voice;
        return voice;
    }

    speakText(text, debaterId = null, index = 0) {
        if (!this.ttsEnabled || !this.isRunning) return;

        // Get volume from slider
        const volume = (this.volumeSlider?.value || 80) / 100;
        if (volume === 0) return;

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.volume = volume;
        utterance.rate = 1.0;
        utterance.pitch = 1.0;

        // Assign voice if we have voices
        if (this.voices.length > 0) {
            const voice = this.getVoiceForDebater(debaterId, index);
            if (voice) {
                utterance.voice = voice;
                // Vary pitch slightly based on index for more variety
                utterance.pitch = 0.9 + (index % 3) * 0.15;
            }
        }

        // Queue management
        this.ttsQueue.push(utterance);
        this.processQueue();
    }

    processQueue() {
        if (this.isSpeaking || this.ttsQueue.length === 0) return;

        this.isSpeaking = true;
        const utterance = this.ttsQueue.shift();

        utterance.onend = () => {
            this.isSpeaking = false;
            this.processQueue();
        };

        utterance.onerror = () => {
            this.isSpeaking = false;
            this.processQueue();
        };

        speechSynthesis.speak(utterance);
    }

    stopTTS() {
        if (this.ttsEnabled) {
            speechSynthesis.cancel();
            this.ttsQueue = [];
            this.isSpeaking = false;
        }
    }

    initElements() {
        // Connection status
        this.connectionStatus = document.getElementById('connection-status');

        // Tabs
        this.tabBtns = document.querySelectorAll('.tab-btn');
        this.templatesTab = document.getElementById('templates-tab');
        this.customTab = document.getElementById('custom-tab');

        // Template elements
        this.templateGrid = document.getElementById('template-grid');
        this.templateRounds = document.getElementById('template-rounds');
        this.createFromTemplateBtn = document.getElementById('create-from-template');
        this.startDebateBtn = document.getElementById('start-debate');

        // Custom debate elements
        this.debateTopic = document.getElementById('debate-topic');
        this.maxRounds = document.getElementById('max-rounds');
        this.moderatorStrictness = document.getElementById('moderator-strictness');
        this.debaterCards = document.getElementById('debater-cards');
        this.debaterCount = document.getElementById('debater-count');
        this.addDebaterBtn = document.getElementById('add-debater');
        this.createCustomBtn = document.getElementById('create-custom');
        this.startCustomDebateBtn = document.getElementById('start-custom-debate');

        // Arena elements
        this.debateSetup = document.getElementById('debate-setup');
        this.debateArena = document.getElementById('debate-arena');
        this.debateTopicDisplay = document.getElementById('debate-topic-display');
        this.debateStatusDisplay = document.getElementById('debate-status-display');
        this.roundInfo = document.getElementById('round-info');
        this.debatersArena = document.getElementById('debaters-arena');
        this.transcript = document.getElementById('transcript');

        // Controls
        this.volumeSlider = document.getElementById('volume-slider');
        this.volumeValue = document.getElementById('volume-value');
        this.stopDebateBtn = document.getElementById('stop-debate');
        this.startDebateArenaBtn = document.getElementById('start-debate-arena');
    }

    initEventListeners() {
        // Tab switching
        this.tabBtns.forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });

        // Template creation
        this.createFromTemplateBtn.addEventListener('click', () => this.createFromTemplate());
        this.startDebateBtn.addEventListener('click', () => this.startDebate());

        // Custom creation
        this.addDebaterBtn.addEventListener('click', () => this.addDebater());
        this.createCustomBtn.addEventListener('click', () => this.createCustomDebate());
        this.startCustomDebateBtn.addEventListener('click', () => this.startDebate());

        // Controls
        this.volumeSlider.addEventListener('input', (e) => {
            this.volumeValue.textContent = `${e.target.value}%`;
        });

        this.stopDebateBtn.addEventListener('click', () => this.stopDebate());
        this.startDebateArenaBtn.addEventListener('click', () => this.startDebate());
    }

    switchTab(tabName) {
        this.tabBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });
        this.templatesTab.classList.toggle('active', tabName === 'templates');
        this.customTab.classList.toggle('active', tabName === 'custom');
    }

    async loadTemplates() {
        try {
            const response = await fetch('/api/templates');
            const data = await response.json();

            this.templateGrid.innerHTML = data.templates.map(template => `
                <div class="template-card" data-template="${template.name}">
                    <div class="template-title">${this.formatTemplateName(template.name)}</div>
                    <div class="template-topic">${template.topic}</div>
                    <div class="template-debaters">
                        ${template.debaters.map(d => `
                            <span class="debater-tag">${d.name} (${d.position})</span>
                        `).join('')}
                    </div>
                </div>
            `).join('');

            // Add click handlers
            this.templateGrid.querySelectorAll('.template-card').forEach(card => {
                card.addEventListener('click', () => this.selectTemplate(card.dataset.template));
            });

            // Select first template by default
            if (data.templates.length > 0) {
                this.selectTemplate(data.templates[0].name);
            }
        } catch (error) {
            console.error('Failed to load templates:', error);
            this.templateGrid.innerHTML = '<p>Failed to load templates. Is the server running?</p>';
        }
    }

    formatTemplateName(name) {
        return name.split('_').map(word =>
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }

    selectTemplate(templateName) {
        this.selectedTemplate = templateName;
        this.templateGrid.querySelectorAll('.template-card').forEach(card => {
            card.classList.toggle('selected', card.dataset.template === templateName);
        });
    }

    initCustomDebaters() {
        // Start with 2 debaters
        this.customDebaters = [
            { name: 'Position 1', stance: '', debater_name: 'Speaker 1', avatar: '' },
            { name: 'Position 2', stance: '', debater_name: 'Speaker 2', avatar: '' }
        ];
        this.renderDebaterCards();
    }

    renderDebaterCards() {
        const avatars = ['', '', '', '', '', ''];
        this.debaterCards.innerHTML = this.customDebaters.map((debater, index) => `
            <div class="debater-card" data-index="${index}">
                <div class="debater-card-header">
                    <span class="debater-number">Debater ${index + 1}</span>
                    ${index >= 2 ? `<button class="remove-debater" data-index="${index}">x</button>` : ''}
                </div>
                <input type="text" placeholder="Position name (e.g., Atheist)"
                       value="${debater.name}" data-field="name" data-index="${index}">
                <input type="text" placeholder="Debater name (e.g., Dr. Smith)"
                       value="${debater.debater_name}" data-field="debater_name" data-index="${index}">
                <textarea placeholder="Stance on the topic..."
                          data-field="stance" data-index="${index}">${debater.stance}</textarea>
            </div>
        `).join('');

        // Update count
        this.debaterCount.textContent = this.customDebaters.length;
        this.addDebaterBtn.disabled = this.customDebaters.length >= 6;

        // Add event listeners
        this.debaterCards.querySelectorAll('input, textarea').forEach(input => {
            input.addEventListener('input', (e) => {
                const index = parseInt(e.target.dataset.index);
                const field = e.target.dataset.field;
                this.customDebaters[index][field] = e.target.value;
            });
        });

        this.debaterCards.querySelectorAll('.remove-debater').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(e.target.dataset.index);
                this.removeDebater(index);
            });
        });
    }

    addDebater() {
        if (this.customDebaters.length >= 6) return;
        const index = this.customDebaters.length + 1;
        this.customDebaters.push({
            name: `Position ${index}`,
            stance: '',
            debater_name: `Speaker ${index}`,
            avatar: ''
        });
        this.renderDebaterCards();
    }

    removeDebater(index) {
        if (this.customDebaters.length <= 2) return;
        this.customDebaters.splice(index, 1);
        this.renderDebaterCards();
    }

    connectWebSocket() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            this.setConnectionStatus('connected', 'Connected');
            if (this.debateId) {
                this.joinDebate(this.debateId);
            }
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.ws.onclose = () => {
            this.setConnectionStatus('disconnected', 'Disconnected');
            setTimeout(() => this.connectWebSocket(), 3000);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.setConnectionStatus('disconnected', 'Error');
        };
    }

    setConnectionStatus(className, text) {
        this.connectionStatus.className = `connection-status ${className}`;
        this.connectionStatus.textContent = text;
    }

    joinDebate(debateId) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'join',
                debate_id: debateId
            }));
        }
    }

    handleWebSocketMessage(data) {
        switch (data.event) {
            case 'debate_started':
                this.onDebateStarted(data);
                break;
            case 'phase_change':
                this.onPhaseChange(data);
                break;
            case 'speaker_change':
                this.onTurnStart(data);
                break;
            case 'turn_completed':
                this.onTurnComplete(data);
                break;
            case 'moderator_action':
                this.onModeration(data);
                break;
            case 'round_start':
                this.onRoundStart(data);
                break;
            case 'debate_ended':
                this.onDebateComplete(data);
                break;
            case 'debate_stopped':
                this.onDebateStopped();
                break;
            case 'off_topic':
                this.onOffTopic(data);
                break;
            case 'joined':
                console.log('Joined debate:', data.debate_id);
                break;
        }
    }

    async createFromTemplate() {
        if (!this.selectedTemplate) {
            alert('Please select a template first');
            return;
        }

        try {
            this.setConnectionStatus('loading', 'Creating...');

            const response = await fetch('/api/debate/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    template: this.selectedTemplate,
                    max_rounds: parseInt(this.templateRounds.value)
                })
            });

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            this.debateId = data.debate_id;
            this.debaters = data.debaters;
            this.buildDebaterIndexMap();

            this.showArena(data);
            this.joinDebate(this.debateId);

            this.startDebateBtn.disabled = false;
            this.setConnectionStatus('connected', 'Ready');

        } catch (error) {
            console.error('Failed to create debate:', error);
            alert(`Failed to create debate: ${error.message}`);
            this.setConnectionStatus('connected', 'Connected');
        }
    }

    async createCustomDebate() {
        const topic = this.debateTopic.value.trim();
        if (!topic) {
            alert('Please enter a debate topic');
            return;
        }

        if (this.customDebaters.length < 2) {
            alert('You need at least 2 debaters');
            return;
        }

        // Validate debaters have names and positions
        for (let i = 0; i < this.customDebaters.length; i++) {
            if (!this.customDebaters[i].name.trim()) {
                alert(`Debater ${i + 1} needs a position name`);
                return;
            }
        }

        try {
            this.setConnectionStatus('loading', 'Creating...');

            const response = await fetch('/api/debate/create-custom', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic: topic,
                    positions: this.customDebaters.map(d => ({
                        name: d.name,
                        stance: d.stance || `Argues the ${d.name} position`,
                        debater_name: d.debater_name || undefined
                    })),
                    max_rounds: parseInt(this.maxRounds.value),
                    moderator_strictness: this.moderatorStrictness.value
                })
            });

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            this.debateId = data.debate_id;
            this.debaters = data.debaters;
            this.buildDebaterIndexMap();

            this.showArena(data);
            this.joinDebate(this.debateId);

            this.startCustomDebateBtn.disabled = false;
            this.setConnectionStatus('connected', 'Ready');

        } catch (error) {
            console.error('Failed to create custom debate:', error);
            alert(`Failed to create debate: ${error.message}`);
            this.setConnectionStatus('connected', 'Connected');
        }
    }

    buildDebaterIndexMap() {
        this.debaterIndexMap = {};
        this.debaters.forEach((d, index) => {
            this.debaterIndexMap[d.id] = index;
        });
    }

    showArena(data) {
        this.debateSetup.style.display = 'none';
        this.debateArena.style.display = 'block';

        this.debateTopicDisplay.textContent = data.topic;
        this.debateStatusDisplay.textContent = 'Ready to start';
        this.roundInfo.textContent = `0 / ${data.max_rounds} rounds`;

        // Render debater panels
        this.renderDebaterPanels();

        // Clear transcript
        this.transcript.innerHTML = '';
    }

    renderDebaterPanels() {
        const count = this.debaters.length;
        this.debatersArena.className = `debaters-arena count-${count}`;

        this.debatersArena.innerHTML = this.debaters.map((debater, index) => `
            <div class="debater-panel" data-debater-id="${debater.id}" data-index="${index}">
                <div class="debater-header">
                    <div class="debater-avatar">${debater.avatar || this.getDefaultAvatar(index)}</div>
                    <div class="debater-info">
                        <div class="debater-name">${debater.name}</div>
                        <div class="debater-position">${debater.position}</div>
                    </div>
                </div>
                ${debater.stance ? `<div class="debater-stance">${debater.stance}</div>` : ''}
                <div class="debater-status" id="status-${debater.id}">Waiting...</div>
            </div>
        `).join('');
    }

    getDefaultAvatar(index) {
        const avatars = ['', '', '', '', '', ''];
        return avatars[index % avatars.length];
    }

    async startDebate() {
        if (!this.debateId) return;

        try {
            this.setConnectionStatus('loading', 'Starting...');

            const response = await fetch(`/api/debate/${this.debateId}/start`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            this.isRunning = true;
            this.startDebateBtn.disabled = true;
            this.startCustomDebateBtn.disabled = true;
            this.startDebateArenaBtn.disabled = true;
            this.stopDebateBtn.disabled = false;

            this.setConnectionStatus('connected', 'Debating');

        } catch (error) {
            console.error('Failed to start debate:', error);
            alert(`Failed to start debate: ${error.message}`);
            this.setConnectionStatus('connected', 'Ready');
        }
    }

    async stopDebate() {
        if (!this.debateId) return;

        // Stop any ongoing TTS
        this.stopTTS();

        try {
            await fetch(`/api/debate/${this.debateId}`, {
                method: 'DELETE'
            });

            this.isRunning = false;
            this.stopDebateBtn.disabled = true;
            this.debateStatusDisplay.textContent = 'Stopped';

        } catch (error) {
            console.error('Failed to stop debate:', error);
        }
    }

    // WebSocket Event Handlers
    onDebateStarted(data) {
        this.debateStatusDisplay.textContent = 'Debate in progress';
        this.isRunning = true;
    }

    onPhaseChange(data) {
        this.debateStatusDisplay.textContent = `Phase: ${this.formatPhase(data.phase)}`;
        if (data.round) {
            this.roundInfo.textContent = `Round ${data.round} / ${data.total_rounds || '?'}`;
        }
    }

    formatPhase(phase) {
        const phases = {
            'introduction': 'Introduction',
            'opening': 'Opening Statements',
            'debate': 'Main Debate',
            'rebuttals': 'Rebuttals',
            'closing': 'Closing Statements',
            'conclusion': 'Conclusion',
            'finished': 'Finished'
        };
        return phases[phase] || phase;
    }

    onTurnStart(data) {
        // Highlight speaking debater
        this.debatersArena.querySelectorAll('.debater-panel').forEach(panel => {
            panel.classList.remove('speaking');
            const statusEl = panel.querySelector('.debater-status');
            if (statusEl) statusEl.className = 'debater-status';
        });

        const speakingPanel = this.debatersArena.querySelector(`[data-debater-id="${data.debater_id}"]`);
        if (speakingPanel) {
            speakingPanel.classList.add('speaking');
            const statusEl = speakingPanel.querySelector('.debater-status');
            if (statusEl) {
                statusEl.className = 'debater-status speaking';
                statusEl.textContent = 'Speaking...';
            }
        }
    }

    onTurnComplete(data) {
        const turn = data.turn || data;
        // Remove speaking highlight
        const speakingPanel = this.debatersArena.querySelector(`[data-debater-id="${turn.debater_id}"]`);
        if (speakingPanel) {
            speakingPanel.classList.remove('speaking');
            const statusEl = speakingPanel.querySelector('.debater-status');
            if (statusEl) {
                statusEl.className = 'debater-status';
                statusEl.textContent = 'Waiting...';
            }
        }

        // Add to transcript
        this.addTranscriptEntry(turn);
    }

    onRoundStart(data) {
        this.roundInfo.textContent = `Round ${data.round} / ${data.total_rounds}`;
    }

    addTranscriptEntry(data) {
        const index = this.debaterIndexMap[data.debater_id] || 0;
        const entry = document.createElement('div');
        entry.className = 'turn-entry';
        entry.dataset.debaterIndex = index;

        // Handle both old format (data.argument) and new format (data.statement)
        const statement = data.statement || data.argument?.main_claim || data.text || '';
        const supportingPoints = data.supporting_points || data.argument?.supporting_points || [];

        let supportingPointsHtml = '';
        if (supportingPoints.length > 0) {
            supportingPointsHtml = `
                <ul class="turn-supporting-points">
                    ${supportingPoints.map(p => `<li>${p}</li>`).join('')}
                </ul>
            `;
        }

        entry.innerHTML = `
            <div class="turn-header">
                <div>
                    <span class="turn-speaker">${data.debater_name}</span>
                    <span class="turn-position">(${data.position_name})</span>
                </div>
                <span class="turn-phase">${this.formatPhase(data.phase || 'debate')}</span>
            </div>
            <div class="turn-content">${statement}</div>
            ${supportingPointsHtml}
        `;

        this.transcript.appendChild(entry);
        this.transcript.scrollTop = this.transcript.scrollHeight;

        // Speak the text using browser TTS
        const fullText = supportingPoints.length > 0
            ? `${statement}. ${supportingPoints.join('. ')}`
            : statement;
        this.speakText(fullText, data.debater_id, index);
    }

    onModeration(data) {
        const entry = document.createElement('div');
        entry.className = 'turn-entry turn-moderator';
        entry.innerHTML = `
            <div class="turn-header">
                <span class="turn-speaker">Moderator</span>
                <span class="turn-phase">${data.action_type || 'moderation'}</span>
            </div>
            <div class="turn-content">${data.message}</div>
        `;

        // Speak moderator text
        this.speakText(data.message, 'moderator', 99);

        this.transcript.appendChild(entry);
        this.transcript.scrollTop = this.transcript.scrollHeight;
    }

    onOffTopic(data) {
        // Show off-topic warning
        const entry = document.createElement('div');
        entry.className = 'turn-entry turn-moderator';
        entry.innerHTML = `
            <div class="turn-header">
                <span class="turn-speaker">Moderator</span>
                <span class="turn-phase">Off-Topic Warning</span>
            </div>
            <div class="turn-content">
                <strong>${data.debater_name}</strong> went off-topic.
                ${data.redirect ? `Suggested redirect: ${data.redirect}` : ''}
            </div>
        `;

        this.transcript.appendChild(entry);
        this.transcript.scrollTop = this.transcript.scrollHeight;
    }

    onRoundComplete(data) {
        this.roundInfo.textContent = `Round ${data.round} / ${data.total_rounds} completed`;
    }

    onDebateComplete(data) {
        this.isRunning = false;
        this.stopDebateBtn.disabled = true;
        this.debateStatusDisplay.textContent = 'Debate Complete';

        // Let TTS finish naturally (don't cut off mid-sentence)

        // Reset all panels
        this.debatersArena.querySelectorAll('.debater-panel').forEach(panel => {
            panel.classList.remove('speaking');
            const statusEl = panel.querySelector('.debater-status');
            if (statusEl) {
                statusEl.className = 'debater-status';
                statusEl.textContent = 'Finished';
            }
        });

        // Add conclusion to transcript if present
        if (data.conclusion) {
            const entry = document.createElement('div');
            entry.className = 'turn-entry turn-moderator';
            entry.innerHTML = `
                <div class="turn-header">
                    <span class="turn-speaker">Moderator</span>
                    <span class="turn-phase">Conclusion</span>
                </div>
                <div class="turn-content">${data.conclusion}</div>
            `;
            this.transcript.appendChild(entry);
        }
    }

    onDebateStopped() {
        this.isRunning = false;
        this.stopDebateBtn.disabled = true;
        this.debateStatusDisplay.textContent = 'Stopped';
        this.stopTTS();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.debateArena = new DebateArenaV2();
});
