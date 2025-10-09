# LiveKit Voice AI Agent

An ultra-low-latency voice AI agent built with LiveKit that features emotion-aware responses, intelligent filler sounds, and comprehensive latency tracking. Perfect for building natural, conversational voice interfaces.

## Features

### 🎭 Emotion-Aware Voice Modulation
- LLM analyzes conversation context and outputs emotion metadata
- TTS dynamically adjusts voice parameters (speed, emotion) based on detected sentiment
- Supports: `neutral`, `happy`, `sad`, `angry`, `confused`, `curious`, `excited`
- Powered by Cartesia's ultra-low-latency TTS with experimental voice controls

### 🔊 Intelligent Filler Sounds
- Plays natural filler sounds ("hmm", "ah", "well") during LLM processing
- Emotion-matched fillers for conversational authenticity
- Configurable trigger thresholds to prevent awkward silences
- Automatically cancels when LLM responds

### ⚡ Latency Optimization
- Real-time latency tracking across the entire voice pipeline:
  - VAD → STT finalization
  - STT → LLM start
  - LLM Time To First Token (TTFT)
  - LLM → TTS start
  - TTS Time To First Chunk
  - Total end-to-end latency
- Optimized VAD settings for natural conversation flow
- Uses Cartesia's `sonic-english` model for ultra-low TTS latency

### 🧠 Voice Pipeline Architecture
```
User Speech → VAD (Silero) → STT (Deepgram Nova-2) → LLM (GPT-4o-mini) → TTS (Cartesia Sonic)
                                                            ↓
                                                    Emotion Analysis
                                                            ↓
                                            Voice Modulation + Filler Sounds
```

## Tech Stack

- **LiveKit**: Real-time voice infrastructure
- **Deepgram**: Speech-to-Text (Nova-2 Conversational AI model)
- **OpenAI**: Language model (GPT-4o-mini with structured outputs)
- **Cartesia**: Text-to-Speech (Sonic English - ultra-low latency)
- **Silero VAD**: Voice Activity Detection
- **FastAPI**: API server (optional)
- **Python 3.12+**: Runtime

## Installation

