"""Test script for TTS adapter"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import tts_adapter

def test_tts():
    print("🧪 Testing TTS Adapter...")
    
    # Check health
    print("\n1. Checking TTS providers health:")
    health = tts_adapter.health_check()
    print(f"Current provider: {health['current_provider']}")
    print(f"Providers: {health['providers']}")
    
    # Test audio generation
    print("\n2. Testing audio generation:")
    test_text = "Hello, this is a test of the VibeVoice TTS system with automatic ElevenLabs fallback."
    
    audio_path = tts_adapter.generate_audio(
        text=test_text,
        filename_prefix="test_audio",
        format="wav"
    )
    
    if audio_path:
        print(f"✅ Audio generated successfully: {audio_path}")
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            print(f"   File size: {file_size} bytes")
    else:
        print("❌ Audio generation failed")
    
    # Test provider switching
    print("\n3. Testing provider switching:")
    print(f"Current: {tts_adapter.get_current_provider()}")
    
    tts_adapter.set_provider('elevenlabs')
    print(f"After switch: {tts_adapter.get_current_provider()}")
    
    tts_adapter.set_provider('vibevoice')
    print(f"Back to: {tts_adapter.get_current_provider()}")

if __name__ == '__main__':
    test_tts()
