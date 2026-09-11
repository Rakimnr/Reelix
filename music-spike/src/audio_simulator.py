import numpy as np

class AudioSimulator:
    def __init__(self, sr=22050):
        self.sr = sr
        
    def degrade(self, audio_data: np.ndarray, degradation: str) -> np.ndarray:
        # Create a copy so we don't modify original reference
        audio = audio_data.copy()
        
        if degradation == "CLEAN":
            return audio
            
        # 1. Volume and Noise
        if degradation in ["LIGHT", "MEDIUM", "HEAVY"]:
            if degradation == "LIGHT":
                audio = audio * 0.8
                noise_amp = 0.005
            elif degradation == "MEDIUM":
                audio = audio * 0.6
                noise_amp = 0.02
            elif degradation == "HEAVY":
                audio = audio * 0.4
                noise_amp = 0.05
                
            noise = np.random.normal(0, noise_amp, audio.shape)
            audio = audio + noise
            
        # 2. Voice Over (simulate by adding filtered/pulsing noise)
        elif degradation == "VOICE_OVER":
            audio = audio * 0.6
            # Create a pulsing noise that mimics speech rhythm (approx 3Hz)
            t = np.arange(len(audio)) / self.sr
            envelope = (np.sin(2 * np.pi * 3 * t) + 1) / 2
            voice_noise = np.random.normal(0, 0.1, audio.shape) * envelope
            audio = audio + voice_noise

        # 3. Speed Up (+5%)
        elif degradation == "SPEED_UP":
            # Resample using linear interpolation
            orig_indices = np.arange(len(audio))
            new_indices = np.arange(0, len(audio), 1.05)
            audio = np.interp(new_indices, orig_indices, audio)
            
        # 4. Slow Down (-5%)
        elif degradation == "SLOW_DOWN":
            orig_indices = np.arange(len(audio))
            new_indices = np.arange(0, len(audio), 0.95)
            audio = np.interp(new_indices, orig_indices, audio)
            
        # 5. Reverb
        elif degradation == "REVERB":
            # Simple exponential decay impulse response
            ir_length = int(self.sr * 0.3) # 300ms reverb
            ir = np.exp(-np.linspace(0, 5, ir_length)) * np.random.normal(0, 0.5, ir_length)
            # Convolve (use valid or full, then trim to original length)
            # using 'same' to keep length
            audio = np.convolve(audio, ir, mode='full')[:len(audio)]
            # Normalize to avoid clipping after convolution
            if np.max(np.abs(audio)) > 0:
                audio = audio / np.max(np.abs(audio))
            
        # Clip to valid audio range
        audio = np.clip(audio, -1.0, 1.0)
        return audio
        
    def extract_segment(self, audio_data: np.ndarray, duration_sec: float, start_sec: float = 0.0) -> np.ndarray:
        start_sample = int(start_sec * self.sr)
        end_sample = start_sample + int(duration_sec * self.sr)
        
        # Ensure we don't go out of bounds
        end_sample = min(end_sample, len(audio_data))
        
        return audio_data[start_sample:end_sample]
