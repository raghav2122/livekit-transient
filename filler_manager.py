"""Filler sound manager to reduce perceived latency during LLM processing.

This module provides the FillerSoundManager class that plays emotion-appropriate
filler sounds (hmm, ah, etc.) when the LLM takes too long to respond.
"""

import asyncio
import json
import random
import wave
from pathlib import Path
from typing import Optional

from livekit import rtc


class FillerSoundManager:
    """Manages playback of filler sounds during LLM processing delays."""

    def __init__(self, filler_sounds_dir: Path, config_path: Path):
        """Initialize the filler sound manager.

        Args:
            filler_sounds_dir: Directory containing generated filler sound WAV files.
            config_path: Path to filler_sounds_config.json.
        """
        self.filler_sounds_dir = filler_sounds_dir
        self.current_emotion = "neutral"
        self.is_playing = False
        self.playback_task: Optional[asyncio.Task] = None

        # Load configuration
        with open(config_path) as f:
            config = json.load(f)
            self.trigger_threshold_ms = config["settings"]["filler_trigger_threshold_ms"]
            self.fillers_config = config["fillers"]

    def set_emotion(self, emotion: str):
        """Set the current emotion for filler sound selection.

        Args:
            emotion: Emotion name (neutral, happy, sad, angry).
        """
        if emotion in self.fillers_config:
            self.current_emotion = emotion

    def get_random_filler_path(self, emotion: Optional[str] = None) -> Path:
        """Get a random filler sound file path for the given emotion.

        Args:
            emotion: Emotion name. If None, uses current_emotion.

        Returns:
            Path to a random filler sound WAV file.
        """
        emotion = emotion or self.current_emotion
        fillers = self.fillers_config.get(emotion, self.fillers_config["neutral"])

        # Pick a random filler from the emotion category
        filler_idx = random.randint(1, len(fillers))
        filler_text = fillers[filler_idx - 1]["text"].replace(" ", "_")

        # Construct filename
        filename = f"{emotion}_{filler_idx}_{filler_text}.wav"
        return self.filler_sounds_dir / filename

    async def play_filler_sound(
        self,
        audio_source: rtc.AudioSource,
        emotion: Optional[str] = None
    ):
        """Play a filler sound through the audio source.

        Args:
            audio_source: LiveKit audio source to play the sound through.
            emotion: Emotion for the filler sound. If None, uses current_emotion.
        """
        if self.is_playing:
            return

        self.is_playing = True
        filler_path = self.get_random_filler_path(emotion)

        try:
            # Read WAV file
            with wave.open(str(filler_path), "rb") as wav_file:
                sample_rate = wav_file.getframerate()
                num_channels = wav_file.getnchannels()
                audio_data = wav_file.readframes(wav_file.getnframes())

            # Convert to AudioFrame and play
            # Note: This is a simplified version. In production, you'd stream chunks
            # and handle sample rate conversion if needed
            frame = rtc.AudioFrame(
                data=audio_data,
                sample_rate=sample_rate,
                num_channels=num_channels,
                samples_per_channel=len(audio_data) // (num_channels * 2),  # 16-bit = 2 bytes
            )

            await audio_source.capture_frame(frame)

        except Exception as e:
            print(f"Error playing filler sound: {e}")
        finally:
            self.is_playing = False

    async def trigger_filler_on_delay(
        self,
        audio_source: rtc.AudioSource,
        delay_ms: Optional[int] = None,
        emotion: Optional[str] = None
    ):
        """Trigger filler sound playback after a delay if LLM hasn't responded.

        Args:
            audio_source: LiveKit audio source to play through.
            delay_ms: Delay in milliseconds before playing filler.
                      If None, uses trigger_threshold_ms from config.
            emotion: Emotion for the filler sound.
        """
        delay_ms = delay_ms or self.trigger_threshold_ms
        delay_seconds = delay_ms / 1000.0

        try:
            # Wait for the threshold
            await asyncio.sleep(delay_seconds)

            # If still no response, play filler
            if not self.is_playing:
                await self.play_filler_sound(audio_source, emotion)

        except asyncio.CancelledError:
            # LLM responded before threshold, cancel filler
            pass

    def start_filler_timer(
        self,
        audio_source: rtc.AudioSource,
        emotion: Optional[str] = None
    ) -> asyncio.Task:
        """Start a timer that will play a filler sound if LLM takes too long.

        Args:
            audio_source: LiveKit audio source to play through.
            emotion: Emotion for the filler sound.

        Returns:
            Asyncio task that can be cancelled when LLM responds.
        """
        if self.playback_task and not self.playback_task.done():
            self.playback_task.cancel()

        self.playback_task = asyncio.create_task(
            self.trigger_filler_on_delay(audio_source, emotion=emotion)
        )
        return self.playback_task

    def cancel_filler(self):
        """Cancel any pending filler sound playback."""
        if self.playback_task and not self.playback_task.done():
            self.playback_task.cancel()
            self.playback_task = None