### Prerequisites
- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip
- LiveKit account ([sign up free](https://livekit.io))
- API keys for:
  - OpenAI
  - Deepgram
  - Cartesia

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/livekit-transient.git
cd livekit-transient
```

2. **Install dependencies**
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-instance.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# OpenAI API Key (for LLM)
OPENAI_API_KEY=your_openai_api_key

# Deepgram API Key (for STT)
DEEPGRAM_API_KEY=your_deepgram_api_key

# Cartesia API Key (for TTS)
CARTESIA_API_KEY=your_cartesia_api_key
CARTESIA_VOICE_ID=your_voice_id  # e.g., a0e99841-438c-4a64-b679-ae501e7d6091
```

4. **Generate filler sounds** (optional but recommended)
```bash
uv run python generate_filler_sounds.py
```

## Usage

### Run the Agent (Development Mode)

```bash
uv run python agent.py dev
```

This starts the agent in development mode with a local LiveKit server.

### Connect to the Agent

1. Open the LiveKit Playground: `https://your-livekit-instance.livekit.cloud`
2. Create a new room
3. The agent will automatically join and greet you

Alternatively, build your own client using [LiveKit's client SDKs](https://docs.livekit.io/client-sdk-js/).

### Production Deployment

```bash
# Using uv
uv run python agent.py start

# Or with custom worker options
uv run python agent.py start --num-workers 4
```

## Configuration

### Emotion Settings
Edit `prompts/cartesia_emotion_config.json` to customize voice modulation:
```json
{
  "emotions": {
    "happy": {
      "speed": 1.1,
      "emotion": ["positivity:highest", "curiosity:high"]
    },
    "angry": {
      "speed": 1.2,
      "emotion": ["anger:high", "intensity:highest"]
    }
  }
}
```

### Filler Sounds
Edit `prompts/filler_sounds_config.json` to configure:
- Trigger threshold (delay before playing filler)
- Filler texts per emotion
- Cartesia voice settings for generation

### System Prompt
Customize the agent's personality in `prompts/insurance_salesman_prompt.md`.

### VAD Settings
Adjust Voice Activity Detection in [agent.py:280-285](agent.py#L280-L285):
```python
vad=silero.VAD.load(
    min_speech_duration=0.1,        # Minimum 100ms of speech to start
    min_silence_duration=0.2,       # End speech after 200ms of silence
    prefix_padding_duration=0.1,    # 100ms padding before speech
    activation_threshold=0.5,       # Speech detection sensitivity
)
```

## Project Structure

```
livekit-transient/
├── agent.py                    # Main agent implementation
├── filler_manager.py           # Filler sound management
├── generate_filler_sounds.py  # TTS generation for filler sounds
├── config.py                   # Settings and environment validation
├── main.py                     # FastAPI server (optional)
├── prompts/
│   ├── insurance_salesman_prompt.md      # System prompt
│   ├── cartesia_emotion_config.json      # Voice modulation settings
│   └── filler_sounds_config.json         # Filler sound configuration
├── filler_sounds/              # Generated filler audio files
└── tests/                      # Integration tests
```

## Development

### Testing

Run integration tests with actual API calls:
```bash
uv run python tests/test_emotion_pipeline.py
```

### Latency Monitoring

The agent logs detailed latency metrics for each conversation turn:
```
============================================================
LATENCY ANALYSIS
============================================================
VAD → STT Finalization: 342.15ms
STT → LLM Start: 12.45ms
LLM TTFT (Time To First Token): 287.33ms
LLM Total Processing: 1543.21ms
LLM → TTS Start: 5.67ms
TTS Time To First Chunk: 156.89ms
TTS Total Generation: 2341.56ms
TOTAL END-TO-END LATENCY: 786.37ms
============================================================
```

### Customizing the Agent

1. **Change the persona**: Edit `prompts/insurance_salesman_prompt.md`
2. **Add emotions**: Update `prompts/cartesia_emotion_config.json`
3. **Modify LLM**: Change model in [agent.py:271](agent.py#L271)
4. **Switch TTS provider**: Replace Cartesia with ElevenLabs or other providers
5. **Adjust VAD sensitivity**: Tune parameters in [agent.py:279-285](agent.py#L279-L285)

## How It Works

### Emotion Detection Flow

1. User speaks → VAD detects speech → STT transcribes
2. LLM receives transcript and outputs structured JSON:
   ```json
   {
     "emotion": "happy",
     "intensity": 0.8,
     "message": "That's wonderful! I'm so glad to hear that."
   }
   ```
3. Agent extracts emotion and intensity
4. TTS voice controls are updated dynamically
5. Filler sound manager tracks last emotion for future fillers

### Filler Sound System

1. LLM processing starts → Filler timer begins (default: 800ms)
2. If LLM first token arrives before threshold:
   - Timer cancelled, no filler plays
3. If threshold exceeded:
   - Emotion-appropriate filler plays ("hmm...", "well...")
   - Reduces perceived latency
4. Filler automatically stops when LLM response starts

## API Keys & Pricing

- **LiveKit**: Free tier available, pay-as-you-go
- **Deepgram**: $0.0043/min for Nova-2 model
- **OpenAI**: ~$0.15/1M input tokens, ~$0.60/1M output tokens (GPT-4o-mini)
- **Cartesia**: ~$0.05/1K characters (Sonic model)

Typical cost: **~$0.02-0.05 per minute** of conversation.

## Troubleshooting

### Common Issues

**Agent doesn't respond:**
- Check all API keys are valid in `.env`
- Verify LiveKit connection: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`
- Check firewall/network allows WebSocket connections

**High latency:**
- Use Cartesia's `sonic-english` model (already configured)
- Reduce VAD `min_silence_duration` (may cause interruptions)
- Check your network connection to API providers
- Consider geographic proximity to API servers

**Filler sounds not playing:**
- Run `python generate_filler_sounds.py` to create audio files
- Verify `filler_sounds/` directory contains `.wav` files
- Check `prompts/filler_sounds_config.json` exists

**Audio quality issues:**
- Try different Cartesia voice IDs
- Adjust `speed` in emotion config (range: 0.8-1.3)
- Check room audio settings in LiveKit dashboard

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Follow existing code style (snake_case, prompts in `prompts/`)
4. Test with real API calls (not mocks)
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Built with [LiveKit Agents Framework](https://docs.livekit.io/agents/)
- Emotion-aware TTS inspired by conversational AI research
- Filler sound technique based on human conversation patterns

## Links

- [LiveKit Documentation](https://docs.livekit.io/)
- [Cartesia Sonic TTS](https://cartesia.ai/)
- [Deepgram Nova-2](https://deepgram.com/product/nova-2)
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)

---

**Built with ❤️ for natural voice conversations**
