#!/usr/bin/env python3
"""Extract vocab from 单词表.docx and generate 26 MP3 files via edge-tts with SSML pauses."""

import json, os, re, subprocess, sys
from docx import Document

DOCX_PATH = "/Users/charlesever/Downloads/单词表.docx"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")
VOICE = "en-US-AriaNeural"

def extract_items(path):
    """Extract letter, word, sentence, and Chinese translations from docx."""
    doc = Document(path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    items = []
    for i, p in enumerate(paragraphs):
        m = re.match(r'^([A-Z])\s{2,}(\w+)$', p)
        if not m:
            continue
        letter = m.group(1)
        word = m.group(2)

        # English sentence (next non-empty paragraph)
        raw_sentence = paragraphs[i + 1] if i + 1 < len(paragraphs) else ""

        # Split English and Chinese parts (handle mixed-line case like N)
        eng_parts = []
        cn_parts = []
        for ch in raw_sentence:
            if '一' <= ch <= '鿿' or '　' <= ch <= '〿' or '＀' <= ch <= '￯':
                cn_parts.append(ch)
            else:
                eng_parts.append(ch)
        sentence = ''.join(eng_parts).strip().rstrip(' ，。、；：！？0123456789 ')

        # Chinese translation for sentence (next paragraph after English)
        cn_sentence = paragraphs[i + 2] if i + 2 < len(paragraphs) else ""
        # The Chinese translation paragraph might also have mixed content; take the CJK part
        # or if the whole paragraph is Chinese, use it directly
        if cn_sentence and not any('一' <= c <= '鿿' for c in cn_sentence):
            cn_sentence = paragraphs[i + 3] if i + 3 < len(paragraphs) else ""
        cn_sentence = cn_sentence.strip()

        if sentence:
            items.append({
                "letter": letter,
                "word": word,
                "sentence": sentence,
                "cn_sentence": cn_sentence
            })
    return items

def generate_audio(items):
    """Generate one MP3 per item using edge-tts --file with SSML break tags."""
    import tempfile
    os.makedirs(OUT_DIR, exist_ok=True)
    for item in items:
        fpath = os.path.join(OUT_DIR, f"Q{item['letter']}.mp3")
        if os.path.exists(fpath) and os.path.getsize(fpath) > 0:
            print(f"[{item['letter']}] SKIP (already exists)")
            continue

        ssml = (
            '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">\n'
            f'  {item["letter"]}.<break time="400ms"/>{item["word"]}.<break time="300ms"/>{item["sentence"]}\n'
            '</speak>'
        )

        print(f"[{item['letter']}] {item['letter']}. {item['word']}. {item['sentence'][:60]}...", end=" ", flush=True)
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as tf:
                tf.write(ssml)
                tmpname = tf.name
            subprocess.run([
                "edge-tts",
                "--voice", VOICE,
                "--file", tmpname,
                "--write-media", fpath
            ], check=True, capture_output=True, timeout=60)
            os.unlink(tmpname)
            print("OK")
        except subprocess.CalledProcessError as e:
            msg = e.stderr.decode()[:120] if e.stderr else str(e)
            print(f"FAIL: {msg}")
    print(f"\nDone — items expected in {OUT_DIR}")

if __name__ == "__main__":
    items = extract_items(DOCX_PATH)
    print(f"Extracted {len(items)} items from docx")

    # Save extracted data for build-player.py to use
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vocab-data.json")
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"Saved vocab data to {data_path}")

    generate_audio(items)
