"""Configuration settings for the LiveKit Voice AI application."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # LiveKit Configuration
    LIVEKIT_URL: str = os.getenv("LIVEKIT_URL", "")
    LIVEKIT_API_KEY: str = os.getenv("LIVEKIT_API_KEY", "")
    LIVEKIT_API_SECRET: str = os.getenv("LIVEKIT_API_SECRET", "")

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Deepgram Configuration
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")

    # ElevenLabs Configuration
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID: str = os.getenv(
        "ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"
    )  # Default: Rachel voice

    # Agent Configuration
    AGENT_INSTRUCTIONS: str = """You are a helpful voice assistant.
    You can answer questions and have natural conversations with users.
    Keep your responses concise and conversational."""

    @classmethod
    def validate(cls) -> bool:
        """Validate that all required settings are present."""
        required_keys = [
            "LIVEKIT_URL",
            "LIVEKIT_API_KEY",
            "LIVEKIT_API_SECRET",
            "OPENAI_API_KEY",
            "DEEPGRAM_API_KEY",
            "ELEVENLABS_API_KEY",
        ]

        missing_keys = [
            key for key in required_keys if not getattr(cls, key, None)
        ]

        if missing_keys:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_keys)}"
            )

        return True


# Create a global settings instance
settings = Settings()
