#!/usr/bin/env python3
"""Build vocab-player.html with embedded base64 audio and vocab data.

Embeds 4 audio sets per letter:
  LETTER_AUDIO — letter name only (e.g. "A")
  WORD_AUDIO   — word only (e.g. "adventure")
  SENT_AUDIO   — sentence only (e.g. "I read a book...")
  AUDIO_BASE64 — legacy combined (kept for compat)
"""

import base64, json, os, re
from docx import Document

DOCX_PATH = "/Users/charlesever/Downloads/单词表.docx"
AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")
OUT_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vocab-player.html")

def extract_items():
    doc = Document(DOCX_PATH)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    items = []
    for i, p in enumerate(paragraphs):
        m = re.match(r'^([A-Z])\s{2,}(\w+)$', p)
        if not m:
            continue
        letter = m.group(1)
        word = m.group(2)
        raw_sentence = paragraphs[i + 1] if i + 1 < len(paragraphs) else ""
        sentence = re.sub(r'[一-鿿]+.*', '', raw_sentence).strip()
        sentence = sentence.rstrip(' ，。、；：！？0123456789 ').strip()
        cn_sentence = paragraphs[i + 2] if i + 2 < len(paragraphs) else ""
        if cn_sentence and not any('一' <= c <= '鿿' for c in cn_sentence):
            cn_sentence = paragraphs[i + 3] if i + 3 < len(paragraphs) else ""
        cn_sentence = cn_sentence.strip()
        if sentence:
            items.append({"letter": letter, "word": word, "sentence": sentence, "cn_sentence": cn_sentence})
    return items

def load_audio_map(prefix):
    """Load base64 for files matching prefix + letter + .mp3 (e.g. 'word_' -> word_A.mp3)."""
    audio_map = {}
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        fpath = os.path.join(AUDIO_DIR, f"{prefix}{letter}.mp3")
        if os.path.exists(fpath) and os.path.getsize(fpath) > 0:
            with open(fpath, 'rb') as f:
                audio_map[letter] = base64.b64encode(f.read()).decode('ascii')
        else:
            print(f"WARNING: {fpath} missing or empty")
    return audio_map

def build_html(items, letter_map, word_map, sent_map, combined_map):
    vocab_json = json.dumps(items, ensure_ascii=False)
    letter_json = json.dumps(letter_map, ensure_ascii=False)
    word_json = json.dumps(word_map, ensure_ascii=False)
    sent_json = json.dumps(sent_map, ensure_ascii=False)
    combined_json = json.dumps(combined_map, ensure_ascii=False)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>Part 3 Word Challenge — Vocab Player</title>
