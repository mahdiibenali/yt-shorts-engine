# 🎬 YT Shorts Engine

An automated, end-to-end **YouTube Shorts content factory** — from topic discovery to published video. Combines the best ideas from ConsisID, Short-Video-Maker, HA6Bots, MoCoGAN and Auto-YouTube-Shorts-Maker into one unified platform.

![CI](https://github.com/mahdiibenali/yt-shorts-engine/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker)
![License](https://img.shields.io/badge/License-MIT-green)

## 🎯 The problem

Running multiple faceless Shorts channels means repeating the same manual loop daily: find a topic, write a hook, generate images, record narration, time captions, cut gameplay footage, render 9:16, upload, track what worked. This engine automates the entire loop with **zero-cost provider fallbacks** so a missing API key never blocks production.

## ✨ Features

- **Content sourcing** — import trending topics from Reddit (PRAW) or write scripts via AI
- **Multi-tier free AI fallback** — Ollama → g4f → Pollinations → 9Router → OpenAI → offline templates (`SmartRouter`) — never hard-blocks on one vendor
- **Background-video fallback chain** — Pexels → Pixabay → Coverr → Pollinations AI video
- **Image-provider chain** — DashScope → Cloudflare FLUX → Pollinations → local Stable Diffusion, plus keyless Wikimedia Commons real-photo reveals (license metadata recorded)
- **AI director engine** — style-bible/world-state continuity, semantic-beat storyboarding and a DirectorCoach that audits rhythm & safety (`app/video/director/`)
- **Precision captions** — faster-whisper word-level timestamps drive karaoke highlighting; spoken countdowns ("three…two…one") trigger photo reveals exactly on cue
- **Text-to-speech** — Microsoft neural voices via edge-tts
- **Rendering** — MoviePy composition: split-screen gameplay or full-screen, ≤58 s vertical output + thumbnails
- **Human review loop** — Tinder-style Streamlit swipe UI to approve/edit before rendering
- **Auto-upload** — YouTube Data API v3 OAuth2 with quota accounting (1,658 units/video against the 10,000 daily budget) and an SQLite ops journal across channels
- **Ops dashboard** — Streamlit overview over the journal database; Dockerized deployment

## 🏗️ Architecture

```
batch_generate.py ──► generate_short.py ──► MP4 + thumbnail ──► upload/youtube ──► journal.db
                          │
        ┌─────────────────┼──────────────────┐
   audio/tts      video/captions       video/director
   (edge-tts)     (faster-whisper)     (storyboards, world state)
                          │
        image_providers / background routers (multi-tier fallback)

run.py ── server | worker | ui | setup        # FastAPI :8000 · worker poller · Streamlit :8501
```

Two ways to run it: **batch mode** for hands-off channel production, or the **interactive path** (FastAPI + review UI + polling worker). Full deep-dive in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## 🚀 Quick start

```bash
pip install -r requirements.txt
cp .env.example .env          # add PEXELS_API_KEY (the only strictly required key)
python run.py setup           # guided first-time setup (voices, YouTube OAuth…)
```

Or with Docker:

```bash
docker-compose up -d          # api :8000 + worker + review ui :8501
```

Generate videos:

```bash
python batch_generate.py --list              # see defined channels
python batch_generate.py --channel critter   # produce a short for a channel
```

Interactive services:

```bash
python run.py server          # FastAPI on :8000 (Swagger at /docs)
python run.py worker          # polls approved scripts every 30 s
python run.py ui              # swipe-review UI on :8501
streamlit run dashboard.py    # ops dashboard (needs pandas + plotly)
```

## 🔑 Environment

Only `PEXELS_API_KEY` is required. Everything else degrades gracefully through the free-provider fallback chain — see [.env.example](.env.example). YouTube upload needs `client_secrets.json` from Google Cloud Console (OAuth2 desktop flow; handled by `run.py setup`).

## 📁 Project structure

```
app/
├── api/          # FastAPI routes
├── audio/        # TTS engine
├── content/      # Reddit + AI script writers
├── render/       # MoviePy composer + thumbnails
├── ui/           # Review dashboard
├── upload/       # YouTube OAuth uploader + quota guard
├── video/        # Captions, backgrounds, director engine, image providers
└── worker/       # Generation pipeline orchestrator
docs/             # ARCHITECTURE.md, channel strategy & upload playbooks
```

## 🧪 Testing

No automated suite yet — CI runs a full syntax gate over all Python sources ([workflow](.github/workflows/ci.yml)); heavy media dependencies make sandboxed rendering tests impractical today. `test_milestone1_director.py` is a manual integration script exercising the director pipeline end-to-end.

## 🔭 Roadmap

- [ ] Bayesian self-learning loop (belief store + A/B experiment scheduler — design in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md))
- [ ] pytest suites for providers, caption timing and quota math
- [ ] Ruff lint pass in CI
- [ ] Channel asset generator cleanup (profile pics / banners)

## 📄 License

MIT — see [LICENSE](LICENSE).
