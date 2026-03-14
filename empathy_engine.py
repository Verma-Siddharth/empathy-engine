"""
Empathy Engine — Core Script
Detects emotion from text and generates modulated speech audio.
"""

import os
import sys
import argparse
from pathlib import Path

# ── Emotion Detection ────────────────────────────────────────────────────────
def detect_emotion(text: str) -> tuple[str, float]:
    """
    Returns (emotion_label, confidence_score).
    Uses HuggingFace's fine-tuned emotion model.
    Falls back to VADER if transformers is unavailable.
    """
    try:
        from transformers import pipeline
        classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=1
        )
        result = classifier(text)[0][0]
        label = result["label"].lower()   # joy, sadness, anger, fear, surprise, disgust, neutral
        score = result["score"]

        # Normalise to our 4 core buckets
        mapping = {
            "joy":      "happy",
            "surprise": "happy",
            "sadness":  "sad",
            "fear":     "sad",
            "anger":    "angry",
            "disgust":  "angry",
            "neutral":  "neutral",
        }
        return mapping.get(label, "neutral"), score

    except ImportError:
        # Fallback: VADER
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()
        scores = analyzer.polarity_scores(text)
        compound = scores["compound"]
        if compound >= 0.35:
            return "happy", abs(compound)
        elif compound <= -0.35:
            return "sad", abs(compound)
        else:
            return "neutral", 1 - abs(compound)


# ── Emotion → Voice Parameter Mapping ────────────────────────────────────────
VOICE_PROFILES = {
    "happy": {
        "speed_factor":  1.20,   # 20% faster
        "pitch_semitones": 4,    # higher pitch
        "description": "Upbeat, energetic, warm"
    },
    "sad": {
        "speed_factor":  0.80,   # 20% slower
        "pitch_semitones": -3,   # lower pitch
        "description": "Slow, heavy, subdued"
    },
    "angry": {
        "speed_factor":  1.10,   # slightly faster
        "pitch_semitones": 2,    # slightly higher
        "description": "Tense, clipped, sharp"
    },
    "neutral": {
        "speed_factor":  1.00,
        "pitch_semitones": 0,
        "description": "Calm, measured, baseline"
    },
}

def scale_parameters(profile: dict, intensity: float) -> dict:
    """
    Scales vocal modulation based on emotion intensity (0–1).
    e.g. low-confidence happy → subtle changes; high-confidence happy → strong changes.
    """
    baseline_speed = 1.0
    speed_delta = (profile["speed_factor"] - baseline_speed) * intensity
    pitch_delta  = profile["pitch_semitones"] * intensity

    return {
        "speed_factor":    round(baseline_speed + speed_delta, 3),
        "pitch_semitones": round(pitch_delta, 2),
        "description":     profile["description"],
    }


# ── Text-to-Speech ────────────────────────────────────────────────────────────
def synthesize_speech(text: str, output_path: str = "raw_speech.mp3") -> str:
    """Generates raw TTS audio using gTTS. Returns path to file."""
    from gtts import gTTS
    tts = gTTS(text=text, lang="en", slow=False)
    tts.save(output_path)
    return output_path


# ── Audio Modulation ──────────────────────────────────────────────────────────
def modulate_audio(
    input_path: str,
    output_path: str,
    speed_factor: float,
    pitch_semitones: float
) -> str:
    """
    Applies speed and pitch modulation to an audio file using pydub.
    Speed change: stretch/compress the audio.
    Pitch shift: shift frequency via frame-rate manipulation.
    Returns path to modulated file.
    """
    from pydub import AudioSegment
    import numpy as np

    audio = AudioSegment.from_file(input_path)

    # ── Pitch Shift via frame rate trick ──────────────────────────────────────
    if pitch_semitones != 0:
        semitone_ratio = 2 ** (pitch_semitones / 12.0)
        new_frame_rate = int(audio.frame_rate * semitone_ratio)
        audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_frame_rate})
        audio = audio.set_frame_rate(44100)

    # ── Speed Change ──────────────────────────────────────────────────────────
    if speed_factor != 1.0:
        new_frame_rate = int(audio.frame_rate * speed_factor)
        audio = audio._spawn(audio.raw_data, overrides={"frame_rate": new_frame_rate})
        audio = audio.set_frame_rate(44100)

    audio.export(output_path, format="wav")
    return output_path


# ── Main Pipeline ─────────────────────────────────────────────────────────────
def run(text: str, output_file: str = "output.wav", verbose: bool = True) -> dict:
    """
    Full pipeline: text → emotion → modulated audio.
    Returns a result dict with emotion, parameters, and output path.
    """
    if verbose:
        print(f"\n🎙  Empathy Engine")
        print(f"{'─'*40}")
        print(f"📝  Input   : {text[:80]}{'...' if len(text)>80 else ''}")

    # Step 1: Detect emotion
    emotion, confidence = detect_emotion(text)
    profile  = VOICE_PROFILES[emotion]
    params   = scale_parameters(profile, confidence)

    if verbose:
        print(f"💡  Emotion  : {emotion.upper()} (confidence: {confidence:.0%})")
        print(f"🔊  Voice    : {profile['description']}")
        print(f"⚙️   Speed    : {params['speed_factor']}x  |  Pitch: {params['pitch_semitones']:+.1f} semitones")

    # Step 2: Synthesize raw speech
    raw_path = "raw_speech.mp3"
    synthesize_speech(text, raw_path)

    # Step 3: Modulate audio
    modulate_audio(
        input_path=raw_path,
        output_path=output_file,
        speed_factor=params["speed_factor"],
        pitch_semitones=params["pitch_semitones"],
    )

    # Cleanup
    if os.path.exists(raw_path):
        os.remove(raw_path)

    if verbose:
        print(f"✅  Saved to : {output_file}")

    return {
        "emotion":    emotion,
        "confidence": confidence,
        "speed":      params["speed_factor"],
        "pitch":      params["pitch_semitones"],
        "output":     output_file,
    }


# ── CLI Entry Point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Empathy Engine — Emotionally-aware TTS")
    parser.add_argument("text",   type=str, help="Text to synthesize")
    parser.add_argument("--out",  type=str, default="output.wav", help="Output audio file path")
    args = parser.parse_args()

    run(args.text, output_file=args.out)