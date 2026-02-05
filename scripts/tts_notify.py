#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "openai",
#   "python-dotenv",
#   "sounddevice",
#   "soundfile",
# ]
# ///

"""
Simple TTS notification utility extracted from voice_to_claude_code.py
Uses OpenAI TTS to speak notifications aloud.

Usage:
    ./tts_notify.py "Your notification message here"

Or import as a module:
    from tts_notify import speak_notification
    speak_notification("Task complete!")
"""

import os
import sys
import tempfile
import sounddevice as sd
import soundfile as sf
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TTS_VOICE = os.getenv("TTS_VOICE", "nova")  # Options: alloy, echo, fable, onyx, nova, shimmer
TTS_SPEED = float(os.getenv("TTS_SPEED", "1.1"))  # Slightly faster for notifications

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def speak_notification(text: str, voice: str = None, speed: float = None):
    """
    Convert text to speech and play it immediately.

    Args:
        text: The text to speak
        voice: Voice to use (default: nova)
        speed: Speech speed 0.25-4.0 (default: 1.1)
    """
    if not text or not text.strip():
        return

    voice = voice or TTS_VOICE
    speed = speed or TTS_SPEED

    try:
        print(f"🔊 Speaking: {text}")

        # Generate speech
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            speed=speed,
        )

        # Create temporary file and write audio data
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_filename = temp_file.name
            temp_file.write(response.content)

        # Play audio
        data, samplerate = sf.read(temp_filename)
        sd.play(data, samplerate)
        sd.wait()

        # Clean up
        os.unlink(temp_filename)

        print("✅ Notification spoken")

    except Exception as e:
        print(f"❌ Error in TTS: {str(e)}")
        print(f"📝 Fallback text: {text}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tts_notify.py <message>")
        print("Example: python tts_notify.py 'Task completed successfully'")
        sys.exit(1)

    message = " ".join(sys.argv[1:])
    speak_notification(message)
