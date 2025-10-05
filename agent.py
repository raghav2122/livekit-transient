"""LiveKit Voice Agent implementation using AgentSession API.

This agent uses STT (Deepgram) -> LLM (OpenAI) -> TTS (ElevenLabs) pipeline
with emotion-based voice modulation.
"""

import json
import logging
from pathlib import Path
from typing import AsyncIterable
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import Agent, AgentSession, WorkerOptions, cli, RoomInputOptions, llm
from livekit.plugins import deepgram, openai, elevenlabs, silero
from livekit.plugins.elevenlabs import VoiceSettings

from config import settings

load_dotenv()

logger = logging.getLogger("voice-agent")


def load_emotion_config():
    """Load emotion configuration from prompts folder."""
    config_path = Path(__file__).parent / "prompts" / "emotion_config.json"
    with open(config_path) as f:
        return json.load(f)


def load_insurance_prompt():
    """Load insurance salesman system prompt."""
    prompt_path = Path(__file__).parent / "prompts" / "insurance_salesman_prompt.md"
    with open(prompt_path) as f:
        return f.read()


class EmotionalVoiceAssistant(Agent):
    """Emotion-aware voice assistant that adapts TTS based on LLM emotion output."""

    def __init__(self) -> None:
        super().__init__(
            instructions=load_insurance_prompt(),
        )
        self.emotion_config = load_emotion_config()

    async def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        tools: list[llm.FunctionTool],
        model_settings
    ) -> AsyncIterable[llm.ChatChunk]:
        """Override LLM node to get structured JSON response with emotion."""
        # Use default LLM processing
        async for chunk in Agent.default.llm_node(self, chat_ctx, tools, model_settings):
            yield chunk

    async def tts_node(
        self,
        text: AsyncIterable[str],
        model_settings
    ):
        """Override TTS node to apply emotion-based voice settings."""
        # Collect full text from LLM
        full_text = ""
        async for chunk in text:
            full_text += chunk

        # Parse JSON response
        json_text = full_text.strip()
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        if json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]
        json_text = json_text.strip()

        try:
            response_data = json.loads(json_text)
            emotion = response_data.get("emotion", "neutral")
            intensity = response_data.get("intensity", 0.5)
            message = response_data.get("message", full_text)

            logger.info(f"Emotion: {emotion}, Intensity: {intensity}")

            # Get base emotion settings
            emotion_settings = self.emotion_config["emotions"].get(emotion, self.emotion_config["emotions"]["neutral"])

            # Apply intensity scaling (optional - adjust settings based on intensity)
            # For now, just use the preset

            # Update TTS voice settings
            tts = self.tts
            if isinstance(tts, elevenlabs.TTS):
                voice_settings = VoiceSettings(
                    stability=emotion_settings["stability"],
                    similarity_boost=emotion_settings["similarity_boost"],
                    style=emotion_settings["style"],
                    use_speaker_boost=emotion_settings["use_speaker_boost"]
                )
                tts.update_options(voice_settings=voice_settings)

            # Return message text for TTS
            async def text_stream():
                yield message

            return Agent.default.tts_node(self, text_stream(), model_settings)

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse emotion from LLM response: {e}")
            # Fallback to original text
            async def fallback_stream():
                yield full_text

            return Agent.default.tts_node(self, fallback_stream(), model_settings)


async def entrypoint(ctx: agents.JobContext):
    """Agent entrypoint - called when agent joins a room.

    Args:
        ctx: JobContext containing room and job information.
    """
    logger.info(f"Starting agent for room: {ctx.room.name}")

    # Create agent session with STT, LLM, and TTS
    session = AgentSession(
        stt=deepgram.STT(
            api_key=settings.DEEPGRAM_API_KEY,
            model="nova-2-conversationalai",
        ),
        llm=openai.LLM(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-4o-mini",
        ),
        tts=elevenlabs.TTS(
            api_key=settings.ELEVENLABS_API_KEY,
            voice_id=settings.ELEVENLABS_VOICE_ID,
            model="eleven_turbo_v2_5",
        ),
        vad=silero.VAD.load(),
    )

    # Start the session with emotional voice assistant
    await session.start(
        room=ctx.room,
        agent=EmotionalVoiceAssistant(),
        room_input_options=RoomInputOptions(
            # Add noise cancellation if needed
            # noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Generate initial greeting
    await session.generate_reply(
        instructions="Greet the customer as a friendly insurance salesman. Introduce yourself and ask how you can help them today."
    )

    logger.info("Agent session started successfully")


if __name__ == "__main__":
    # Validate settings before starting
    settings.validate()

    # Run the agent with CLI
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
