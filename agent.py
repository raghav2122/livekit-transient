"""LiveKit Voice Agent implementation using AgentSession API.

This agent uses STT (Deepgram) -> LLM (OpenAI) -> TTS (Cartesia) pipeline
with emotion-based voice modulation.
"""

import json
import logging
import time
from pathlib import Path
from typing import AsyncIterable, Optional
from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import Agent, AgentSession, WorkerOptions, cli, RoomInputOptions, llm
from livekit.plugins import deepgram, openai, cartesia, silero

from config import settings
from filler_manager import FillerSoundManager

load_dotenv()

logger = logging.getLogger("voice-agent")


class LatencyTracker:
    """Track latency across the voice pipeline stages."""

    def __init__(self):
        self.timestamps = {}
        self.session_start = None

    def mark(self, event: str):
        """Mark a timestamp for an event."""
        timestamp = time.time()
        self.timestamps[event] = timestamp
        return timestamp

    def get_duration(self, start_event: str, end_event: str) -> float:
        """Get duration between two events in milliseconds."""
        if start_event not in self.timestamps or end_event not in self.timestamps:
            return 0.0
        return (self.timestamps[end_event] - self.timestamps[start_event]) * 1000

    def log_latency(self):
        """Log all latency measurements."""
        if not self.timestamps:
            return

        logger.info("=" * 60)
        logger.info("LATENCY ANALYSIS")
        logger.info("=" * 60)

        # VAD to STT
        if "user_speech_end" in self.timestamps and "stt_finalized" in self.timestamps:
            vad_to_stt = self.get_duration("user_speech_end", "stt_finalized")
            logger.info(f"VAD → STT Finalization: {vad_to_stt:.2f}ms")

        # STT to LLM start
        if "stt_finalized" in self.timestamps and "llm_start" in self.timestamps:
            stt_to_llm = self.get_duration("stt_finalized", "llm_start")
            logger.info(f"STT → LLM Start: {stt_to_llm:.2f}ms")

        # LLM TTFT (Time To First Token)
        if "llm_start" in self.timestamps and "llm_first_token" in self.timestamps:
            llm_ttft = self.get_duration("llm_start", "llm_first_token")
            logger.info(f"LLM TTFT (Time To First Token): {llm_ttft:.2f}ms")

        # LLM completion
        if "llm_start" in self.timestamps and "llm_complete" in self.timestamps:
            llm_total = self.get_duration("llm_start", "llm_complete")
            logger.info(f"LLM Total Processing: {llm_total:.2f}ms")

        # LLM to TTS start
        if "llm_complete" in self.timestamps and "tts_start" in self.timestamps:
            llm_to_tts = self.get_duration("llm_complete", "tts_start")
            logger.info(f"LLM → TTS Start: {llm_to_tts:.2f}ms")

        # TTS first chunk
        if "tts_start" in self.timestamps and "tts_first_chunk" in self.timestamps:
            tts_ttfc = self.get_duration("tts_start", "tts_first_chunk")
            logger.info(f"TTS Time To First Chunk: {tts_ttfc:.2f}ms")

        # TTS completion
        if "tts_start" in self.timestamps and "tts_complete" in self.timestamps:
            tts_total = self.get_duration("tts_start", "tts_complete")
            logger.info(f"TTS Total Generation: {tts_total:.2f}ms")

        # Total end-to-end latency
        if "user_speech_end" in self.timestamps and "tts_first_chunk" in self.timestamps:
            total_latency = self.get_duration("user_speech_end", "tts_first_chunk")
            logger.info(f"TOTAL END-TO-END LATENCY: {total_latency:.2f}ms")

        logger.info("=" * 60)

        # Reset for next turn
        self.timestamps.clear()


# Global latency tracker
latency_tracker = LatencyTracker()


def load_emotion_config():
    """Load Cartesia emotion configuration from prompts folder."""
    config_path = Path(__file__).parent / "prompts" / "cartesia_emotion_config.json"
    with open(config_path) as f:
        return json.load(f)


def load_insurance_prompt():
    """Load insurance salesman system prompt."""
    prompt_path = Path(__file__).parent / "prompts" / "insurance_salesman_prompt.md"
    with open(prompt_path) as f:
        return f.read()


