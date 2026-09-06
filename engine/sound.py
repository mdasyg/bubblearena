"""
engine/sound.py - Procedural 8-bit chiptune sound effect synthesizer and dynamic BGM engine.
Synthesizes square, triangle, and noise waveforms using standard Python array buffers.
"""
import math
import struct
import array
import random
import pygame

class SoundManager:
    """Manages 8-bit arcade sound effects and chiptune background music."""
    def __init__(self, sample_rate=22050):
        self.sample_rate = sample_rate
        self.enabled = False
        self.sfx = {}
        self.bgm_playing = False
        self.fast_bgm = False
        self.bgm_track_id = 0
        self.music_channel = None

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=sample_rate, size=-16, channels=2, buffer=512)
            self.enabled = True
            self.music_channel = pygame.mixer.Channel(7)  # reserve channel 7 for BGM
            self._generate_all_sfx()
            self._generate_bgm_tracks()
        except Exception as e:
            print(f"[SoundManager] Audio initialization notice: {e}. Game continuing in silent mode without audio.")
            self.enabled = False
            self.music_channel = None
            self.sfx = {}
            self.normal_bgm = None
            self.fast_bgm_sound = None

    def _generate_tone(self, freq_list, duration, wave_type="square", volume=0.5, duty=0.5):
        """Generates a raw 16-bit stereo PCM sound buffer from frequency and duration steps."""
        if not self.enabled:
            return None
        total_samples = int(self.sample_rate * duration)
        buf = array.array('h')
        num_steps = len(freq_list)
        step_len = max(1, total_samples // num_steps)

        phase = 0.0
        import random
        for i in range(total_samples):
            step_idx = min(i // step_len, num_steps - 1)
            freq = freq_list[step_idx]
            if freq <= 0:
                val = 0
            else:
                phase_inc = (2.0 * math.pi * freq) / self.sample_rate
                phase = (phase + phase_inc) % (2.0 * math.pi)

                if wave_type == "square":
                    val = 1.0 if phase < (2.0 * math.pi * duty) else -1.0
                elif wave_type == "triangle":
                    val = 2.0 * abs(2.0 * (phase / (2.0 * math.pi) - math.floor(phase / (2.0 * math.pi) + 0.5))) - 1.0
                elif wave_type == "sawtooth":
                    val = (phase / math.pi) - 1.0
                elif wave_type == "noise":
                    val = random.uniform(-1.0, 1.0)
                else:
                    val = math.sin(phase)

            # Apply envelope (quick attack, linear decay)
            envelope = max(0.0, 1.0 - (i / total_samples))
            sample_val = int(val * envelope * volume * 32767.0)
            sample_val = max(-32767, min(32767, sample_val))
            buf.append(sample_val) # Left channel
            buf.append(sample_val) # Right channel

        return pygame.mixer.Sound(buffer=buf)

    def _generate_all_sfx(self):
        """Generates standard retro arcade sounds."""
        # 1. Bubble Shoot: rising sweep
        self.sfx["shoot"] = self._generate_tone(
            [400, 520, 680, 880, 1100], duration=0.10, wave_type="square", volume=0.35, duty=0.25
        )
        # 2. Bubble Pop: quick crunch + high burst
        self.sfx["pop"] = self._generate_tone(
            [800, 400, 200, 100], duration=0.08, wave_type="noise", volume=0.45
        )
        # 3. Player Jump: upward arpeggio
        self.sfx["jump"] = self._generate_tone(
            [220, 330, 440, 660], duration=0.12, wave_type="square", volume=0.3, duty=0.5
        )
        # 4. Bubble Bounce: springy twang
        self.sfx["bounce"] = self._generate_tone(
            [300, 550, 400, 700], duration=0.14, wave_type="triangle", volume=0.4
        )
        # 5. Trap Player: dramatic chord
        self.sfx["trap"] = self._generate_tone(
            [600, 450, 300, 200], duration=0.25, wave_type="square", volume=0.4, duty=0.75
        )
        # 6. Rescue Teammate: bright ascending fanfare
        self.sfx["rescue"] = self._generate_tone(
            [392, 523, 659, 784, 1046], duration=0.28, wave_type="square", volume=0.45, duty=0.5
        )
        # 7. Power-up Pickup: sparkly arpeggio
        self.sfx["powerup"] = self._generate_tone(
            [523, 659, 784, 1046, 1318], duration=0.22, wave_type="triangle", volume=0.4
        )
        # 8. Death / Elimination: downward pitch crunch
        self.sfx["death"] = self._generate_tone(
            [500, 380, 260, 180, 110], duration=0.35, wave_type="noise", volume=0.45
        )
        # 9. Flag Capture / Drop
        self.sfx["flag"] = self._generate_tone(
            [440, 880, 440, 880], duration=0.18, wave_type="square", volume=0.35, duty=0.5
        )
        # 10. Hurry Up Alarm: fast pulsing warning
        self.sfx["hurry"] = self._generate_tone(
            [880, 1174, 880, 1174, 880, 1174], duration=0.4, wave_type="square", volume=0.45, duty=0.25
        )
        # 11. Victory Fanfare
        self.sfx["victory"] = self._generate_tone(
            [523, 523, 523, 659, 784, 1046], duration=0.6, wave_type="square", volume=0.5, duty=0.5
        )
        # 12. Menu Click / Select
        self.sfx["select"] = self._generate_tone(
            [440, 880], duration=0.06, wave_type="triangle", volume=0.3
        )

    def _generate_bgm_tracks(self):
        """Synthesizes a catchy multi-bar retro chiptune loop."""
        if not self.enabled:
            return
        # Notes frequency map (Hz)
        N = {
            "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.00, "A4": 440.00, "B4": 493.88,
            "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46, "G5": 783.99, "A5": 880.00, "B5": 987.77,
            "C6": 1046.50,"-": 0.0
        }

        # Happy, upbeat arcade theme inspired by Bubble Bobble melodies
        lead_melody = [
            ("C5", 0.15), ("E5", 0.15), ("G5", 0.15), ("A5", 0.15),
            ("G5", 0.30), ("E5", 0.15), ("C5", 0.15),
            ("D5", 0.15), ("F5", 0.15), ("A5", 0.15), ("G5", 0.15),
            ("E5", 0.30), ("C5", 0.30),
            ("A4", 0.15), ("C5", 0.15), ("E5", 0.15), ("G5", 0.15),
            ("F5", 0.20), ("D5", 0.20), ("G4", 0.20),
            ("C5", 0.30), ("G5", 0.15), ("E5", 0.15), ("C5", 0.30),
        ]

        self.normal_bgm = self._compile_melody_track(lead_melody, tempo_factor=1.0)
        self.fast_bgm_sound = self._compile_melody_track(lead_melody, tempo_factor=1.45)

    def _compile_melody_track(self, melody_data, tempo_factor=1.0, volume=0.25):
        """Compiles a melody sequence with bassline and pulse accompaniment into a looping Sound object."""
        if not self.enabled:
            return None
        total_duration = sum(dur / tempo_factor for _, dur in melody_data)
        total_samples = int(self.sample_rate * total_duration)
        buf = array.array('h')

        # Frequency lookup table
        freq_map = {
            "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.00, "A4": 440.00, "B4": 493.88,
            "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46, "G5": 783.99, "A5": 880.00, "B5": 987.77,
            "C6": 1046.50,"-": 0.0, "G4": 392.00, "A4": 440.00
        }

        # Build list of samples
        sample_idx = 0
        lead_phase = 0.0
        bass_phase = 0.0

        for note_name, dur in melody_data:
            step_dur = dur / tempo_factor
            step_samples = int(self.sample_rate * step_dur)
            freq = freq_map.get(note_name, 0.0)
            bass_freq = (freq * 0.5) if freq > 0 else 0.0

            for s in range(step_samples):
                # Lead voice (square 25% duty)
                if freq > 0:
                    lead_phase = (lead_phase + (2.0 * math.pi * freq) / self.sample_rate) % (2.0 * math.pi)
                    lead_val = 0.6 if lead_phase < (2.0 * math.pi * 0.25) else -0.6
                else:
                    lead_val = 0.0

                # Bass voice (triangle wave)
                if bass_freq > 0:
                    bass_phase = (bass_phase + (2.0 * math.pi * bass_freq) / self.sample_rate) % (2.0 * math.pi)
                    bass_val = 0.4 * (2.0 * abs(2.0 * (bass_phase / (2.0 * math.pi) - math.floor(bass_phase / (2.0 * math.pi) + 0.5))) - 1.0)
                else:
                    bass_val = 0.0

                # Envelope for each note
                env = max(0.1, 1.0 - 0.7 * (s / step_samples))
                mixed = (lead_val * 0.7 + bass_val * 0.5) * env * volume * 32767.0
                clamped = int(max(-32767, min(32767, mixed)))
                buf.append(clamped)
                buf.append(clamped)
                sample_idx += 1

        return pygame.mixer.Sound(buffer=buf)

    def play_sfx(self, name):
        """Plays a registered sound effect by name."""
        if not self.enabled:
            return
        try:
            snd = self.sfx.get(name)
            if snd:
                snd.play()
        except Exception:
            pass

    def start_bgm(self, fast=False):
        """Starts looping the background music track."""
        if not self.enabled or not self.music_channel:
            return
        try:
            self.fast_bgm = fast
            snd = self.fast_bgm_sound if fast else self.normal_bgm
            if snd:
                self.music_channel.play(snd, loops=-1)
                self.bgm_playing = True
        except Exception:
            self.bgm_playing = False

    def set_hurry_mode(self, hurry=True):
        """Switches dynamically between normal and fast tempo BGM."""
        if not self.enabled or hurry == self.fast_bgm:
            return
        try:
            self.start_bgm(fast=hurry)
        except Exception:
            pass

    def stop_bgm(self):
        """Stops background music."""
        if not self.enabled or not self.music_channel:
            return
        try:
            self.music_channel.stop()
        except Exception:
            pass
        self.bgm_playing = False
