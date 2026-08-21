# 🎬 YT Shorts Engine

An automated, end-to-end **YouTube Shorts content factory** — from topic discovery to published video. Combines the best ideas from ConsisID, Short-Video-Maker, HA6Bots, MoCoGAN and Auto-YouTube-Shorts-Maker into one unified platform.

> 📈 Battle-tested: powers real YouTube channels with published videos and organic views.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- **Content sourcing** — import trending topics from Reddit (PRAW) or generate via AI
- **Multi-tier free AI fallback** — Ollama → g4f → 9Router → Pollinations → OpenAI → templates (never blocks on a single provider)
- **AI director engine** — scene planning, prompt translation and world-state continuity (`app/video/director/`)
- **Visual storytelling engine** — shot libraries, reveal images, UI graphics, AI video generation (Jimeng/Dreamina + Pollinations)
- **Text-to-speech** — Microsoft neural voices via edge-tts
- **Auto-captions** — Whisper word-level timing with karaoke highlighting
- **Background videos** — Pexels → Pixabay → Coverr → Pollinations auto-fallback chain
- **Human review loop** — Tinder-style swipe UI to approve/edit before rendering
- **Rendering** — MoviePy composition with captions, music and thumbnails
- **Auto-upload** — YouTube Data API v3 with OAuth2, status tracking and journaling
- **Ops dashboard** — Streamlit dashboard, SQLite journal, Dockerized deployment

## 🏗️ Architecture

```
content/ ──► worker/generator ──► video/ (director · captions · backgrounds)
   │                 │                      │
   │                 ▼                      ▼
reddit / AI     render/composer ──► upload/youtube ──► journal.db
                    ▲
             ui/review.py (human-in-the-loop)
```

## 🚀 Quick start

```bash
pip install -r requirements.txt
cp .env.example .env        # add PEXELS_API_KEY (required)
python run.py               # starts API + worker
```

Or with Docker:

```bash
docker-compose up -d
```

Generate a short:

```bash
python generate_short.py --topic "your topic"
# or batch mode
python batch_generate.py --count 5
```

## 📁 Project structure

```
app/
├── api/          # FastAPI routes
├── audio/        # TTS engine
├── content/      # Reddit + AI script writers
├── render/       # MoviePy composer + thumbnails
├── ui/           # Review dashboard
├── upload/       # YouTube OAuth uploader
├── video/        # Captions, backgrounds, director engine, storytelling
└── worker/       # Generation pipeline orchestrator
docs/             # Architecture & channel strategy notes
```

## 🔑 Environment

Only `PEXELS_API_KEY` is required. Everything else degrades gracefully through the free-provider fallback chain — see `.env.example`.

## 📄 License

MIT — see [LICENSE](LICENSE).