class EmotionalVoiceAssistant(Agent):
    """Emotion-aware voice assistant that adapts TTS based on LLM emotion output."""

    def __init__(self, filler_manager: Optional[FillerSoundManager] = None, audio_source: Optional[rtc.AudioSource] = None) -> None:
        super().__init__(
            instructions=load_insurance_prompt(),
        )
        self.emotion_config = load_emotion_config()
        self.filler_manager = filler_manager
        self.audio_source = audio_source
        self.last_emotion = "neutral"

    async def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        tools: list[llm.FunctionTool],
        model_settings
    ) -> AsyncIterable[llm.ChatChunk]:
        """Override LLM node to get structured JSON response with emotion."""
        latency_tracker.mark("llm_start")
        first_token = True

        # Start filler sound timer if configured
        if self.filler_manager and self.audio_source:
            self.filler_manager.start_filler_timer(
                self.audio_source,
                emotion=self.last_emotion
            )

        # Use default LLM processing
        async for chunk in Agent.default.llm_node(self, chat_ctx, tools, model_settings):
            if first_token:
                latency_tracker.mark("llm_first_token")
                # Cancel filler sound when first token arrives
                if self.filler_manager:
                    self.filler_manager.cancel_filler()
                first_token = False
            yield chunk

        latency_tracker.mark("llm_complete")

    async def tts_node(
        self,
        text: AsyncIterable[str],
        model_settings
    ):
        """Override TTS node to apply emotion-based voice settings."""
        latency_tracker.mark("tts_start")

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

            # Track last emotion for filler sound selection
            self.last_emotion = emotion
            if self.filler_manager:
                self.filler_manager.set_emotion(emotion)

            logger.info(f"Emotion: {emotion}, Intensity: {intensity}")

            # Get base emotion settings for Cartesia
            emotion_settings = self.emotion_config["emotions"].get(emotion, self.emotion_config["emotions"]["neutral"])

            # Update Cartesia TTS voice controls
            tts = self.tts
            if isinstance(tts, cartesia.TTS):
                # Cartesia uses experimental_voice_controls
                voice_controls = {
                    "speed": emotion_settings["speed"],
                    "emotion": emotion_settings["emotion"]
                }
                tts.update_options(experimental_voice_controls=voice_controls)

            # Return message text for TTS
            async def text_stream():
                yield message

            # Wrap TTS output to track first chunk
            first_chunk = True
            async for audio_chunk in Agent.default.tts_node(self, text_stream(), model_settings):
                if first_chunk:
                    latency_tracker.mark("tts_first_chunk")
                    first_chunk = False
                yield audio_chunk

            latency_tracker.mark("tts_complete")
            latency_tracker.log_latency()

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse emotion from LLM response: {e}")
            # Fallback to original text
            async def fallback_stream():
                yield full_text

            # Wrap TTS output to track first chunk
            first_chunk = True
            async for audio_chunk in Agent.default.tts_node(self, fallback_stream(), model_settings):
                if first_chunk:
                    latency_tracker.mark("tts_first_chunk")
                    first_chunk = False
                yield audio_chunk

            latency_tracker.mark("tts_complete")
            latency_tracker.log_latency()


async def entrypoint(ctx: agents.JobContext):
    """Agent entrypoint - called when agent joins a room.

    Args:
        ctx: JobContext containing room and job information.
    """
    logger.info(f"Starting agent for room: {ctx.room.name}")

    # Initialize filler sound manager
    filler_sounds_dir = Path(__file__).parent / "filler_sounds"
    filler_config_path = Path(__file__).parent / "prompts" / "filler_sounds_config.json"

    filler_manager = None
    if filler_sounds_dir.exists() and filler_config_path.exists():
        filler_manager = FillerSoundManager(filler_sounds_dir, filler_config_path)
        logger.info("Filler sound manager initialized")
    else:
        logger.warning("Filler sounds not found, running without filler sound support")

    # Create audio source for filler sounds
    # Note: We'll need to get this from the room after connecting
    audio_source = None

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
        tts=cartesia.TTS(
            api_key=settings.CARTESIA_API_KEY,
            voice=settings.CARTESIA_VOICE_ID,
            model="sonic-english",  # Ultra-low latency model
        ),
        vad=silero.VAD.load(
            min_speech_duration=0.1,        # Minimum 100ms of speech to start
            min_silence_duration=0.2,       # End speech after 200ms of silence
            prefix_padding_duration=0.1,    # 100ms padding before speech
            activation_threshold=0.5,       # Speech detection sensitivity
        ),
    )

    # Add event listeners for latency tracking
    @session.on("user_speech_committed")
    def on_user_speech_committed(msg):
        """Track when user finishes speaking (VAD detected end)."""
        latency_tracker.mark("user_speech_end")
        logger.debug(f"User speech ended: {msg.text if hasattr(msg, 'text') else ''}")

    @session.on("user_transcript_committed")
    def on_transcript_committed(msg):
        """Track when STT finalizes transcript."""
        latency_tracker.mark("stt_finalized")
        logger.debug(f"STT finalized transcript: {msg.text if hasattr(msg, 'text') else ''}")

    @session.on("agent_started_speaking")
    def on_agent_speaking():
        """Track when agent starts speaking."""
        logger.debug("Agent started speaking")

    # Start the session with emotional voice assistant
    await session.start(
        room=ctx.room,
        agent=EmotionalVoiceAssistant(
            filler_manager=filler_manager,
            audio_source=audio_source
        ),
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