<style>
  :root {{
    --blue: #4285f4; --green: #34a853; --orange: #f59e0b; --bg: #f0f4f8; --card: #ffffff;
    --text: #2d3748; --text-light: #718096; --shadow: 0 4px 20px rgba(0,0,0,.08);
    --radius: 16px;
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    font-family: -apple-system, "Microsoft YaHei", sans-serif;
    background: var(--bg); color: var(--text); min-height:100vh; overflow-x:hidden;
  }}
  .header {{
    background: white; padding: 12px 24px; display:flex; align-items:center;
    justify-content:space-between; box-shadow:0 2px 10px rgba(0,0,0,.06);
    position:sticky; top:0; z-index:100;
  }}
  .header-title {{ font-size:1.1em; font-weight:700; color:var(--blue); }}
  .header-title span {{ color:var(--text-light); font-weight:400; font-size:.85em; }}

  .main {{ max-width:600px; margin:0 auto; padding:24px 16px 60px; }}

  /* Mode tabs */
  .mode-tabs {{
    display:flex; gap:0; margin-bottom:20px; background:white; border-radius:50px;
    box-shadow:var(--shadow); overflow:hidden; padding:4px;
  }}
  .mode-tab {{
    flex:1; padding:12px 8px; border:none; background:transparent;
    font-size:1em; font-weight:700; cursor:pointer; transition:all .25s;
    border-radius:50px; color:var(--text-light); font-family:inherit;
    -webkit-tap-highlight-color:transparent;
  }}
  .mode-tab.active {{
    background:var(--blue); color:white; box-shadow:0 2px 8px rgba(66,133,244,.3);
  }}
  @media (hover: hover) {{
    .mode-tab:not(.active):hover {{ background:#e8f0fe; }}
  }}

  /* Buttons */
  .btn {{
    display:inline-flex; align-items:center; justify-content:center; gap:8px;
    padding:14px 36px; border:none; border-radius:50px; font-size:1.1em;
    font-weight:700; cursor:pointer; transition:all .2s; font-family:inherit;
    letter-spacing:.5px; -webkit-tap-highlight-color:transparent;
    white-space:nowrap;
  }}
  .btn:active {{ transform:scale(.95); }}
  .btn-primary {{ background:var(--blue); color:white; box-shadow:0 4px 15px rgba(66,133,244,.4); }}
  .btn-green {{ background:var(--green); color:white; box-shadow:0 4px 15px rgba(52,168,83,.4); }}
  .btn-orange {{ background:var(--orange); color:white; box-shadow:0 4px 15px rgba(245,158,11,.4); }}
  .btn-outline {{ background:white; color:var(--blue); border:2px solid var(--blue); }}
  .btn-sm {{ padding:8px 20px; font-size:.9em; }}
  .btn-lg {{ padding:16px 48px; font-size:1.2em; }}

  @media (hover: hover) {{
    .btn-primary:hover {{ background:#3367d6; }}
    .btn-green:hover {{ background:#2d9249; }}
    .btn-orange:hover {{ background:#d97706; }}
    .btn-outline:hover {{ background:#e8f0fe; }}
  }}

  /* Card */
  .card {{
    width:100%; background:white; border-radius:var(--radius);
    box-shadow:var(--shadow); padding:30px 24px; text-align:center;
    margin-bottom:20px; position:relative; overflow:hidden;
  }}
  .letter-badge {{
    display:inline-flex; align-items:center; justify-content:center;
    width:72px; height:72px; background:var(--blue); color:white;
    border-radius:50%; font-size:2.2em; font-weight:700; margin-bottom:16px;
    transition:transform .3s, background .3s;
  }}
  .letter-badge.question {{ background:var(--orange); }}
  .word-display {{
    font-size:1.6em; font-weight:700; color:var(--text); margin-bottom:8px;
    transition:opacity .4s, max-height .4s;
  }}
  .sentence-display {{
    font-size:1.1em; color:var(--text); line-height:1.6; margin-bottom:8px;
    transition:opacity .4s, max-height .4s;
  }}
  .cn-display {{
    font-size:.85em; color:var(--text-light); line-height:1.5;
    transition:opacity .4s, max-height .4s;
  }}
  .hidden-text {{
    opacity:0; max-height:0; overflow:hidden; margin-bottom:0 !important;
  }}
  .revealed-text {{
    opacity:1; max-height:200px;
  }}

  /* Reveal divider */
  .reveal-divider {{
    width:40px; height:3px; background:#e2e8f0; margin:12px auto;
    border-radius:2px; transition:opacity .3s;
  }}

  /* Progress */
  .progress-wrap {{ margin:20px 0; }}
  .progress-bar {{
    width:100%; height:8px; background:#e2e8f0; border-radius:4px; overflow:hidden;
  }}
  .progress-fill {{
    height:100%; background:var(--green); border-radius:4px; transition:width .3s;
  }}
  .progress-text {{ text-align:center; font-size:.85em; color:var(--text-light); margin-top:6px; }}

  /* Controls */
  .controls {{ display:flex; gap:12px; flex-wrap:wrap; justify-content:center; margin:16px 0; }}
  .pause-controls {{ display:flex; gap:12px; flex-wrap:wrap; justify-content:center; margin:12px 0; }}

  /* Animations */
  @keyframes popIn {{
    0% {{ transform:scale(.8); opacity:0; }}
    100% {{ transform:scale(1); opacity:1; }}
  }}
  .pop {{ animation:popIn .3s ease-out; }}

  @keyframes fadeUp {{
    0% {{ opacity:0; transform:translateY(8px); }}
    100% {{ opacity:1; transform:translateY(0); }}
  }}

  .done-badge {{
    display:inline-block; background:#e8f5e9; color:#2e7d32;
    padding:6px 16px; border-radius:20px; font-weight:700; margin:12px 0;
  }}

  /* Queue dots */
  .queue-dots {{ display:flex; gap:5px; flex-wrap:wrap; justify-content:center; margin-top:16px; }}
  .queue-dot {{
    width:30px; height:30px; border-radius:50%; display:flex; align-items:center;
    justify-content:center; font-size:.65em; font-weight:700; cursor:pointer;
    background:#e2e8f0; color:var(--text-light); transition:all .2s;
    -webkit-tap-highlight-color:transparent;
  }}
  .queue-dot.done {{ background:#c8e6c9; color:#2e7d32; }}
  .queue-dot.current {{ background:var(--blue); color:white; transform:scale(1.25); }}
  .queue-dot.current-question {{ background:var(--orange); color:white; transform:scale(1.25); }}

  /* Responsive */
  @media (max-width:600px) {{
    .header {{ padding:10px 16px; }}
    .header-title {{ font-size:.95em; }}
    .btn {{ padding:12px 28px; font-size:1em; }}
    .card {{ padding:24px 16px; }}
    .letter-badge {{ width:60px; height:60px; font-size:1.8em; }}
    .word-display {{ font-size:1.3em; }}
    .sentence-display {{ font-size:1em; }}
    .queue-dot {{ width:26px; height:26px; font-size:.6em; }}
    .mode-tab {{ font-size:.9em; padding:10px 6px; }}
  }}
</style>
</head>
<body>

<header class="header">
  <div class="header-title">单词听力训练 <span>Part 3 · Word Challenge</span></div>
  <div style="font-size:.85em;color:var(--text-light);" id="progressLabel">准备就绪</div>
</header>

<main class="main">

  <!-- Mode tabs -->
  <div class="mode-tabs">
    <button class="mode-tab active" id="tabEar" onclick="switchMode('ear')">磨耳朵</button>
    <button class="mode-tab" id="tabTrain" onclick="switchMode('train')">训练自测</button>
  </div>

  <!-- Main card -->
  <div class="card" id="nowPlayingCard">
    <div class="letter-badge" id="letterBadge">?</div>
    <div class="word-display hidden-text" id="wordDisplay"></div>
    <div class="sentence-display hidden-text" id="sentenceDisplay"></div>
    <div class="cn-display hidden-text" id="cnDisplay"></div>
    <div class="reveal-divider" id="revealDivider" style="opacity:0;"></div>
  </div>

  <!-- Progress -->
  <div class="progress-wrap">
    <div class="progress-bar"><div class="progress-fill" id="progressFill" style="width:0%"></div></div>
    <div class="progress-text" id="progressText">0 / 26</div>
  </div>

  <!-- Controls -->
  <div class="controls" id="controls"></div>
  <div class="pause-controls" id="pauseControls" style="display:none;"></div>

  <!-- Done message -->
  <div id="doneMessage" style="text-align:center;display:none;">
    <div class="done-badge">本轮完成！</div>
  </div>

  <!-- Queue dots -->
  <div class="queue-dots" id="queueDots"></div>

</main>

<script>
const VOCAB = {vocab_json};
const LETTER_AUDIO = {letter_json};
const WORD_AUDIO = {word_json};
const SENT_AUDIO = {sent_json};

// ===== STATE =====
let mode = 'ear';         // 'ear' | 'train'
let queue = [];
let currentIdx = -1;
let isPlaying = false;
let isPaused = false;
let answerRevealed = false;
let activeAudio = null;
let audioAbort = null;     // resolve function to unblock playAudio on pause

const GAP_WORD_SENT = 1000;   // ear-training: gap between word and sentence (ms)
const GAP_SENT_NEXT = 400;    // training: gap between sentence and next auto-advance

// ===== AUDIO HELPERS =====
// Use atob() + Blob — avoid fetch(data:...) which is unreliable on mobile Safari.
// Reuse a single Audio element — creating new Audio() away from user gesture
// triggers iOS autoplay block.
function getAudioUrl(base64Map, letter) {{
  const b64 = base64Map[letter];
  if (!b64) return null;
  try {{
    const binary = atob(b64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return URL.createObjectURL(new Blob([bytes], {{ type: 'audio/mp3' }}));
  }} catch (e) {{
    return null;
  }}
}}

function stopAudio() {{
  if (activeAudio) {{
    activeAudio.pause();
    // Don't null activeAudio — we reuse the element
  }}
  if (audioAbort) {{
    audioAbort();
    audioAbort = null;
  }}
}}

function playAudio(url) {{
  return new Promise((resolve) => {{
    if (!url) {{ resolve(); return; }}
    stopAudio();

    // Reuse a single Audio element to stay within iOS Safari's autoplay grant
    if (!activeAudio) {{
      activeAudio = new Audio();
    }}
    // Revoke previous blob URL if any
    if (activeAudio.src && activeAudio.src.startsWith('blob:')) {{
      URL.revokeObjectURL(activeAudio.src);
    }}

    let resolved = false;
    const done = () => {{
      if (!resolved) {{
        resolved = true;
        audioAbort = null;
        resolve();
      }}
    }};
    audioAbort = done;

    activeAudio.onended = done;
    activeAudio.onerror = done;
    activeAudio.src = url;
    activeAudio.load();
    activeAudio.play().catch(done);
  }});
}}

function playLetterAudio(letter) {{
  const url = getAudioUrl(LETTER_AUDIO, letter);
  return playAudio(url);
}}

function playWordAudio(letter) {{
  const url = getAudioUrl(WORD_AUDIO, letter);
  return playAudio(url);
}}

function playSentAudio(letter) {{
  const url = getAudioUrl(SENT_AUDIO, letter);
  return playAudio(url);
}}

// ===== REVEAL SOUND (Web Audio API: C5->E5->G5->C6 arpeggio) =====
function playRevealSound() {{
  try {{
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
    const noteDuration = 0.12;
    notes.forEach((freq, i) => {{
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.value = freq;
      const startTime = ctx.currentTime + i * noteDuration;
      const endTime = startTime + noteDuration + 0.08;
      gain.gain.setValueAtTime(0, startTime);
      gain.gain.linearRampToValueAtTime(0.5, startTime + 0.03);
      gain.gain.linearRampToValueAtTime(0.3, startTime + noteDuration);
      gain.gain.linearRampToValueAtTime(0, endTime);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(startTime);
      osc.stop(endTime);
    }});
  }} catch(e) {{ /* audio context not available */ }}
}}

// ===== SHUFFLE =====
function shuffle(arr) {{
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {{
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }}
  return a;
}}

function buildQueue() {{
  const indices = Array.from({{ length: VOCAB.length }}, (_, i) => i);
  queue = shuffle(indices);
  currentIdx = -1;
  isPlaying = false;
  isPaused = false;
  answerRevealed = false;
}}

// ===== MODE SWITCH =====
function switchMode(newMode) {{
  if (mode === newMode) return;
  stopAudio();
  mode = newMode;
  buildQueue();
  document.getElementById('tabEar').classList.toggle('active', mode === 'ear');
  document.getElementById('tabTrain').classList.toggle('active', mode === 'train');
  document.getElementById('doneMessage').style.display = 'none';
  document.getElementById('pauseControls').style.display = 'none';
  if (mode === 'train') {{
    resetCard();
  }} else {{
    showEarPlaceholder();
  }}
  renderControls();
  updateUI();
}}

function showEarPlaceholder() {{
  const wordEl = document.getElementById('wordDisplay');
  const sentEl = document.getElementById('sentenceDisplay');
  const cnEl = document.getElementById('cnDisplay');
  wordEl.textContent = '—';
  sentEl.textContent = '点击开始播放，随机顺序';
  cnEl.textContent = '';
  wordEl.className = 'word-display revealed-text';
  sentEl.className = 'sentence-display revealed-text';
  cnEl.className = 'cn-display hidden-text';
  document.getElementById('revealDivider').style.opacity = '0';
  answerRevealed = false;
}}

// ===== CARD RESET =====
function resetCard() {{
  document.getElementById('wordDisplay').className = 'word-display hidden-text';
  document.getElementById('sentenceDisplay').className = 'sentence-display hidden-text';
  document.getElementById('cnDisplay').className = 'cn-display hidden-text';
  document.getElementById('revealDivider').style.opacity = '0';
  answerRevealed = false;
}}

function showCardContent(item) {{
  const wordEl = document.getElementById('wordDisplay');
  const sentEl = document.getElementById('sentenceDisplay');
  const cnEl = document.getElementById('cnDisplay');
  const divider = document.getElementById('revealDivider');
  wordEl.textContent = item.word;
  sentEl.textContent = item.sentence;
  cnEl.textContent = item.cn_sentence || '';
  wordEl.className = 'word-display revealed-text';
  sentEl.className = 'sentence-display revealed-text';
  cnEl.className = 'cn-display revealed-text';
  divider.style.opacity = '1';
  answerRevealed = true;
}}

function hideCardContent() {{
  const wordEl = document.getElementById('wordDisplay');
  const sentEl = document.getElementById('sentenceDisplay');
  const cnEl = document.getElementById('cnDisplay');
  wordEl.textContent = '';
  sentEl.textContent = '';
  cnEl.textContent = '';
  wordEl.className = 'word-display hidden-text';
  sentEl.className = 'sentence-display hidden-text';
  cnEl.className = 'cn-display hidden-text';
  document.getElementById('revealDivider').style.opacity = '0';
  answerRevealed = false;
}}

function updateBadgeLetter(letter, isQuestion) {{
  const badge = document.getElementById('letterBadge');
  badge.textContent = letter;
  badge.classList.toggle('question', isQuestion);
  badge.classList.remove('pop');
  void badge.offsetWidth;
  badge.classList.add('pop');
}}

// ===== EAR TRAINING MODE =====
async function startEarTraining() {{
  if (currentIdx < 0) buildQueue();
  isPlaying = true;
  isPaused = false;
  answerRevealed = true;
  document.getElementById('doneMessage').style.display = 'none';
  document.getElementById('pauseControls').style.display = 'none';
  renderControls();
  await earPlayLoop();
}}

async function earPlayLoop() {{
  if (currentIdx < 0) currentIdx = -1;
  while (isPlaying && !isPaused) {{
    const nextIdx = currentIdx + 1;
    if (nextIdx >= queue.length) {{
      // Finished
      isPlaying = false;
      document.getElementById('doneMessage').style.display = 'block';
      renderControls();
      updateUI();
      return;
    }}
    currentIdx = nextIdx;
    const item = VOCAB[queue[currentIdx]];
    showCardContent(item);
    updateBadgeLetter(item.letter, false);
    updateUI();

    if (!isPlaying || isPaused) break;
    await playWordAudio(item.letter);
    if (!isPlaying || isPaused) break;
    await sleep(GAP_WORD_SENT);
    if (!isPlaying || isPaused) break;
    await playSentAudio(item.letter);
  }}
  if (!isPlaying || isPaused) {{
    renderControls();
    updateUI();
  }}
}}

function pauseEarTraining() {{
  isPaused = true;
  isPlaying = false;
  stopAudio();
  document.getElementById('pauseControls').style.display = 'flex';
  renderControls();
}}

function resumeEarTraining() {{
  isPaused = false;
  isPlaying = true;
  currentIdx--;  // replay the paused item from its word audio
  document.getElementById('pauseControls').style.display = 'none';
  renderControls();
  earPlayLoop();
}}

async function repeatCurrent() {{
  if (currentIdx < 0 || currentIdx >= queue.length) return;
  const item = VOCAB[queue[currentIdx]];
  await playWordAudio(item.letter);
  await sleep(GAP_WORD_SENT);
  await playSentAudio(item.letter);
}}

function sleep(ms) {{
  return new Promise(r => setTimeout(r, ms));
}}

// ===== TRAINING MODE =====
function startTraining() {{
  stopAudio();
  buildQueue();
  document.getElementById('doneMessage').style.display = 'none';
  advanceTraining();
}}

async function advanceTraining() {{
  stopAudio();
  const nextIdx = currentIdx + 1;
  if (nextIdx >= queue.length) {{
    currentIdx = queue.length - 1;
    document.getElementById('doneMessage').style.display = 'block';
    renderControls();
    updateUI();
    return;
  }}
  currentIdx = nextIdx;
  const item = VOCAB[queue[currentIdx]];
  hideCardContent();
  updateBadgeLetter(item.letter, true);
  updateUI();
  renderControls();
  await playLetterAudio(item.letter);
}}

async function revealAnswer() {{
  if (answerRevealed || currentIdx < 0 || currentIdx >= queue.length) return;
  answerRevealed = true;  // block double-clicks immediately
  const item = VOCAB[queue[currentIdx]];
  playRevealSound();
  // Small delay to let the sound start before text appears
  await sleep(200);
  showCardContent(item);
  updateUI();
  renderControls();
  await playWordAudio(item.letter);
  await sleep(400);
  await playSentAudio(item.letter);
}}

function trainNext() {{
  advanceTraining();
}}

async function replayTraining() {{
  if (currentIdx < 0 || currentIdx >= queue.length) return;
  const item = VOCAB[queue[currentIdx]];
  await playWordAudio(item.letter);
  await sleep(400);
  await playSentAudio(item.letter);
}}

function jumpToEar(queueIdx) {{
  if (mode !== 'ear' || isPaused) return;
  stopAudio();
  currentIdx = queueIdx - 1;  // earPlayLoop will advance to queueIdx
  earPlayLoop();
}}

function reshuffle() {{
  stopAudio();
  isPlaying = false;
  isPaused = false;
  answerRevealed = false;
  buildQueue();
  document.getElementById('doneMessage').style.display = 'none';
  document.getElementById('pauseControls').style.display = 'none';
  resetCard();
  renderControls();
  updateUI();
}}

// ===== RENDER CONTROLS =====
function renderControls() {{
  const container = document.getElementById('controls');
  const done = document.getElementById('doneMessage').style.display !== 'none';

  if (mode === 'ear') {{
    if (done) {{
      container.innerHTML = `
        <button class="btn btn-green btn-lg" onclick="reshuffle(); startEarTraining();">再来一轮</button>
        <button class="btn btn-outline btn-sm" onclick="reshuffle();">重新打乱</button>
      `;
    }} else if (isPlaying && !isPaused) {{
      container.innerHTML = `
        <button class="btn btn-outline" onclick="pauseEarTraining();">暂停</button>
        <button class="btn btn-sm" style="background:#e2e8f0;color:var(--text-light);border:none;" onclick="reshuffle();">重新打乱</button>
      `;
    }} else if (isPaused) {{
      container.innerHTML = '';
    }} else {{
      container.innerHTML = `
        <button class="btn btn-green btn-lg" onclick="startEarTraining();">开始播放</button>
        <button class="btn btn-outline btn-sm" onclick="reshuffle();">重新打乱</button>
      `;
    }}

    // Pause bar
    const pauseDiv = document.getElementById('pauseControls');
    if (isPaused && !done) {{
      pauseDiv.style.display = 'flex';
      pauseDiv.innerHTML = `
        <button class="btn btn-orange" onclick="repeatCurrent();">再说一遍</button>
        <button class="btn btn-primary" onclick="resumeEarTraining();">继续</button>
      `;
    }} else {{
      pauseDiv.style.display = 'none';
    }}

  }} else {{ // train mode
    if (done) {{
      container.innerHTML = `
        <button class="btn btn-green btn-lg" onclick="reshuffle(); startTraining();">再来一轮</button>
      `;
    }} else if (currentIdx < 0) {{
      container.innerHTML = `
        <button class="btn btn-green btn-lg" onclick="startTraining();">开始训练</button>
      `;
    }} else if (!answerRevealed) {{
      container.innerHTML = `
        <button class="btn btn-orange btn-lg" onclick="revealAnswer();">显示答案</button>
      `;
    }} else {{
      container.innerHTML = `
        <button class="btn btn-primary btn-lg" onclick="trainNext();">下一个</button>
        <button class="btn btn-outline btn-sm" onclick="replayTraining();">再听一遍</button>
      `;
    }}
    document.getElementById('pauseControls').style.display = 'none';
  }}
}}

// ===== UI UPDATE =====
function updateUI() {{
  const progressFill = document.getElementById('progressFill');
  const progressText = document.getElementById('progressText');
  const progressLabel = document.getElementById('progressLabel');
  const queueDots = document.getElementById('queueDots');

  const done = currentIdx >= 0 ? currentIdx + 1 : 0;
  const pct = VOCAB.length > 0 ? (done / VOCAB.length * 100) : 0;
  progressFill.style.width = pct + '%';
  progressText.textContent = done + ' / ' + VOCAB.length;

  if (mode === 'ear') {{
    if (isPlaying) progressLabel.textContent = '正在播放';
    else if (isPaused) progressLabel.textContent = '已暂停';
    else if (done >= VOCAB.length) progressLabel.textContent = '已完成';
    else progressLabel.textContent = '准备就绪';
  }} else {{
    if (currentIdx >= 0 && !answerRevealed) progressLabel.textContent = '请回忆单词和句子';
    else if (currentIdx >= 0 && answerRevealed) progressLabel.textContent = '答案已显示';
    else if (done >= VOCAB.length) progressLabel.textContent = '已完成';
    else progressLabel.textContent = '准备就绪';
  }}

  // Queue dots
  let dotsHTML = '';
  for (let i = 0; i < queue.length; i++) {{
    const item = VOCAB[queue[i]];
    let cls = 'queue-dot';
    if (i < currentIdx) cls += ' done';
    else if (i === currentIdx) {{
      if (mode === 'train' && !answerRevealed) cls += ' current-question';
      else cls += ' current';
    }}
    const isHidden = mode === 'train' && !answerRevealed && i === currentIdx;
    const title = isHidden ? '?' : (item.letter + '. ' + item.word);
    const onclick = (mode === 'ear' && i !== currentIdx) ? `onclick="jumpToEar(${{i}})"` : '';
    dotsHTML += `<div class="${{cls}}" title="${{title}}" ${{onclick}}>${{isHidden ? '?' : item.letter}}</div>`;
  }}
  queueDots.innerHTML = dotsHTML;
}}

// ===== INIT =====
buildQueue();
showEarPlaceholder();
renderControls();
updateUI();
</script>
</body>
</html>'''
    return html

if __name__ == "__main__":
    items = extract_items()
    print(f"Extracted {len(items)} items")

    print("Loading letter audio...")
    letter_map = load_audio_map("letter_")
    print(f"  {len(letter_map)} files")

    print("Loading word audio...")
    word_map = load_audio_map("word_")
    print(f"  {len(word_map)} files")

    print("Loading sentence audio...")
    sent_map = load_audio_map("sent_")
    print(f"  {len(sent_map)} files")

    print("Loading combined audio (legacy)...")
    combined_map = load_audio_map("Q")
    print(f"  {len(combined_map)} files")

    html = build_html(items, letter_map, word_map, sent_map, combined_map)
    with open(OUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    size_kb = os.path.getsize(OUT_HTML) / 1024
    print(f"Written {OUT_HTML} ({size_kb:.0f} KB)")
