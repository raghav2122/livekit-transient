"""Generate emotion-based filler sound audio files using ElevenLabs TTS.

This script creates short audio files for filler sounds (hmm, ah, etc.)
with different emotional voice settings for each emotion category.
"""

import asyncio
import json
import wave
from pathlib import Path

import aiohttp
from livekit.plugins import elevenlabs
from livekit.plugins.elevenlabs import VoiceSettings

from config import settings


async def generate_filler_sounds():
    """Generate all filler sound audio files."""
    # Load configurations
    emotion_config_path = Path(__file__).parent / "prompts" / "emotion_config.json"
    filler_config_path = Path(__file__).parent / "prompts" / "filler_sounds_config.json"

    with open(emotion_config_path) as f:
        emotion_config = json.load(f)

    with open(filler_config_path) as f:
        filler_config = json.load(f)

    # Create output directory
    output_dir = Path(__file__).parent / "filler_sounds"
    output_dir.mkdir(exist_ok=True)

    print(f"Generating filler sounds in: {output_dir}")

    async with aiohttp.ClientSession() as http_session:
        for emotion, fillers in filler_config["fillers"].items():
            print(f"\n{'='*60}")
            print(f"Generating {emotion.upper()} filler sounds")
            print(f"{'='*60}")

            # Get emotion-specific voice settings
            emotion_settings = emotion_config["emotions"].get(
                emotion, emotion_config["emotions"]["neutral"]
            )

            for idx, filler in enumerate(fillers):
                text = filler["text"]
                description = filler["description"]

                print(f"  [{idx+1}/{len(fillers)}] Generating: '{text}' ({description})")

                # Create TTS with emotion settings
                voice_settings = VoiceSettings(
                    stability=emotion_settings["stability"],
                    similarity_boost=emotion_settings["similarity_boost"],
                    style=emotion_settings["style"],
                    use_speaker_boost=emotion_settings["use_speaker_boost"],
                )

                tts = elevenlabs.TTS(
                    api_key=settings.ELEVENLABS_API_KEY,
                    voice_id=settings.ELEVENLABS_VOICE_ID,
                    model="eleven_turbo_v2_5",
                    voice_settings=voice_settings,
                    http_session=http_session,
                )

                # Generate audio
                audio_frames = []
                sample_rate = 24000  # ElevenLabs default
                num_channels = 1

                async for audio in tts.synthesize(text):
                    audio_frames.append(audio.frame.data.tobytes())

                # Combine all frames
                audio_data = b"".join(audio_frames)

                # Save as WAV file
                filename = f"{emotion}_{idx+1}_{text.replace(' ', '_')}.wav"
                output_path = output_dir / filename

                with wave.open(str(output_path), "wb") as wav_file:
                    wav_file.setnchannels(num_channels)
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_data)

                print(f"      ✓ Saved: {filename}")

    print(f"\n{'='*60}")
    print(f"✅ All filler sounds generated successfully!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(generate_filler_sounds())
