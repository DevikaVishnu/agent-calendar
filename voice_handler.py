import openai
import os
import platform
import subprocess
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
# Initialize OpenAI client
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY is None:
    raise RuntimeError("OPENAI_API_KEY env var not set")
client = openai.OpenAI(api_key=OPENAI_API_KEY)


def transcribe_audio(audio_file_path):
    """
    Convert speech to text using Whisper
    
    Args:
        audio_file_path: Path to audio file (wav, mp3, etc.)
    
    Returns:
        Transcribed text
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"  # Optional: specify language
            )
        return transcript.text
    except Exception as e:
        print(f"❌ Transcription error: {e}")
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
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        response.stream_to_file(output_file)
        return output_file
    
    except Exception as e:
        print(f"❌ TTS error: {e}")
        return None

def play_audio(audio_file):
    """
    Play audio file using system default player
    
    Args:
        audio_file: Path to audio file
    """
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            subprocess.run(["afplay", audio_file], check=True)
        elif system == "Linux":
            subprocess.run(["aplay", audio_file], check=True)
        elif system == "Windows":
            subprocess.run(["start", audio_file], shell=True, check=True)
        else:
            print(f"⚠️  Can't auto-play on {system}. File saved at: {audio_file}")
    
    except Exception as e:
        print(f"❌ Error playing audio: {e}")
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