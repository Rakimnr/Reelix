import os
import shutil
import subprocess
import scipy.io.wavfile as wavfile
import numpy as np

class AudioExtractor:
    def __init__(self):
        self.ffmpeg_path = shutil.which('ffmpeg')
        if not self.ffmpeg_path:
            winget_path = r"C:\Users\USER\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"
            if os.path.exists(winget_path):
                self.ffmpeg_path = winget_path
        
    def extract_audio(self, input_path: str, output_path: str) -> str:
        """
        Extracts/resamples audio to a standard format (WAV, 22050Hz, Mono)
        so it can be reliably fingerprinted.
        """
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
        # Standardize everything to mono 22050Hz WAV
        target_sr = 22050
        
        # If no ffmpeg and it's already a wav, try to load it natively
        if not self.ffmpeg_path:
            if input_path.lower().endswith('.wav'):
                print(f"Warning: FFmpeg not found, but input is .wav. Attempting direct load...")
                sr, data = wavfile.read(input_path)
                if len(data.shape) > 1:
                    data = data.mean(axis=1).astype(data.dtype) # mono
                # Not resampling to 22050 here to keep it simple without librosa. 
                # Scipy doesn't have an easy resampler unless we use scipy.signal.resample
                wavfile.write(output_path, sr, data)
                return output_path
            else:
                raise RuntimeError(
                    f"FFmpeg is not installed or not in PATH. Cannot process {input_path}. "
                    "Please provide .wav files, or install FFmpeg."
                )
                
        # Use ffmpeg
        cmd = [
            self.ffmpeg_path,
            "-y", "-i", input_path,
            "-ac", "1",           # mono
            "-ar", str(target_sr),# 22050 Hz
            "-vn",                # no video
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return output_path
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg failed to extract audio from {input_path}") from e

    def load_audio(self, wav_path: str):
        sr, data = wavfile.read(wav_path)
        # normalize to float -1 to 1
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
        return sr, data
