import openai
import os
import platform
import subprocess
from dotenv import load_dotenv
from pathlib import Path
from logger_config import get_logger

logger = get_logger(__name__)

load_dotenv()
# Initialize OpenAI client
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY is None:
    logger.critical("OPENAI_API_KEY not found in environment variables!")
    raise RuntimeError("OPENAI_API_KEY env var not set")
logger.debug("OpenAI API key loaded successfully")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def transcribe_audio(audio_file_path):
    """
    Convert speech to text using Whisper
    
    Args:
        audio_file_path: Path to audio file (wav, mp3, etc.)
    
    Returns:
        Transcribed text
    """
    logger.info(f"Transcribing audio file: {audio_file_path}")
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"  # Optional: specify language
            )
        logger.info(f"Transcription successful: '{transcript.text}'")
        return transcript.text
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}", exc_info=True)
        return None

def text_to_speech(text, output_file="response.mp3", voice="alloy"):
    """
    Convert text to speech using OpenAI TTS
    
    Args:
        text: Text to convert to speech
        output_file: Where to save the audio file
        voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
    
    Returns:
        Path to the generated audio file
    """
    logger.info(f"Generating speech for text (length: {len(text)} chars)")
    logger.debug(f"Text to speak: '{text}'")
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        response.stream_to_file(output_file)
        logger.info(f"Speech generated successfully: {output_file}")
        return output_file
    
    except Exception as e:
        logger.error(f"TTS generation failed: {str(e)}", exc_info=True)
        return None

def play_audio(audio_file):
    """
    Play audio file using system default player
    
    Args:
        audio_file: Path to audio file
    """
    logger.info(f"Playing audio file: {audio_file}")
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            subprocess.run(["afplay", audio_file], check=True)
        elif system == "Linux":
            subprocess.run(["aplay", audio_file], check=True)
        elif system == "Windows":
            subprocess.run(["start", audio_file], shell=True, check=True)
        else:
            logger.warning(f"Unknown system: {system}, cannot auto-play")
            print(f"⚠️  Can't auto-play on {system}. File saved at: {audio_file}")
        logger.info("Audio playback completed")

    except Exception as e:
        logger.error(f"Audio playback failed: {str(e)}", exc_info=True)
        print(f"Audio saved at: {audio_file}")

# Test functions
if __name__ == '__main__':
    print("🎤 Testing voice handler...\n")
    
    # Test TTS
    print("1. Testing text-to-speech...")
    test_text = "Hello! I am your voice calendar assistant. I can help you manage your schedule."
    audio_file = text_to_speech(test_text, "test_tts.mp3")
    
    if audio_file:
        print(f"   ✅ Generated audio: {audio_file}")
        print("   🔊 Playing audio...")
        play_audio(audio_file)
    
    print("\n2. To test speech-to-text, record a short audio file and run:")
    print("   python voice_handler.py <audio_file.mp3>")