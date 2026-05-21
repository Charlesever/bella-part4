#!/usr/bin/env python3
"""Extract vocab from 单词表.docx and generate split MP3 files via edge-tts.

Generates 4 sets of audio per letter:
  QA.mp3      — combined: "A. adventure. I read a book..."  (legacy, kept)
  letter_A.mp3 — letter only: "A"
  word_A.mp3   — word only: "adventure"
  sent_A.mp3   — sentence only: "I read a book..."
"""

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

        raw_sentence = paragraphs[i + 1] if i + 1 < len(paragraphs) else ""

        # Split English and Chinese parts (handle mixed-line case)
        eng_parts = []
        for ch in raw_sentence:
            if '一' <= ch <= '鿿' or '　' <= ch <= '〿' or '＀' <= ch <= '￯':
                continue
            eng_parts.append(ch)
        sentence = ''.join(eng_parts).strip().rstrip(' ，。、；：！？0123456789 ')

        cn_sentence = paragraphs[i + 2] if i + 2 < len(paragraphs) else ""
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


def tts(text, out_path):
    """Run edge-tts for a single text, writing to out_path. Returns True on success."""
    try:
        subprocess.run([
            "edge-tts",
            "--voice", VOICE,
            "--text", text,
            "--write-media", out_path
        ], check=True, capture_output=True, timeout=60)
        return True
    except subprocess.CalledProcessError as e:
        msg = e.stderr.decode()[:120] if e.stderr else str(e)
        print(f"  FAIL: {msg}")
        return False


def generate_all(items):
    """Generate 4 sets of MP3 files for each vocab item."""
    os.makedirs(OUT_DIR, exist_ok=True)

    for item in items:
        letter = item["letter"]
        word = item["word"]
        sentence = item["sentence"]

        # 1. Combined: "A. adventure. I read a book..."
        path_combined = os.path.join(OUT_DIR, f"Q{letter}.mp3")
        if not (os.path.exists(path_combined) and os.path.getsize(path_combined) > 0):
            text = f"{letter}. {word}. {sentence}"
            print(f"[{letter}] combined: {text[:80]}...", end=" ", flush=True)
            if tts(text, path_combined):
                print("OK")
        else:
            print(f"[{letter}] combined SKIP (exists)")

        # 2. Letter only: "A"
        path_letter = os.path.join(OUT_DIR, f"letter_{letter}.mp3")
        if not (os.path.exists(path_letter) and os.path.getsize(path_letter) > 0):
            text = letter
            print(f"[{letter}] letter:   {text}", end=" ", flush=True)
            if tts(text, path_letter):
                print("OK")

        # 3. Word only: "adventure"
        path_word = os.path.join(OUT_DIR, f"word_{letter}.mp3")
        if not (os.path.exists(path_word) and os.path.getsize(path_word) > 0):
            text = word
            print(f"[{letter}] word:     {text}", end=" ", flush=True)
            if tts(text, path_word):
                print("OK")

        # 4. Sentence only: "I read a book..."
        path_sent = os.path.join(OUT_DIR, f"sent_{letter}.mp3")
        if not (os.path.exists(path_sent) and os.path.getsize(path_sent) > 0):
            text = sentence
            print(f"[{letter}] sentence: {text[:80]}...", end=" ", flush=True)
            if tts(text, path_sent):
                print("OK")

    print(f"\nDone — files in {OUT_DIR}")


if __name__ == "__main__":
    items = extract_items(DOCX_PATH)
    print(f"Extracted {len(items)} items from docx")

    # Save extracted data for build-player.py
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vocab-data.json")
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"Saved vocab data to {data_path}")

    generate_all(items)
