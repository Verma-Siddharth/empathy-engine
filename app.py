"""
Empathy Engine — FastAPI Web Application
Run: uvicorn app:app --reload
"""

import os
import uuid
import base64
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from empathy_engine import run, VOICE_PROFILES

# ── App Setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="Empathy Engine", version="1.0.0")

AUDIO_DIR = Path("audio_outputs")
AUDIO_DIR.mkdir(exist_ok=True)


# ── Request / Response Models ─────────────────────────────────────────────────
class SynthesizeRequest(BaseModel):
    text: str


class SynthesizeResponse(BaseModel):
    emotion:    str
    confidence: float
    speed:      float
    pitch:      float
    audio_url:  str
    description: str


# ── API Routes ────────────────────────────────────────────────────────────────
@app.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize(req: SynthesizeRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    output_filename = f"{uuid.uuid4().hex}.wav"
    output_path     = AUDIO_DIR / output_filename

    result = run(req.text, output_file=str(output_path), verbose=False)

    return SynthesizeResponse(
        emotion=result["emotion"],
        confidence=round(result["confidence"], 3),
        speed=result["speed"],
        pitch=result["pitch"],
        audio_url=f"/audio/{output_filename}",
        description=VOICE_PROFILES[result["emotion"]]["description"],
    )


@app.get("/audio/{filename}")
async def get_audio(filename: str):
    file_path = AUDIO_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found.")
    return FileResponse(str(file_path), media_type="audio/wav")


# ── Frontend ──────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_PAGE


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Empathy Engine</title>
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;800&family=DM+Mono:ital,wght@0,400;0,500;1,400&display=swap" rel="stylesheet"/>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:        #0a0a0f;
      --surface:   #12121a;
      --border:    #1e1e2e;
      --accent:    #7c6af7;
      --accent2:   #f76a8c;
      --text:      #e8e6f0;
      --muted:     #6b6880;
      --happy:     #67e8a0;
      --sad:       #60a5fa;
      --angry:     #f87171;
      --neutral:   #a78bfa;
    }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'DM Mono', monospace;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 60px 24px 80px;
      overflow-x: hidden;
    }

    /* ── Background grain ── */
    body::before {
      content: '';
      position: fixed; inset: 0;
      background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
      pointer-events: none; z-index: 0;
    }

    .container { position: relative; z-index: 1; width: 100%; max-width: 680px; }

    /* ── Header ── */
    header { text-align: center; margin-bottom: 52px; }

    .logo-badge {
      display: inline-flex; align-items: center; gap: 8px;
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 999px; padding: 6px 16px;
      font-size: 11px; letter-spacing: 0.12em; color: var(--muted);
      text-transform: uppercase; margin-bottom: 24px;
    }
    .logo-badge span { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); animation: pulse 2s infinite; }

    @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(1.5)} }

    h1 {
      font-family: 'Syne', sans-serif; font-size: clamp(36px, 8vw, 58px);
      font-weight: 800; line-height: 1.05; letter-spacing: -0.02em;
      background: linear-gradient(135deg, var(--text) 30%, var(--accent));
      -webkit-background-clip: text; -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .subtitle { margin-top: 14px; color: var(--muted); font-size: 13px; line-height: 1.7; }

    /* ── Card ── */
    .card {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 20px; padding: 32px;
      box-shadow: 0 0 60px rgba(124, 106, 247, 0.06);
    }

    .field-label {
      font-size: 10px; letter-spacing: 0.12em; text-transform: uppercase;
      color: var(--muted); margin-bottom: 10px; display: block;
    }

    textarea {
      width: 100%; background: var(--bg); border: 1px solid var(--border);
      border-radius: 12px; color: var(--text); font-family: 'DM Mono', monospace;
      font-size: 14px; line-height: 1.7; padding: 16px; resize: vertical;
      min-height: 120px; outline: none; transition: border-color .2s;
    }
    textarea:focus { border-color: var(--accent); }
    textarea::placeholder { color: var(--muted); }

    /* ── Presets ── */
    .presets { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }

    .preset-btn {
      background: transparent; border: 1px solid var(--border);
      border-radius: 8px; color: var(--muted); font-family: 'DM Mono', monospace;
      font-size: 11px; padding: 6px 12px; cursor: pointer; transition: all .2s;
    }
    .preset-btn:hover { border-color: var(--accent); color: var(--text); }

    /* ── Submit ── */
    button.submit {
      margin-top: 20px; width: 100%;
      background: var(--accent); border: none; border-radius: 12px;
      color: #fff; font-family: 'Syne', sans-serif; font-size: 15px;
      font-weight: 600; letter-spacing: 0.02em; padding: 16px;
      cursor: pointer; transition: all .2s; position: relative; overflow: hidden;
    }
    button.submit:hover { background: #6b58e8; transform: translateY(-1px); box-shadow: 0 8px 30px rgba(124,106,247,.35); }
    button.submit:active { transform: translateY(0); }
    button.submit:disabled { opacity: .5; cursor: not-allowed; transform: none; }

    /* ── Result ── */
    .result {
      margin-top: 24px; padding: 24px; background: var(--bg);
      border: 1px solid var(--border); border-radius: 16px;
      display: none; animation: fadeUp .4s ease;
    }
    .result.visible { display: block; }

    @keyframes fadeUp { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }

    .emotion-tag {
      display: inline-flex; align-items: center; gap: 8px;
      border-radius: 999px; padding: 6px 14px; font-size: 12px;
      font-weight: 500; letter-spacing: 0.06em; text-transform: uppercase;
      margin-bottom: 20px;
    }
    .emotion-tag.happy  { background: rgba(103,232,160,.12); color: var(--happy);  border: 1px solid rgba(103,232,160,.25); }
    .emotion-tag.sad    { background: rgba(96,165,250,.12);  color: var(--sad);    border: 1px solid rgba(96,165,250,.25);  }
    .emotion-tag.angry  { background: rgba(248,113,113,.12); color: var(--angry);  border: 1px solid rgba(248,113,113,.25); }
    .emotion-tag.neutral{ background: rgba(167,139,250,.12); color: var(--neutral);border: 1px solid rgba(167,139,250,.25); }

    .params-grid {
      display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;
      margin-bottom: 20px;
    }
    .param {
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 10px; padding: 12px; text-align: center;
    }
    .param-label { font-size: 9px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); margin-bottom: 4px; display: block; }
    .param-value { font-family: 'Syne', sans-serif; font-size: 18px; font-weight: 700; color: var(--text); }

    audio {
      width: 100%; margin-top: 4px;
      filter: invert(1) hue-rotate(200deg) brightness(0.85);
      border-radius: 8px;
    }

    /* ── Error ── */
    .error-msg { color: var(--angry); font-size: 13px; margin-top: 12px; display: none; }
    .error-msg.visible { display: block; }

    /* ── Loader ── */
    .spinner {
      display: inline-block; width: 16px; height: 16px;
      border: 2px solid rgba(255,255,255,.3); border-top-color: #fff;
      border-radius: 50%; animation: spin .7s linear infinite; vertical-align: middle; margin-right: 8px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
  </style>
</head>
<body>
<div class="container">
  <header>
    <div class="logo-badge"><span></span> AI Voice System</div>
    <h1>Empathy<br/>Engine</h1>
    <p class="subtitle">Type any text. The engine reads your emotion<br/>and speaks back — the way a human would.</p>
  </header>

  <div class="card">
    <label class="field-label">Your text</label>
    <textarea id="inputText" placeholder="e.g. I just got promoted — this is the best day of my life!"></textarea>

    <div class="presets">
      <button class="preset-btn" onclick="setPreset('I just got promoted! This is absolutely incredible news, I cannot believe it!')">😄 Happy</button>
      <button class="preset-btn" onclick="setPreset('I lost my wallet and I have no idea where it is. This day has been terrible.')">😔 Sad</button>
      <button class="preset-btn" onclick="setPreset('I have been waiting for three hours and no one has helped me. This is completely unacceptable.')">😡 Angry</button>
      <button class="preset-btn" onclick="setPreset('The meeting is scheduled for Thursday at 2pm. Please confirm your attendance.')">😐 Neutral</button>
    </div>

    <button class="submit" id="submitBtn" onclick="synthesize()">
      Generate Voice
    </button>

    <p class="error-msg" id="errorMsg"></p>

    <div class="result" id="result">
      <div id="emotionTag" class="emotion-tag"></div>
      <div class="params-grid">
        <div class="param">
          <span class="param-label">Emotion</span>
          <span class="param-value" id="emotionLabel">—</span>
        </div>
        <div class="param">
          <span class="param-label">Speed</span>
          <span class="param-value" id="speedLabel">—</span>
        </div>
        <div class="param">
          <span class="param-label">Pitch</span>
          <span class="param-value" id="pitchLabel">—</span>
        </div>
      </div>
      <label class="field-label">Audio Output</label>
      <audio id="audioPlayer" controls></audio>
    </div>
  </div>
</div>

<script>
  function setPreset(text) {
    document.getElementById('inputText').value = text;
  }

  async function synthesize() {
    const text = document.getElementById('inputText').value.trim();
    const btn  = document.getElementById('submitBtn');
    const err  = document.getElementById('errorMsg');
    const res  = document.getElementById('result');

    err.classList.remove('visible');
    res.classList.remove('visible');

    if (!text) { showError('Please enter some text first.'); return; }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span>Analysing & synthesizing…';

    try {
      const response = await fetch('/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Something went wrong.');
      }

      const data = await response.json();

      // Populate result
      const tag = document.getElementById('emotionTag');
      tag.className = `emotion-tag ${data.emotion}`;
      tag.innerHTML = `<span>●</span> ${data.emotion} — ${data.description}`;

      document.getElementById('emotionLabel').textContent = data.emotion;
      document.getElementById('speedLabel').textContent   = data.speed + 'x';
      document.getElementById('pitchLabel').textContent   = (data.pitch >= 0 ? '+' : '') + data.pitch + ' st';

      const player = document.getElementById('audioPlayer');
      player.src = data.audio_url + '?t=' + Date.now();
      player.load();

      res.classList.add('visible');
    } catch (e) {
      showError(e.message);
    } finally {
      btn.disabled = false;
      btn.innerHTML = 'Generate Voice';
    }
  }

  function showError(msg) {
    const err = document.getElementById('errorMsg');
    err.textContent = msg;
    err.classList.add('visible');
  }
</script>
</body>
</html>
"""