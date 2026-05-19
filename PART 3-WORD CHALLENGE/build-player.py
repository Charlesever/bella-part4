#!/usr/bin/env python3
"""Build vocab-player.html with embedded base64 audio and vocab data."""

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
        # English sentence (next paragraph, strip any Chinese mixed in)
        raw_sentence = paragraphs[i + 1] if i + 1 < len(paragraphs) else ""
        sentence = re.sub(r'[一-鿿]+.*', '', raw_sentence).strip()
        sentence = sentence.rstrip(' ，。、；：！？0123456789 ').strip()
        # Chinese translation (2 paragraphs after letter+word)
        cn_sentence = paragraphs[i + 2] if i + 2 < len(paragraphs) else ""
        if cn_sentence and not any('一' <= c <= '鿿' for c in cn_sentence):
            cn_sentence = paragraphs[i + 3] if i + 3 < len(paragraphs) else ""
        cn_sentence = cn_sentence.strip()
        if sentence:
            items.append({"letter": letter, "word": word, "sentence": sentence, "cn_sentence": cn_sentence})
    return items

def load_audio_base64(items):
    audio_map = {}
    for item in items:
        fpath = os.path.join(AUDIO_DIR, f"Q{item['letter']}.mp3")
        if os.path.exists(fpath):
            with open(fpath, 'rb') as f:
                audio_map[item['letter']] = base64.b64encode(f.read()).decode('ascii')
        else:
            print(f"WARNING: {fpath} not found")
    return audio_map

def build_html(items, audio_map):
    vocab_json = json.dumps(items, ensure_ascii=False)
    audio_json = json.dumps(audio_map, ensure_ascii=False)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<title>Part 3 Word Challenge — Vocab Player</title>
