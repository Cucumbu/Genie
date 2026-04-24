import soundcard as sc
import numpy as np
from config import MODEL_SIZE

model = None


def _get_model():
    global model

    if model is None:
        print(f"Loading speech model ({MODEL_SIZE})...")
        from faster_whisper import WhisperModel

        model = WhisperModel(MODEL_SIZE, compute_type="int8")

    return model


def preload_model():
    try:
        _get_model()
    except Exception as exc:
        print(f"Speech model preload failed: {exc}")

def listen(callback):
    speaker = sc.default_speaker()
    speech_model = _get_model()

    with speaker.recorder(samplerate=16000) as mic:
        print("Listening...")
        while True:
            data = mic.record(numframes=16000)
            audio = np.array(data[:,0])
            segments, _ = speech_model.transcribe(audio, beam_size=1)
            for segment in segments:
                text = segment.text.strip().lower()
                if text:
                    print(f"User: {text}")
                    should_continue = callback(text)
                    if should_continue is False:
                        print("Stopping listener...")
                        return