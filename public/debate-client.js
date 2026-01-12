class DebateClient {
    constructor() {
        this.websocket = null;
        this.currentDebateId = null;
        this.audioContext = null;
        this.volume = 0.8;
        this.isConnected = false;

        // Ralph Wiggum loading messages - "I'm learnding!"
        this.ralphQuotes = [
            "I'm learnding!",
            "Me fail debate? That's unpossible!",
            "My cat's breath smells like cat food.",
            "I bent my Wookie.",
            "Hi, Super Nintendo Chalmers!",
            "I choo-choo-choose you!",
            "It tastes like burning!",
            "Sleep! That's where I'm a Viking!",
            "Go banana!",
            "When I grow up I want to be a principal or a caterpillar!",
            "I'm Idaho!",
            "The leprechaun tells me to burn things!",
            "Even my boogers are delicious!",
            "I found a moon rock in my nose!",
            "Slow down! My legs don't know how to be as long as yours!",
        ];

        this.initializeElements();
        this.setupEventListeners();
        this.connect();
    }

    getRandomRalphQuote() {
        return this.ralphQuotes[Math.floor(Math.random() * this.ralphQuotes.length)];
    }
    
    initializeElements() {
        // Setup elements
        this.elements = {
            debateSetup: document.getElementById('debate-setup'),
            debateArena: document.getElementById('debate-arena'),
            debateTopic: document.getElementById('debate-topic'),
            maxRounds: document.getElementById('max-rounds'),
            createDebateBtn: document.getElementById('create-debate'),
            startDebateBtn: document.getElementById('start-debate'),
            stopDebateBtn: document.getElementById('stop-debate'),
            debateTopicDisplay: document.getElementById('debate-topic-display'),
            debateStatusDisplay: document.getElementById('debate-status-display'),
            agentProStatus: document.getElementById('agent-pro-status'),
            agentConStatus: document.getElementById('agent-con-status'),
            transcript: document.getElementById('transcript'),
            connectionStatus: document.getElementById('connection-status'),
            volumeSlider: document.getElementById('volume-slider'),
            volumeValue: document.getElementById('volume-value')
        };
    }
    
    setupEventListeners() {
        this.elements.createDebateBtn.addEventListener('click', () => this.createDebate());
        this.elements.startDebateBtn.addEventListener('click', () => this.startDebate());
        this.elements.stopDebateBtn.addEventListener('click', () => this.stopDebate());
        
        this.elements.volumeSlider.addEventListener('input', (e) => {
            this.volume = e.target.value / 100;
            this.elements.volumeValue.textContent = `${e.target.value}%`;
        });
        
        // Initialize audio context on user interaction
        document.addEventListener('click', () => {
            if (!this.audioContext) {
                this.initializeAudio();
            }
        }, { once: true });
    }
    
    async initializeAudio() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('Audio context initialized');
        } catch (error) {
            console.error('Failed to initialize audio context:', error);
        }
    }
    
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.updateConnectionStatus('connected');
        };
        
        this.websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Failed to parse message:', error);
            }
        };
        
        this.websocket.onclose = () => {
            console.log('WebSocket disconnected');
            this.isConnected = false;
            this.updateConnectionStatus('disconnected');
            
            // Reconnect after 3 seconds
            setTimeout(() => this.connect(), 3000);
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus('disconnected');
        };
    }
    
    updateConnectionStatus(status) {
        this.elements.connectionStatus.className = `connection-status ${status}`;
        this.elements.connectionStatus.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    }
    
    handleMessage(data) {
        switch (data.type) {
            case 'joined':
                console.log(`Joined debate: ${data.debate_id}`);
                break;
                
            case 'debate_event':
                this.handleDebateEvent(data);
                break;
                
            case 'audio_stream':
                this.playAudio(data.audio_data, data.metadata);
                break;
                
            case 'pong':
                // Keep-alive response
                break;
                
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    handleDebateEvent(data) {
        if (data.event === 'turn_completed') {
            this.addTranscriptEntry(data.turn);
            this.updateAgentStatus(data.turn);
        } else if (data.event === 'debate_ended') {
            this.handleDebateEnd(data);
        } else if (data.event === 'debate_error') {
            this.handleDebateError(data);
        }
    }
    
    addTranscriptEntry(turn) {
        const entry = document.createElement('div');
        entry.className = `turn-entry turn-${turn.role}`;
        
        const timestamp = new Date(turn.timestamp * 1000).toLocaleTimeString();
        
        entry.innerHTML = `
            <div class="turn-header">
                <span class="turn-agent">${turn.agent_name}</span>
                <span class="turn-time">${timestamp}</span>
            </div>
            <div class="turn-statement">${turn.statement}</div>
        `;
        
        this.elements.transcript.appendChild(entry);
        this.elements.transcript.scrollTop = this.elements.transcript.scrollHeight;
    }
    
    updateAgentStatus(turn) {
        // Reset all statuses to listening
        this.elements.agentProStatus.className = 'agent-status status-listening';
        this.elements.agentProStatus.textContent = 'Listening...';
        this.elements.agentConStatus.className = 'agent-status status-listening';
        this.elements.agentConStatus.textContent = 'Listening...';
        
        // Set current speaker
        if (turn.role === 'pro') {
            this.elements.agentProStatus.className = 'agent-status status-speaking';
            this.elements.agentProStatus.textContent = 'Speaking...';
        } else if (turn.role === 'con') {
            this.elements.agentConStatus.className = 'agent-status status-speaking';
            this.elements.agentConStatus.textContent = 'Speaking...';
        }
        
        // Update debate status
        const phaseText = turn.phase.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
        this.elements.debateStatusDisplay.textContent = `${phaseText} - ${turn.agent_name} speaking`;
    }
    
    async playAudio(audioDataBase64, metadata) {
        if (!this.audioContext) {
            console.log('Audio context not initialized');
            return;
        }
        
        try {
            // Decode base64 audio data
            const audioData = atob(audioDataBase64);
            const arrayBuffer = new ArrayBuffer(audioData.length);
            const uint8Array = new Uint8Array(arrayBuffer);
            
            for (let i = 0; i < audioData.length; i++) {
                uint8Array[i] = audioData.charCodeAt(i);
            }
            
            // Decode audio buffer
            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
            
            // Create and play audio source
            const source = this.audioContext.createBufferSource();
            const gainNode = this.audioContext.createGain();
            
            source.buffer = audioBuffer;
            gainNode.gain.value = this.volume;
            
            source.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            source.start();
            
            console.log(`Playing audio for ${metadata.agent_name}: "${metadata.statement}"`);
            
        } catch (error) {
            console.error('Failed to play audio:', error);
        }
    }
    
    handleDebateEnd(data) {
        this.elements.debateStatusDisplay.textContent = 'Debate Completed';
        this.elements.startDebateBtn.disabled = false;
        this.elements.stopDebateBtn.disabled = true;
        this.elements.agentProStatus.textContent = 'Debate finished';
        this.elements.agentConStatus.textContent = 'Debate finished';

        // Add completion message to transcript with Ralph Wiggum quote
        const ralphQuote = this.getRandomRalphQuote();
        const completionEntry = document.createElement('div');
        completionEntry.className = 'turn-entry turn-moderator';
        completionEntry.innerHTML = `
            <div class="turn-header">
                <span class="turn-agent">🎭 Debate Completed</span>
                <span class="turn-time">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="turn-statement">Thank you for watching this AI-powered debate! Total turns: ${data.total_turns}<br><em>"${ralphQuote}" - Ralph Wiggum</em></div>
        `;
        
        this.elements.transcript.appendChild(completionEntry);
        this.elements.transcript.scrollTop = this.elements.transcript.scrollHeight;
    }
    
    handleDebateError(data) {
        this.elements.debateStatusDisplay.textContent = `Error: ${data.error}`;
        this.elements.startDebateBtn.disabled = false;
        this.elements.stopDebateBtn.disabled = true;
        
        // Add error message to transcript
        const errorEntry = document.createElement('div');
        errorEntry.className = 'turn-entry turn-moderator';
        errorEntry.style.background = 'rgba(244, 67, 54, 0.2)';
        errorEntry.innerHTML = `
            <div class="turn-header">
                <span class="turn-agent">❌ Error</span>
                <span class="turn-time">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="turn-statement">Debate encountered an error: ${data.error}</div>
        `;
        
        this.elements.transcript.appendChild(errorEntry);
    }
    
    async createDebate() {
        const topic = this.elements.debateTopic.value.trim();
        const maxRounds = parseInt(this.elements.maxRounds.value);
        
        if (!topic) {
            alert('Please enter a debate topic');
            return;
        }
        
        this.elements.createDebateBtn.disabled = true;
        this.elements.createDebateBtn.textContent = this.getRandomRalphQuote();
        this.updateConnectionStatus('loading');
        
        try {
            const response = await fetch('/api/debate/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    topic: topic,
                    max_rounds: maxRounds
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            this.currentDebateId = data.debate_id;
            
            // Join the debate via WebSocket
            if (this.websocket && this.isConnected) {
                this.websocket.send(JSON.stringify({
                    type: 'join_debate',
                    debate_id: this.currentDebateId
                }));
            }
            
            // Update UI
            this.elements.debateTopicDisplay.textContent = topic;
            this.elements.debateSetup.style.display = 'none';
            this.elements.debateArena.style.display = 'block';
            this.elements.startDebateBtn.disabled = false;
            this.elements.createDebateBtn.disabled = false;
            this.elements.createDebateBtn.textContent = 'Create Debate';
            
            // Clear previous transcript
            this.elements.transcript.innerHTML = '';
            
            this.updateConnectionStatus('connected');
            
        } catch (error) {
            console.error('Failed to create debate:', error);
            alert('Failed to create debate. Please try again.');
            this.elements.createDebateBtn.disabled = false;
            this.updateConnectionStatus('disconnected');
        }
    }
    
    async startDebate() {
        if (!this.currentDebateId) {
            alert('No debate created yet');
            return;
        }
        
        this.elements.startDebateBtn.disabled = true;
        this.elements.stopDebateBtn.disabled = false;
        this.elements.debateStatusDisplay.textContent = 'Starting debate...';
        
        try {
            const response = await fetch(`/api/debate/${this.currentDebateId}/start`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            this.elements.debateStatusDisplay.textContent = 'Debate in progress...';
            
        } catch (error) {
            console.error('Failed to start debate:', error);
            alert('Failed to start debate. Please try again.');
            this.elements.startDebateBtn.disabled = false;
            this.elements.stopDebateBtn.disabled = true;
        }
    }
    
    async stopDebate() {
        if (!this.currentDebateId) {
            return;
        }
        
        try {
            const response = await fetch(`/api/debate/${this.currentDebateId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.elements.debateStatusDisplay.textContent = 'Debate stopped';
                this.elements.startDebateBtn.disabled = false;
                this.elements.stopDebateBtn.disabled = true;
            }
            
        } catch (error) {
            console.error('Failed to stop debate:', error);
        }
    }
    
    // Keep connection alive
    startHeartbeat() {
        setInterval(() => {
            if (this.websocket && this.isConnected) {
                this.websocket.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000); // Send ping every 30 seconds
    }
}

// Initialize the debate client when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.debateClient = new DebateClient();
    window.debateClient.startHeartbeat();
});