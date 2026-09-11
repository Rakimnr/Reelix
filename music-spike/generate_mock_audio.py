import os
import numpy as np
from scipy.io import wavfile

def generate_tone(freqs, duration, sr=22050):
    t = np.linspace(0, duration, int(sr * duration), False)
    wave = np.zeros_like(t)
    for f in freqs:
        wave += np.sin(2 * np.pi * f * t)
    # add some noise
    wave += np.random.normal(0, 0.1, wave.shape)
    wave = wave / np.max(np.abs(wave))
    return (wave * 32767).astype(np.int16)

def main():
    sr = 22050
    # Ref 1: Song A (Chord progression)
    songA = generate_tone([440, 554, 659], 20) # A major
    wavfile.write("references/songA.wav", sr, songA)
    wavfile.write("queries/known/songA_test.wav", sr, songA)

    # Ref 2: Song B
    songB = generate_tone([523.25, 659.25, 783.99], 20) # C major
    wavfile.write("references/songB.wav", sr, songB)
    wavfile.write("queries/known/songB_test.wav", sr, songB)

    # Ref 3: Song C
    songC = generate_tone([392, 493.88, 587.33], 20) # G major
    wavfile.write("references/songC.wav", sr, songC)
    wavfile.write("queries/known/songC_test.wav", sr, songC)

    # Unknown: Song D
    songD = generate_tone([349.23, 440, 523.25], 20) # F major
    wavfile.write("queries/unknown/songD_test.wav", sr, songD)
    
    print("Mock audio files generated.")

if __name__ == "__main__":
    main()
