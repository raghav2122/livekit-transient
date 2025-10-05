"""LiveKit Voice Agent implementation using VoicePipelineAgent.

This agent connects STT (Deepgram) -> LLM (OpenAI) -> TTS (ElevenLabs)
for real-time voice conversations.
"""

import logging
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, openai, elevenlabs, silero

from config import settings

logger = logging.getLogger("voice-agent")


def create_agent() -> VoicePipelineAgent:
    """Create and configure the VoicePipelineAgent.

    Returns:
        VoicePipelineAgent: Configured voice agent with STT, LLM, and TTS.
    """
    logger.info("Creating voice pipeline agent...")

    # Configure the agent with the voice pipeline
    agent = VoicePipelineAgent(
        # Speech-to-Text: Deepgram
        stt=deepgram.STT(
            api_key=settings.DEEPGRAM_API_KEY,
            model="nova-2-conversationalai",
        ),
        # Large Language Model: OpenAI GPT
        llm=openai.LLM(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-4o-mini",
        ),
        # Text-to-Speech: ElevenLabs
        tts=elevenlabs.TTS(
            api_key=settings.ELEVENLABS_API_KEY,
            voice_id=settings.ELEVENLABS_VOICE_ID,
            model_id="eleven_turbo_v2_5",
        ),
        # Voice Activity Detection
        vad=silero.VAD.load(),
        # Chat context with initial instructions
        chat_ctx=llm.ChatContext().append(
            role="system",
            text=settings.AGENT_INSTRUCTIONS,
        ),
    )

    return agent


async def entrypoint(ctx: JobContext):
    """Agent entrypoint - called when agent joins a room.

    Args:
        ctx: JobContext containing room and job information.
    """
    logger.info(f"Starting agent for room: {ctx.room.name}")

    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Create the voice agent
    agent = create_agent()

    # Start the agent
    agent.start(ctx.room)

    # Wait for the first participant to join
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant joined: {participant.identity}")

    # Start the agent session with the participant
    await agent.say("Hello! I'm your voice assistant. How can I help you today?", allow_interruptions=True)

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
