import numpy as np
from scipy.signal import spectrogram
from scipy.ndimage import maximum_filter

class FingerprintService:
    def __init__(self, target_sr=22050):
        self.target_sr = target_sr
        self.nperseg = 1024
        self.noverlap = 512
        
    def generate_fingerprints(self, audio_data: np.ndarray, sr: int):
        """
        Generates a list of hashes and their time offsets.
        Returns: list of (hash_string, time_offset)
        """
        # Ensure we don't process empty data
        if len(audio_data) < self.nperseg:
            return []

        # 1. Spectrogram
        f, t, Sxx = spectrogram(audio_data, fs=sr, nperseg=self.nperseg, noverlap=self.noverlap)
        
        # Convert to dB (log scale)
        # Avoid log of zero
        Sxx = 10 * np.log10(Sxx + 1e-10)
        
        # 2. Find Peaks (local maxima)
        neighborhood_size = 20 # 20 bins in time/freq
        threshold = np.percentile(Sxx, 90) # Only top 10% highest energy peaks
        
        local_max = maximum_filter(Sxx, size=neighborhood_size) == Sxx
        background = (Sxx > threshold)
        peaks_mask = np.logical_and(local_max, background)
        
        freq_idx, time_idx = np.where(peaks_mask)
        
        # Sort peaks by time
        peaks = sorted(zip(freq_idx, time_idx), key=lambda x: x[1])
        
        # 3. Create Hashes (Constellation Map)
        hashes = []
        target_zone = 5 # Look at next 5 peaks
        delay_min = 1
        delay_max = 200 # Delta time limit
        
        for i in range(len(peaks)):
            f1, t1 = peaks[i][0].item(), peaks[i][1].item()
            
            for j in range(1, target_zone + 1):
                if i + j < len(peaks):
                    f2, t2 = peaks[i + j][0].item(), peaks[i + j][1].item()
                    delta_t = t2 - t1
                    
                    if delay_min <= delta_t <= delay_max:
                        # Create a compact string hash: "f1|f2|dt"
                        hash_str = f"{f1}|{f2}|{delta_t}"
                        hashes.append((hash_str, t1))
                        
        return hashes
