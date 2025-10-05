# LiveKit Voice AI Agent

A real-time voice AI agent built with **LiveKit**, **FastAPI**, and modern AI services. This project implements a complete voice conversation pipeline using:

- **STT (Speech-to-Text)**: Deepgram
- **LLM (Language Model)**: OpenAI GPT-4
- **TTS (Text-to-Speech)**: ElevenLabs
- **Infrastructure**: LiveKit for WebRTC real-time communication

## Architecture

The system uses LiveKit's `VoicePipelineAgent` which chains together:

```
User Audio → Deepgram STT → OpenAI GPT → ElevenLabs TTS → Agent Audio
```

The pipeline handles:
- Turn detection and interruptions
- Voice activity detection (VAD)
- Real-time streaming audio
- Natural conversation flow

## Project Structure

```
livekit-transient/
├── pyproject.toml          # UV package configuration
├── .env                    # Environment variables (create from .env.example)
├── .env.example            # Template for environment variables
├── main.py                 # FastAPI REST API server
├── agent.py                # LiveKit voice agent implementation
├── config.py               # Configuration management
└── README.md               # This file
```

## Prerequisites

- **Python** >= 3.12
- **UV** package manager ([installation guide](https://github.com/astral-sh/uv))
- **LiveKit Cloud** account or self-hosted instance
- API keys for:
  - LiveKit
  - OpenAI
  - Deepgram
  - ElevenLabs

## Setup

### 1. Clone and Install Dependencies

```bash
cd livekit-transient

# Install dependencies using UV
uv sync
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
```

Required environment variables:

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-instance.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# OpenAI API Key
OPENAI_API_KEY=sk-...

# Deepgram API Key
DEEPGRAM_API_KEY=your_deepgram_key

# ElevenLabs API Key
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Optional: Default is Rachel
```

### 3. Get API Keys

- **LiveKit**: Sign up at [livekit.io](https://livekit.io) or use self-hosted
- **OpenAI**: Get API key from [platform.openai.com](https://platform.openai.com)
- **Deepgram**: Sign up at [deepgram.com](https://deepgram.com)
- **ElevenLabs**: Get API key from [elevenlabs.io](https://elevenlabs.io)

## Usage

### Running the FastAPI Server

Start the REST API server to manage rooms and tokens:

```bash
uv run uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

**API Endpoints:**

- `GET /` - Health check
- `POST /rooms` - Create a new LiveKit room
- `POST /token` - Generate access token for a participant
- `GET /rooms` - List all active rooms
- `DELETE /rooms/{room_name}` - Delete a room

**Example: Create a room**

```bash
curl -X POST http://localhost:8000/rooms \
  -H "Content-Type: application/json" \
  -d '{"room_name": "my-voice-room"}'
```

**Example: Generate token**

```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/json" \
  -d '{
    "room_name": "my-voice-room",
    "participant_identity": "user123",
    "participant_name": "John Doe"
  }'
```

### Running the Voice Agent

Start the LiveKit agent worker:

```bash
uv run python agent.py dev
```

This will:
1. Connect to your LiveKit server
2. Wait for participants to join rooms
3. Automatically start voice conversations
4. Handle STT → LLM → TTS pipeline

### Testing in Console Mode

For testing, you can run the agent in console mode:

```bash
uv run python agent.py console
```

This allows you to test the voice agent directly from your terminal.

## How It Works

### 1. FastAPI Server (`main.py`)

- Provides REST endpoints to manage LiveKit infrastructure
- Creates rooms for voice conversations
- Generates access tokens for participants
- Uses LiveKit API for room management

### 2. Voice Agent (`agent.py`)

- Implements `VoicePipelineAgent` with custom configuration
- Connects to LiveKit rooms as a participant
- Processes audio through the STT → LLM → TTS pipeline
- Handles conversation flow, interruptions, and turn detection

### 3. Configuration (`config.py`)

- Loads environment variables
- Validates required API keys
- Provides centralized settings management

## Voice Pipeline Details

The `VoicePipelineAgent` automatically manages:

- **Voice Activity Detection (VAD)**: Detects when users start/stop speaking
- **Turn Detection**: Identifies conversation turns for natural dialogue
- **Interruption Handling**: Allows users to interrupt the agent mid-sentence
- **Streaming**: Real-time audio streaming with minimal latency

## Customization

### Change the Agent's Instructions

Edit `config.py`:

```python
AGENT_INSTRUCTIONS: str = """Your custom instructions here..."""
```

### Use Different AI Models

Edit `agent.py`:

```python
# Change STT model
stt=deepgram.STT(
    api_key=settings.DEEPGRAM_API_KEY,
    model="nova-2-general",  # Change model here
)

# Change LLM
llm=openai.LLM(
    api_key=settings.OPENAI_API_KEY,
    model="gpt-4o",  # Use GPT-4 instead
)

# Change TTS voice
tts=elevenlabs.TTS(
    api_key=settings.ELEVENLABS_API_KEY,
    voice_id="different-voice-id",  # Change voice
    model_id="eleven_turbo_v2_5",
)
```

### Available ElevenLabs Voices

Popular voice IDs:
- `21m00Tcm4TlvDq8ikWAM` - Rachel (default)
- `EXAVITQu4vr4xnSDxMaL` - Bella
- `ErXwobaYiN019PkySvjV` - Antoni

Find more at [elevenlabs.io/voice-library](https://elevenlabs.io/voice-library)

## Development

### Project Dependencies

Core packages:
- `fastapi` - Modern web framework
- `uvicorn` - ASGI server
- `livekit-agents` - LiveKit agent framework
- `livekit-plugins-openai` - OpenAI integration
- `livekit-plugins-deepgram` - Deepgram STT
- `livekit-plugins-elevenlabs` - ElevenLabs TTS
- `livekit-plugins-silero` - Voice activity detection
- `python-dotenv` - Environment variable management

### Adding New Features

To add tools or functions the agent can use:

```python
from livekit.agents import llm

# Define a function
async def get_weather(location: str) -> str:
    return f"The weather in {location} is sunny"

# Add to agent context
fnc_ctx = llm.FunctionContext()
fnc_ctx.ai_callable()(get_weather)

# Update agent creation in agent.py
agent = VoicePipelineAgent(
    # ... existing config ...
    fnc_ctx=fnc_ctx,
)
```

## Troubleshooting

### Common Issues

**Import errors**:
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

**API connection errors**:
- Verify all API keys are correct in `.env`
- Check LiveKit URL format: `wss://your-instance.livekit.cloud`
- Ensure you have credits/quota on all services

**Agent not responding**:
- Check agent logs for errors
- Verify room exists before connecting agent
- Ensure participant has proper permissions

## Resources

- [LiveKit Documentation](https://docs.livekit.io)
- [LiveKit Agents Guide](https://docs.livekit.io/agents/)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [UV Package Manager](https://github.com/astral-sh/uv)

## License

MIT
