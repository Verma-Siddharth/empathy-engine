# 🎙 Empathy Engine

> *Dynamically modulated Text-to-Speech that speaks the way humans feel.*

The Empathy Engine is an AI-powered voice synthesis service that detects the emotional tone of input text and programmatically adjusts vocal characteristics — speed, pitch — to produce speech that genuinely reflects the emotion behind the words.

---

## ✨ Features

| Feature | Detail |
|---|---|
| **Emotion Detection** | Uses `j-hartmann/emotion-english-distilroberta-base` (HuggingFace) — classifies into 7 emotions mapped to 4 voice buckets |
| **Intensity Scaling** | Higher confidence scores produce stronger vocal modulation — *"good news"* vs *"BEST NEWS EVER"* sound different |
| **Voice Modulation** | Speed (rate) and Pitch (semitones) adjusted via `pydub` post-processing |
| **Web Interface** | FastAPI backend + single-page UI with preset buttons and embedded audio player |
| **CLI Mode** | Run directly from terminal without a browser |
| **Graceful Fallback** | Falls back to VADER sentiment if `transformers` is unavailable |

---

## 🧠 Emotion → Voice Mapping

| Detected Emotion | Speed | Pitch | Rationale |
|---|---|---|---|
| **Happy** (joy, surprise) | +20% faster | +4 semitones | Energy and warmth; mirrors how excited humans raise their voice |
| **Sad** (sadness, fear) | -20% slower | -3 semitones | Heaviness and resignation; slow pace signals low energy |
| **Angry** (anger, disgust) | +10% faster | +2 semitones | Tension and urgency; clipped delivery feels confrontational |
| **Neutral** | Baseline | Baseline | Clear, measured, professional |

### Intensity Scaling

All parameters are scaled linearly by the model's confidence score:

```
final_speed_delta = (profile_speed - 1.0) × confidence
final_pitch       = profile_pitch × confidence
```

So `"I'm happy"` (60% confidence) gets a smaller pitch boost than `"I'm absolutely ecstatic!!!"` (95% confidence).

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.9+
- `ffmpeg` installed on your system (required by `pydub`)
  - macOS: `brew install ffmpeg`
  - Ubuntu: `sudo apt install ffmpeg`
  - Windows: [Download from ffmpeg.org](https://ffmpeg.org/download.html)

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/empathy-engine.git
cd empathy-engine
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ First run will download the HuggingFace model (~300MB). This is cached after the first download.

---

## ▶️ Running the App

### Option A — Web Interface (Recommended)

```bash
uvicorn app:app --reload
```

Then open **http://localhost:8000** in your browser.

You'll see a text input, preset buttons for each emotion, and an embedded audio player that plays the result instantly.

### Option B — CLI

```bash
python empathy_engine.py "I just got promoted — this is the best day of my life!"
```

Output:

```
🎙  Empathy Engine
────────────────────────────────────────
📝  Input   : I just got promoted — this is the best day of my life!
💡  Emotion  : HAPPY (confidence: 97%)
🔊  Voice    : Upbeat, energetic, warm
⚙️   Speed    : 1.194x  |  Pitch: +3.9 semitones
✅  Saved to : output.wav
```

Custom output path:

```bash
python empathy_engine.py "I lost everything." --out sad_output.wav
```

---

## 🗂️ Project Structure

```
empathy-engine/
├── empathy_engine.py   # Core pipeline: emotion detection + TTS + modulation
├── app.py              # FastAPI web app + frontend HTML
├── requirements.txt    # Python dependencies
├── audio_outputs/      # Generated audio files (auto-created)
└── README.md
```

---

## 🔌 API Reference

### `POST /synthesize`

**Request body:**
```json
{ "text": "This is the worst experience I've ever had." }
```

**Response:**
```json
{
  "emotion":     "angry",
  "confidence":  0.91,
  "speed":       1.091,
  "pitch":       1.82,
  "audio_url":   "/audio/abc123.wav",
  "description": "Tense, clipped, sharp"
}
```

### `GET /audio/{filename}`
Returns the generated `.wav` file for playback or download.

---

## 🧪 Test Sentences by Emotion

| Emotion | Example |
|---|---|
| Happy | *"I just got promoted! This is absolutely incredible!"* |
| Sad | *"I lost my dog today. I don't know what to do."* |
| Angry | *"I've been on hold for 2 hours. This is completely unacceptable."* |
| Neutral | *"The meeting is scheduled for Thursday at 2pm."* |

---

## 🛠️ Design Decisions

1. **Why `j-hartmann/emotion-english-distilroberta-base` over TextBlob/VADER?**  
   VADER only returns positive/negative/neutral polarity. The HuggingFace model classifies into 7 nuanced emotions (joy, anger, sadness, fear, surprise, disgust, neutral), enabling much more precise voice mapping. It's also fine-tuned specifically for emotion — not just sentiment.

2. **Why `pydub` for modulation instead of SSML?**  
   SSML (Speech Synthesis Markup Language) gives limited, platform-dependent control. `pydub`'s frame-rate trick for pitch shifting works offline, is reproducible, and gives us continuous numerical control tied directly to the model confidence score.

3. **Why intensity scaling?**  
   A flat mapping (happy = always +4 semitones) ignores the *degree* of emotion. Scaling by confidence means weakly emotional text gets subtle changes while strongly emotional text gets full modulation — much closer to how humans naturally modulate their voice.

4. **Why FastAPI over Flask?**  
   Async-native, automatic OpenAPI docs at `/docs`, Pydantic validation, and significantly faster for I/O-bound tasks like audio file serving.

---

## 📄 License

MIT License — free to use, modify, and distribute.