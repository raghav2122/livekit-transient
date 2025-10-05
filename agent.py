"""LiveKit Voice Agent implementation using AgentSession API.

This agent uses STT (Deepgram) -> LLM (OpenAI) -> TTS (ElevenLabs) pipeline.
"""

import logging
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import Agent, AgentSession, WorkerOptions, cli, RoomInputOptions
from livekit.plugins import deepgram, openai, elevenlabs, silero

from config import settings

load_dotenv()

logger = logging.getLogger("voice-agent")


class VoiceAssistant(Agent):
    """Voice assistant agent with custom instructions."""

    def __init__(self) -> None:
        super().__init__(
            instructions=settings.AGENT_INSTRUCTIONS,
        )


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
            model_id="eleven_turbo_v2_5",
        ),
        vad=silero.VAD.load(),
    )

    # Start the session
    await session.start(
        room=ctx.room,
        agent=VoiceAssistant(),
        room_input_options=RoomInputOptions(
            # Add noise cancellation if needed
            # noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # Generate initial greeting
    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
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