<style>
  :root {{
    --blue: #4285f4; --green: #34a853; --bg: #f0f4f8; --card: #ffffff;
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

  .btn {{
    display:inline-flex; align-items:center; justify-content:center; gap:8px;
    padding:14px 36px; border:none; border-radius:50px; font-size:1.1em;
    font-weight:700; cursor:pointer; transition:all .2s; font-family:inherit;
    letter-spacing:.5px; -webkit-tap-highlight-color:transparent;
  }}
  .btn:active {{ transform:scale(.95); }}
  .btn-primary {{ background:var(--blue); color:white; box-shadow:0 4px 15px rgba(66,133,244,.4); }}
  .btn-green {{ background:var(--green); color:white; box-shadow:0 4px 15px rgba(52,168,83,.4); }}
  .btn-outline {{ background:white; color:var(--blue); border:2px solid var(--blue); }}
  .btn-sm {{ padding:8px 20px; font-size:.9em; }}

  @media (hover: hover) {{
    .btn-primary:hover {{ background:#3367d6; }}
    .btn-green:hover {{ background:#2d9249; }}
    .btn-outline:hover {{ background:#e8f0fe; }}
  }}

  .card {{
    width:100%; background:white; border-radius:var(--radius);
    box-shadow:var(--shadow); padding:30px 24px; text-align:center;
    margin-bottom:20px;
  }}
  .letter-badge {{
    display:inline-flex; align-items:center; justify-content:center;
    width:64px; height:64px; background:var(--blue); color:white;
    border-radius:50%; font-size:2em; font-weight:700; margin-bottom:16px;
  }}
  .word-display {{ font-size:1.6em; font-weight:700; color:var(--text); margin-bottom:12px; }}
  .sentence-display {{ font-size:1.1em; color:var(--text); line-height:1.6; }}
  .cn-display {{ font-size:.85em; color:var(--text-light); margin-top:8px; line-height:1.5; }}

  .progress-wrap {{ margin:20px 0; }}
  .progress-bar {{
    width:100%; height:8px; background:#e2e8f0; border-radius:4px; overflow:hidden;
  }}
  .progress-fill {{
    height:100%; background:var(--green); border-radius:4px; transition:width .3s;
  }}
  .progress-text {{ text-align:center; font-size:.85em; color:var(--text-light); margin-top:6px; }}

  .btn-row {{ display:flex; gap:12px; flex-wrap:wrap; justify-content:center; }}

  .controls {{ display:flex; gap:12px; justify-content:center; margin:20px 0; }}

  /* Shuffle animation */
  @keyframes popIn {{
    0% {{ transform:scale(.8); opacity:0; }}
    100% {{ transform:scale(1); opacity:1; }}
  }}
  .pop {{ animation:popIn .3s ease-out; }}

  .done-badge {{
    display:inline-block; background:#e8f5e9; color:#2e7d32;
    padding:6px 16px; border-radius:20px; font-weight:700; margin:12px 0;
  }}

  /* Queue preview dots */
  .queue-dots {{ display:flex; gap:4px; flex-wrap:wrap; justify-content:center; margin-top:16px; }}
  .queue-dot {{
    width:28px; height:28px; border-radius:50%; display:flex; align-items:center;
    justify-content:center; font-size:.65em; font-weight:700; cursor:pointer;
    background:#e2e8f0; color:var(--text-light); transition:all .2s;
  }}
  .queue-dot.done {{ background:#c8e6c9; color:#2e7d32; }}
  .queue-dot.current {{ background:var(--blue); color:white; transform:scale(1.2); }}

  @media (max-width:600px) {{
    .header {{ padding:10px 16px; }}
    .header-title {{ font-size:.95em; }}
    .btn {{ padding:12px 28px; font-size:1em; }}
    .card {{ padding:24px 16px; }}
    .letter-badge {{ width:52px; height:52px; font-size:1.6em; }}
    .word-display {{ font-size:1.3em; }}
    .sentence-display {{ font-size:1em; }}
    .queue-dot {{ width:24px; height:24px; font-size:.6em; }}
  }}
</style>
</head>
<body>

<header class="header">
  <div class="header-title">单词听力训练 <span>Part 3 · Word Challenge</span></div>
  <div style="font-size:.85em;color:var(--text-light);" id="progressLabel">准备就绪</div>
</header>

<main class="main">

  <div class="card" id="nowPlayingCard">
    <div class="letter-badge" id="letterBadge">A</div>
    <div class="word-display" id="wordDisplay">—</div>
    <div class="sentence-display" id="sentenceDisplay">点击开始播放，随机顺序</div>
    <div class="cn-display" id="cnDisplay"></div>
  </div>

  <div class="progress-wrap">
    <div class="progress-bar"><div class="progress-fill" id="progressFill" style="width:0%"></div></div>
    <div class="progress-text" id="progressText">0 / 26</div>
  </div>

  <div class="controls">
    <button class="btn btn-green" id="btnPlay" onclick="togglePlay()">开始播放</button>
    <button class="btn btn-outline btn-sm" id="btnShuffle" onclick="reshuffle()">重新打乱</button>
  </div>

  <div class="queue-dots" id="queueDots"></div>

  <div id="doneMessage" style="text-align:center;display:none;">
    <div class="done-badge">本轮完成！</div>
  </div>

</main>

<script>
const VOCAB = {vocab_json};
const AUDIO_BASE64 = {audio_json};

// ===== STATE =====
let queue = [];           // shuffled indices (0-25)
let currentIdx = -1;      // position within queue
let isPlaying = false;
let paused = false;
let audioElement = null;
const GAP_MS = 1000;      // pause between items

// ===== SHUFFLE (Fisher-Yates) =====
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
  paused = false;
}}

// ===== AUDIO =====
async function getAudioUrl(letter) {{
  const b64 = AUDIO_BASE64[letter];
  if (!b64) return null;
  try {{
    const dataUri = 'data:audio/mp3;base64,' + b64;
    const resp = await fetch(dataUri);
    const blob = await resp.blob();
    return URL.createObjectURL(blob);
  }} catch (e) {{
    return null;
  }}
}}

async function playItem(index) {{
  if (index >= queue.length) {{
    isPlaying = false;
    updateUI();
    document.getElementById('doneMessage').style.display = 'block';
    document.getElementById('btnPlay').textContent = '再来一轮';
    document.getElementById('btnPlay').className = 'btn btn-green';
    return;
  }}
  currentIdx = index;
  const item = VOCAB[queue[index]];
  updateUI();

  stopAudio();
  const url = await getAudioUrl(item.letter);
  if (!url) {{
    if (isPlaying && !paused) setTimeout(() => playItem(index + 1), GAP_MS);
    return;
  }}
  audioElement = new Audio(url);
  audioElement.onended = () => {{
    URL.revokeObjectURL(url);
    audioElement = null;
    if (isPlaying && !paused) setTimeout(() => playItem(index + 1), GAP_MS);
  }};
  audioElement.onerror = () => {{
    URL.revokeObjectURL(url);
    audioElement = null;
    if (isPlaying && !paused) setTimeout(() => playItem(index + 1), GAP_MS);
  }};
  try {{
    await audioElement.play();
  }} catch (e) {{
    URL.revokeObjectURL(url);
    audioElement = null;
    if (isPlaying && !paused) setTimeout(() => playItem(index + 1), GAP_MS);
  }}
}}

function stopAudio() {{
  if (audioElement) {{
    audioElement.pause();
    audioElement = null;
  }}
}}

// ===== CONTROLS =====
function togglePlay() {{
  const btn = document.getElementById('btnPlay');
  const doneMsg = document.getElementById('doneMessage');
  doneMsg.style.display = 'none';

  if (currentIdx >= queue.length - 1 && !isPlaying) {{
    // Finished or initial — restart
    buildQueue();
  }}

  if (isPlaying) {{
    // Pause
    paused = true;
    isPlaying = false;
    stopAudio();
    btn.textContent = '继续播放';
    btn.className = 'btn btn-primary';
  }} else if (paused) {{
    // Resume
    paused = false;
    isPlaying = true;
    playItem(currentIdx >= 0 ? currentIdx : 0);
    btn.textContent = '暂停';
    btn.className = 'btn btn-outline';
  }} else {{
    // Start fresh
    if (currentIdx < 0) buildQueue();
    isPlaying = true;
    playItem(0);
    btn.textContent = '暂停';
    btn.className = 'btn btn-outline';
  }}
  updateUI();
}}

function reshuffle() {{
  stopAudio();
  isPlaying = false;
  paused = false;
  buildQueue();
  document.getElementById('doneMessage').style.display = 'none';
  document.getElementById('btnPlay').textContent = '开始播放';
  document.getElementById('btnPlay').className = 'btn btn-green';
  currentIdx = -1;
  updateUI();
}}

function jumpTo(queueIdx) {{
  stopAudio();
  isPlaying = true;
  paused = false;
  currentIdx = queueIdx - 1;
  playItem(queueIdx);
  document.getElementById('btnPlay').textContent = '暂停';
  document.getElementById('btnPlay').className = 'btn btn-outline';
  document.getElementById('doneMessage').style.display = 'none';
}}

// ===== UI =====
function updateUI() {{
  const progressFill = document.getElementById('progressFill');
  const progressText = document.getElementById('progressText');
  const letterBadge = document.getElementById('letterBadge');
  const wordDisplay = document.getElementById('wordDisplay');
  const sentenceDisplay = document.getElementById('sentenceDisplay');
  const cnDisplay = document.getElementById('cnDisplay');
  const progressLabel = document.getElementById('progressLabel');
  const queueDots = document.getElementById('queueDots');

  const done = currentIdx >= 0 ? currentIdx + 1 : 0;
  const pct = VOCAB.length > 0 ? (done / VOCAB.length * 100) : 0;
  progressFill.style.width = pct + '%';
  progressText.textContent = done + ' / ' + VOCAB.length;

  if (currentIdx >= 0 && currentIdx < queue.length) {{
    const item = VOCAB[queue[currentIdx]];
    letterBadge.textContent = item.letter;
    wordDisplay.textContent = item.word;
    sentenceDisplay.textContent = item.sentence;
    cnDisplay.textContent = item.cn_sentence || '';
    letterBadge.classList.remove('pop');
    void letterBadge.offsetWidth;
    letterBadge.classList.add('pop');
    progressLabel.textContent = '正在播放';
  }} else if (done >= VOCAB.length) {{
    cnDisplay.textContent = '';
    progressLabel.textContent = '已完成';
  }} else {{
    letterBadge.textContent = '?';
    wordDisplay.textContent = '—';
    sentenceDisplay.textContent = '点击开始播放，随机顺序';
    cnDisplay.textContent = '';
    progressLabel.textContent = '准备就绪';
  }}

  // Queue dots
  let dotsHTML = '';
  for (let i = 0; i < queue.length; i++) {{
    const item = VOCAB[queue[i]];
    let cls = 'queue-dot';
    if (i < currentIdx) cls += ' done';
    else if (i === currentIdx) cls += ' current';
    dotsHTML += `<div class="${{cls}}" onclick="jumpTo(${{i}})" title="${{item.letter}}. ${{item.word}}">${{item.letter}}</div>`;
  }}
  queueDots.innerHTML = dotsHTML;
}}

// ===== INIT =====
buildQueue();
updateUI();
</script>
</body>
</html>'''
    return html

if __name__ == "__main__":
    items = extract_items()
    print(f"Extracted {len(items)} items")
    audio_map = load_audio_base64(items)
    print(f"Loaded {len(audio_map)} audio files")
    html = build_html(items, audio_map)
    with open(OUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    size_kb = os.path.getsize(OUT_HTML) / 1024
    print(f"Written {OUT_HTML} ({size_kb:.0f} KB)")
