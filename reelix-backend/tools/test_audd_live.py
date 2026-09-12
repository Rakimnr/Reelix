import os
import sys
import argparse
import time

# Add the parent directory to the path so we can import from the backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from providers.audd_music_provider import AudDMusicProvider

def main():
    parser = argparse.ArgumentParser(description="Live smoke test for AudDMusicProvider.")
    parser.add_argument("audio_file", help="Path to local WAV/MP3 file")
    args = parser.parse_args()

    audio_path = args.audio_file

    print("AudD live test")
    print("-------------")

    if not os.path.exists(audio_path):
        print(f"Error: File '{audio_path}' does not exist.")
        sys.exit(1)

    file_size = os.path.getsize(audio_path)
    print(f"File: {os.path.basename(audio_path)}")
    print(f"Size: {file_size / 1024:.2f} KB")

    if file_size == 0:
        print("Error: File is empty.")
        sys.exit(1)

    # Force enable for this isolated test
    config.AUDD_ENABLED = True
    
    # Optional: check if token is provided via env
    token = os.environ.get("AUDD_API_TOKEN")
    if not token:
        print("Note: AUDD_API_TOKEN not found in environment.")
        print("You can use the test token by setting: set AUDD_API_TOKEN=test")
        sys.exit(1)
        
    config.AUDD_API_TOKEN = token
    provider = AudDMusicProvider()
    
    start_time = time.time()
    try:
        # provider.recognize will catch HTTP errors, but if we want to print real audD errors 
        # we have to rely on what AudDMusicProvider logs/returns, or we can just let it run.
        result = provider.recognize(audio_path)
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        print("\nResult:")
        print(f"state: {result.state}")
        if result.state == "MATCH":
            print(f"title: {result.track}")
            print(f"artist: {result.artist}")
            print(f"album: {result.album}")
        print(f"provider: {result.provider}")
        print(f"elapsed_ms: {elapsed_ms}")
        
    except Exception as e:
        print(f"\nUnhandled Error: {type(e).__name__} - {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
