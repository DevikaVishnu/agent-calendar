import pyaudio
import wave
import os
import select
import sys
from datetime import datetime
from agent import chat_with_agent
from voice_handler import transcribe_audio, text_to_speech, play_audio
from logger_config import get_logger

logger = get_logger(__name__)
# Audio recording settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS_MAX = 10

def record_audio(output_file="input.wav"):
    """
    Record audio from microphone
    Press Enter to start, Enter again to stop
    
    Returns:
        Path to recorded audio file
    """
    print("\n🎤 Press ENTER to start recording...")
    input()
    
    audio = pyaudio.PyAudio()
    
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    
    print("🔴 Recording... (Press ENTER to stop)")
    
    frames = []
    
    # Record until Enter is pressed
    # This is a simple approach - for production you'd use threading
    
    recording = True
    while recording:
        data = stream.read(CHUNK)
        frames.append(data)
        
        # Check if Enter was pressed (Unix/Mac only)
        if sys.platform != "win32":
            if select.select([sys.stdin], [], [], 0.0)[0]:
                input()  # Clear the input buffer
                recording = False
        # On Windows, we'll just record for a fixed time
        elif len(frames) > RATE / CHUNK * RECORD_SECONDS_MAX:
            recording = False
    
    print("⏹️  Recording stopped")
    
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    # Save the audio file
    wf = wave.open(output_file, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    return output_file

def voice_interaction():
    """
    Complete voice interaction loop:
    1. Record user speech
    2. Transcribe to text
    3. Process with agent
    4. Convert response to speech
    5. Play audio response
    """
    logger.info("Starting voice interaction")
    
    print("\n" + "="*50)
    print("🗓️  VOICE CALENDAR AGENT")
    print("="*50)
    print("\nExamples:")
    print("  • 'What's on my calendar today?'")
    print("  • 'Schedule lunch with Sarah tomorrow at noon'")
    print("  • 'Add a dentist appointment next Monday at 2pm'")
    print("\n" + "="*50)
    
    # Step 1: Record audio
    audio_file = record_audio("user_input.wav")
    
    # Step 2: Transcribe
    print("\n🔄 Transcribing your speech...")
    user_text = transcribe_audio(audio_file)
    
    if not user_text:
        print("❌ Could not understand audio. Please try again.")
        return
    
    print(f"✅ You said: \"{user_text}\"")
    
    # Step 3: Process with agent
    print("\n🤔 Processing your request...")
    try:
        response_text = chat_with_agent(user_text)
        print(f"\n📝 Agent response: {response_text}")
    except Exception as e:
        print(f"❌ Error processing request: {e}")
        return
    
    # Step 4: Convert response to speech
    print("\n🔊 Generating voice response...")
    audio_response = text_to_speech(response_text, "agent_response.mp3")
    
    if not audio_response:
        print("❌ Could not generate speech")
        return
    
    # Step 5: Play response
    print("🔊 Playing response...")
    play_audio(audio_response)
    
    print("\n✅ Done!")

def main():
    """Main loop"""
    print("\n🎙️  Voice Calendar Agent")
    print("=" * 50)
    
    while True:
        choice = input("\n[V]oice command or [T]ext command or [Q]uit? ").strip().upper()
        
        if choice == 'Q':
            print("Goodbye! 👋")
            break
        
        elif choice == 'V':
            try:
                voice_interaction()
            except KeyboardInterrupt:
                print("\n\nInterrupted!")
                continue
            except Exception as e:
                print(f"\n❌ Error: {e}")
                continue
        
        elif choice == 'T':
            # Text fallback mode
            user_input = input("\nYou: ").strip()
            if user_input:
                try:
                    response = chat_with_agent(user_input)
                    print(f"\nAgent: {response}")
                    
                    # Optional: speak the response
                    speak = input("\nSpeak response? (y/n): ").strip().lower()
                    if speak == 'y':
                        audio_file = text_to_speech(response)
                        if audio_file:
                            play_audio(audio_file)
                
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        else:
            print("Invalid choice. Please enter V, T, or Q.")

if __name__ == '__main__':
    main()