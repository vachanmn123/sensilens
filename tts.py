import time
import os
import numpy as np
import sounddevice as sd
import soundfile as sf
from threading import Thread, Lock
from piper import PiperVoice
import wave
import queue

voice = PiperVoice.load("checkpoints/en_US-lessac-low.onnx")

sounds = {}  # Dictionary to cache sound file paths
debounce_map = {}
DEBOUNCE_INTERVAL = 5  # seconds

# Simple beep generation
SAMPLE_RATE = 44100
_beep_q = queue.Queue(maxsize=100)
_beep_worker_started = False
_lock = Lock()


def synthesize_speech(text: str) -> str:
    """Generate TTS audio file if not cached"""
    if text in sounds:
        return sounds[text]

    sound_file = f"sounds/generated/{text}.wav"
    os.makedirs(os.path.dirname(sound_file), exist_ok=True)

    if os.path.exists(sound_file):
        sounds[text] = sound_file
        return sound_file

    with wave.open(sound_file, "wb") as wf:
        voice.synthesize_wav(text, wf)

    sounds[text] = sound_file
    return sound_file


def _play_tts(text: str):
    """Simple TTS playback"""
    try:
        sound_file = synthesize_speech(text)
        if not os.path.exists(sound_file):
            print(f"Sound file {sound_file} does not exist.")
            return

        # Read and play with sounddevice (simpler than pydub)
        data, fs = sf.read(sound_file)  # You'll need: pip install soundfile
        sd.play(data, fs)
    except Exception as e:
        print(f"TTS playback error: {e}")


def play_tts(text: str):
    """Play text-to-speech with debouncing"""
    now = time.time()
    prev_call = debounce_map.get(text, 0)

    if now - prev_call > DEBOUNCE_INTERVAL:
        thread = Thread(target=_play_tts, args=(text,), daemon=True)
        thread.start()
        debounce_map[text] = now


def generate_beep(
    frequency: float, duration: float, volume: float = 0.3, pan: float = 0.0
):
    """Generate a simple sine wave beep"""
    frames = int(duration * SAMPLE_RATE)
    t = np.linspace(0, duration, frames, False)

    # Generate sine wave
    wave_data = np.sin(frequency * 2 * np.pi * t) * volume

    # Apply panning (simple stereo)
    if pan != 0.0:
        left_vol = 1.0 - max(0, pan)
        right_vol = 1.0 + min(0, pan)
        stereo = np.column_stack([wave_data * left_vol, wave_data * right_vol])
        return stereo

    return wave_data


def _beep_worker():
    """Simple beep worker thread"""
    while True:
        try:
            speed, x_dist, depth = _beep_q.get()

            # Clear queue backlog to prevent lag
            while _beep_q.qsize() > 5:
                try:
                    _beep_q.get_nowait()
                except queue.Empty:
                    break

            # Generate beep parameters
            base_freq = 800  # Hz
            duration = 0.1  # seconds

            # Adjust frequency based on speed (higher speed = higher pitch)
            frequency = base_freq + (speed - 1.0) * 200
            frequency = max(200, min(2000, frequency))  # Clamp frequency

            # Volume based on depth (closer = louder)
            volume = max(0.1, min(0.5, 0.3 * (1.0 - depth)))

            # Pan based on x distance
            pan = max(-1.0, min(1.0, x_dist / 320.0))

            # Generate and play beep
            beep_data = generate_beep(frequency, duration, volume, pan)

            # Play without blocking
            sd.play(beep_data, SAMPLE_RATE)

            # Multiple beeps for high speed
            if speed > 2.0:
                time.sleep(0.05)
                sd.play(beep_data, SAMPLE_RATE)

        except Exception as e:
            print(f"Beep worker error: {e}")
            time.sleep(0.01)  # Brief pause on error


def _ensure_beep_worker():
    """Start beep worker if not already running"""
    global _beep_worker_started
    with _lock:
        if not _beep_worker_started:
            t = Thread(target=_beep_worker, daemon=True)
            t.start()
            _beep_worker_started = True


def play_distance_beep(speed: float, x_dist: float = 0.0, depth: float = 0.0):
    """Queue a distance beep"""
    if speed < 0.1:
        return

    _ensure_beep_worker()
    try:
        _beep_q.put_nowait((speed, x_dist, depth))
    except queue.Full:
        pass  # Drop if queue is full
