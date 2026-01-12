# AI Debate Arena

Multi-party AI debate system powered by PydanticAI with real-time streaming and intelligent moderation.

## Features

- **Multi-Debater Support (2-6)**: Configure any number of debaters with custom positions
- **Smart Moderator**: AI moderator keeps debates focused on the topic
- **Pre-built Templates**: God's existence, AI consciousness, Free will debates
- **Custom Debates**: Create debates on any topic with custom positions
- **Real-time Streaming**: WebSocket streaming for live debate updates
- **Topic Relevance Checking**: Automatic detection and redirection of off-topic arguments
- **Voice Synthesis Ready**: Liquid Audio integration for voice output
- **Multiple LLM Support**: Groq (recommended), OpenAI, or local Ollama

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **One of the following LLM services** (in order of preference):
   - **Groq API** (fastest - recommended)
   - **Google Gemini API**
   - **Local Ollama** (fallback)
3. **Liquid Audio** (install via pip)

### Installation

```bash
# 1. Clone or download the project
cd ai_debate_arena

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env

# 4. Edit .env file with your API keys
nano .env
```

### Environment Configuration

Edit `.env` file:

```bash
# For Groq (fastest, recommended)
GROQ_API_KEY=your_groq_api_key_here

# OR for Google Gemini
GOOGLE_API_KEY=your_google_api_key_here

# OR use local Ollama (no API key needed)
OLLAMA_URL=http://localhost:11434

# Server configuration
PORT=8080
DEBATE_MAX_ROUNDS=3
TURN_DURATION_SECONDS=30
```

### Getting API Keys

#### Option 1: Groq (Recommended - Fast & Free)
1. Visit [Groq Console](https://console.groq.com/)
2. Sign up for free account
3. Create API key
4. Add to `.env` as `GROQ_API_KEY`

#### Option 2: Google Gemini
1. Visit [Google AI Studio](https://makersuite.google.com/)
2. Create API key
3. Add to `.env` as `GOOGLE_API_KEY`

#### Option 3: Local Ollama (Automatic Fallback)
1. Install [Ollama](https://ollama.ai/)
2. Run: `ollama serve`
3. The system automatically uses your best available model:
   - **gemma2:latest** (recommended for debates) ✅ Available
   - **llama3:instruct** (instruction-tuned) ✅ Available  
   - **mistral:latest** (good reasoning) ✅ Available
   - Other models as fallback ✅ Available

### Running the Application

```bash
# Start the debate server
python main.py
```

Open your browser to `http://localhost:8080`

## 🎯 How to Use

1. **Enter a Debate Topic**: Type any controversial or interesting topic
2. **Select Rounds**: Choose number of debate rounds (2-5)
3. **Create Debate**: Click "Create Debate" to set up the arena
4. **Start Debate**: Click "Start Debate" to begin the AI discussion
5. **Watch & Listen**: Enjoy real-time debate with voice synthesis

### Example Topics

- "Should AI replace human teachers in schools?"
- "Is social media harmful to society?"
- "Should we colonize Mars?"
- "Is remote work better than office work?"
- "Should cryptocurrency replace traditional money?"

## 🏗️ Architecture

### Core Components

```
ai_debate_arena/
├── src/
│   ├── debate_engine.py      # Core debate logic & Liquid Audio
│   ├── llm_integration.py    # Multi-provider LLM integration
│   ├── audio_server.py       # WebSocket + HTTP server
│   └── debate_scoring.py     # Argument analysis (optional)
├── public/
│   ├── index.html           # Web interface
│   └── debate-client.js     # Frontend JavaScript
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

### Flow

1. **Setup**: User creates debate via web interface
2. **LLM Generation**: Agents generate arguments using selected LLM
3. **Voice Synthesis**: Arguments converted to speech via Liquid Audio
4. **Streaming**: Audio + text streamed to browser via WebSocket
5. **Visualization**: Real-time updates in web interface

## 🔧 Configuration

### Agent Personalities

Agents have distinct personalities defined in `debate_engine.py`:

- **Dr. Advocate** (Pro): Analytical, evidence-based, uses statistics
- **Prof. Challenger** (Con): Critical, philosophical, emphasizes ethics

### LLM Models

| Provider | Model | Speed | Quality |
|----------|-------|--------|---------|
| Groq | mixtral-8x7b-32768 | ⚡⚡⚡ | ⭐⭐⭐ |
| Google | gemini-pro | ⚡⚡ | ⭐⭐⭐⭐ |
| Ollama | llama2/mistral | ⚡ | ⭐⭐ |

## 🎨 Customization

### Adding New Agent Personalities

Edit `src/debate_engine.py`:

```python
Agent(
    id="agent_new",
    name="New Agent",
    role=DebateRole.PRO,
    voice_id=3,  # Use 4th voice
    personality="your personality here",
    argument_style="your style here"
)
```

### Custom Debate Topics

Add pre-defined topics in `public/index.html`:

```html
<option value="Your custom topic">Your Custom Topic</option>
```

### Styling Changes

Edit `public/index.html` CSS section for custom colors, fonts, layouts.

## 📊 Advanced Features

### Debate Scoring (Optional)

The system includes argument analysis in `debate_scoring.py`:

- Logical fallacy detection
- Argument quality scoring
- Audience simulation
- Momentum tracking

### WebSocket Events

Real-time events streamed to browser:

```javascript
{
  "type": "debate_event",
  "event": "turn_completed",
  "turn": {
    "agent_name": "Dr. Advocate",
    "statement": "...",
    "timestamp": 1234567890
  }
}
```

## 🛠️ Troubleshooting

### Common Issues

**No audio playing:**
- Ensure browser permissions for audio
- Check volume slider in interface
- Verify Liquid Audio installation

**LLM generation failed:**
- Check API keys in `.env`
- Verify network connectivity
- Review logs in `debate_arena.log`

**WebSocket connection failed:**
- Check firewall settings
- Verify port 8080 is available
- Try different browser

### Debug Mode

Add to `.env`:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

### Performance Tuning

For faster debates:
1. Use Groq API (fastest LLM)
2. Reduce max_rounds to 2-3
3. Use shorter debate topics
4. Run on faster hardware

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📝 License

MIT License - feel free to use for personal and commercial projects!

## 🙏 Acknowledgments

- **Liquid AI** for the Liquid Audio model
- **Groq** for fast LLM inference
- **Google** for Gemini API
- **Ollama** for local LLM support

---

**Ready to watch AIs debate? Start your arena now! 🎭**