import warnings

import soundcard as sc
import numpy as np
from config import AUDIO_SOURCE, MODEL_SIZE, WHISPER_COMPUTE_TYPE, WHISPER_DEVICE

try:
    from soundcard.mediafoundation import SoundcardRuntimeWarning
except Exception:
    SoundcardRuntimeWarning = Warning

model = None

# soundcard installs this warning as "always" on some setups, so ignore by category.
warnings.simplefilter("ignore", SoundcardRuntimeWarning)
warnings.filterwarnings(
    "ignore",
    category=SoundcardRuntimeWarning,
    module=r"soundcard\.mediafoundation",
)


def _get_model():
    global model

    if model is None:
        print(
            f"Loading speech model ({MODEL_SIZE}) on {WHISPER_DEVICE} "
            f"with compute type {WHISPER_COMPUTE_TYPE}..."
        )
        from faster_whisper import WhisperModel

        model = WhisperModel(
            MODEL_SIZE,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE,
        )

    return model


def preload_model():
    try:
        _get_model()
    except Exception as exc:
        print(f"Speech model preload failed: {exc}")


def _get_recorder_source():
    if AUDIO_SOURCE == "microphone":
        microphone = sc.default_microphone()
        print(f"Listening from microphone: {microphone.name}")
        return microphone

    speaker = sc.default_speaker()
    try:
        loopback = sc.get_microphone(str(speaker.name), include_loopback=True)
        print(f"Listening from speaker loopback: {speaker.name}")
        return loopback
    except Exception as exc:
        print(f"Loopback capture unavailable ({exc}). Falling back to default microphone.")
        microphone = sc.default_microphone()
        print(f"Listening from microphone: {microphone.name}")
        return microphone


def listen(callback):
    recorder_source = _get_recorder_source()
    speech_model = _get_model()

    with recorder_source.recorder(samplerate=16000) as mic:
        print("Listening...")
        while True:
            data = mic.record(numframes=16000)
            audio = np.asarray(data[:, 0], dtype=np.float32)

            if audio.size == 0:
                continue

            if np.max(np.abs(audio)) < 0.01:
                continue

            try:
                segments, _ = speech_model.transcribe(audio, beam_size=1)
            except Exception as exc:
                print(f"Transcription failed: {exc}")
                continue

            for segment in segments:
                text = segment.text.strip().lower()
                if text:
                    print(f"User: {text}")
                    should_continue = callback(text)
                    if should_continue is False:
                        print("Stopping listener...")
                        return
