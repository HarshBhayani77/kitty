import math
import array
import pygame
from PyQt6.QtCore import QThread

class SoundWorker(QThread):
    """Background worker to play synthesized cat sounds without freezing the GUI."""
    def __init__(self, sound_type: str, volume: float = 0.8):
        super().__init__()
        self.sound_type = sound_type
        self.volume = volume

    def run(self) -> None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1)
        except Exception as e:
            print(f"Failed to initialize pygame mixer: {e}")
            return

        sample_rate = 22050
        duration = 1.2 if self.sound_type == "purr" else 0.4
        num_samples = int(sample_rate * duration)
        
        samples = array.array('h', [0] * num_samples)
        
        if self.sound_type == "purr":
            # Low frequency rumble (approx 28 Hz) modulated by a 3 Hz envelope to simulate purr cycles
            for i in range(num_samples):
                t = i / sample_rate
                # 28 Hz base tone
                val = math.sin(2 * math.pi * 28 * t)
                # Breathing envelope
                env = 0.5 + 0.5 * math.sin(2 * math.pi * 3 * t)
                # Harmonics for vibration texture
                val += 0.3 * math.sin(2 * math.pi * 56 * t) * env
                val += 0.1 * math.sin(2 * math.pi * 84 * t) * env
                
                samples[i] = int(val * env * 12000 * self.volume)
        elif self.sound_type == "meow":
            # Frequency sweep from 450 Hz -> 800 Hz -> 550 Hz
            for i in range(num_samples):
                t = i / sample_rate
                if t < 0.15:
                    freq = 450 + (350 * (t / 0.15))
                else:
                    freq = 800 - (250 * ((t - 0.15) / 0.25))
                
                val = math.sin(2 * math.pi * freq * t)
                val += 0.4 * math.sin(2 * math.pi * (freq * 2) * t)  # 2nd harmonic
                val += 0.2 * math.sin(2 * math.pi * (freq * 3) * t)  # 3rd harmonic
                
                # Amplitude envelope
                if t < 0.04:
                    env = t / 0.04
                elif t > 0.3:
                    env = 1.0 - ((t - 0.3) / 0.1)
                else:
                    env = 1.0
                    
                samples[i] = int(val * env * 8000 * self.volume)
                
        try:
            sound = pygame.mixer.Sound(buffer=samples)
            sound.play()
            # Wait for sound to finish playing in background
            pygame.time.wait(int(duration * 1000))
        except Exception as e:
            print(f"Failed to play synthesized sound: {e}")

class SoundManager:
    """Manages sound effects and coordinates background playback."""
    _active_workers = []

    @staticmethod
    def play_sound(sound_type: str, volume_percent: int = 80, enabled: bool = True) -> None:
        """Asynchronously play a synthesized sound effect."""
        if not enabled:
            return
            
        volume = max(0.0, min(1.0, volume_percent / 100.0))
        worker = SoundWorker(sound_type, volume)
        SoundManager._active_workers.append(worker)
        worker.finished.connect(lambda: SoundManager._clean_worker(worker))
        worker.start()

    @staticmethod
    def _clean_worker(worker: SoundWorker) -> None:
        if worker in SoundManager._active_workers:
            SoundManager._active_workers.remove(worker)
