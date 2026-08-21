# YT Shorts Engine — Channel Launch & Monetization Strategy

## Architecture Overview

```
                    ┌──────────────┐
                    │  Reddit API  │
                    │  (Content)   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐     ┌───────────────┐
                    │  Review UI   │────▶│  AI Refiner   │
                    │  (Swipe/Edit)│     │  (OpenAI)     │
                    └──────┬───────┘     └───────┬───────┘
                           │                     │
                    ┌──────▼─────────────────────▼───────┐
                    │        Video Generator Worker       │
                    │  ┌────────┐ ┌────────┐ ┌────────┐  │
                    │  │  TTS   │ │Caption │ │Pexels  │  │
                    │  │(edge)  │ │(Whisp.)│ │(Video) │  │
                    │  └────────┘ └────────┘ └────────┘  │
                    │  ┌────────┐ ┌────────┐ ┌────────┐  │
                    │  │Composer│ │Thumb.  │ │ Music  │  │
                    │  │(MovPy) │ │(PIL)   │ │(Kevin) │  │
                    │  └────────┘ └────────┘ └────────┘  │
                    └────────────────┬───────────────────┘
                                     │
                    ┌────────────────▼───────────────────┐
                    │       YouTube Upload API           │
                    │  (Quota-managed, scheduled)         │
                    └────────────────┬───────────────────┘
                                     │
                              ┌──────▼──────┐
                              │  YouTube    │
                              │  Channel    │
                              └─────────────┘
```

## Phase 1: Foundation (Week 1–2)

### 1.1 Channel Setup
- **Niche selection**: Pick ONE of these proven Shorts niches:
  - `r/AskReddit` stories (proven formula, lowest effort)
  - `r/AmItheAsshole` moral dilemmas (high engagement)
  - `r/LifeProTips` useful advice (shareable)
  - `r/TodayILearned` facts (educational)
  - Gaming moments (requires custom gameplay footage)
- **Channel identity**: Username, avatar, banner, description with keywords
- **Monetization prerequisites**:
  - 1,000 subscribers
  - 4,000 watch hours (public) OR 10M Shorts views (90-day window)
  - AdSense account

### 1.2 System Deployment
```bash
# Option A: Docker (recommended)
docker compose up -d

# Option B: Local
pip install -r requirements.txt
python run.py setup
python run.py server &     # API :8000
python run.py ui &         # UI :8501
python run.py worker &     # Background generator
```

### 1.3 Initial Content Strategy
- **Upload 1 video/day minimum** (3/day ideal)
- Use the Review UI to:
  1. Fetch 5–10 Reddit posts
  2. Swipe-approve the best comments (high score, engaging, not offensive)
  3. Let AI refine the script
  4. Approve → worker generates + uploads automatically
- **Title format**: `[Hook] #shorts`
- **First 10 videos**: Test different niches/voices/formats

## Phase 2: Growth (Week 3–6)

### 2.1 Scaling Production
- Increase to **3–6 videos/day** (YouTube API max)
- Use multiple subreddits for variety
- A/B test:
  - Different TTS voices (male vs female, different accents)
  - Caption positions (top vs bottom)
  - Background video styles
  - Music vs no music

### 2.2 Content Mix Optimization
```python
# Optimal upload schedule (from HA6Bots research + YouTube analytics)
SCHEDULE = {
    "Monday":     "15:00 UTC",   # Back-to-work browsing
    "Tuesday":    "15:00 UTC",
    "Wednesday":  "12:00 UTC",   # Midday break
    "Thursday":   "15:00 UTC",
    "Friday":     "17:00 UTC",   # Pre-weekend
    "Saturday":   "10:00 UTC",   # Weekend morning
    "Sunday":     "10:00 UTC",
}
```

### 2.3 Viral Mechanics for Shorts
- **Hook in first 1.5 seconds**: "You won't believe..." / "Here's why..." / "This is crazy but..."
- **Pacing**: Short sentences. 1 line = 1 caption frame. Fast cuts.
- **CTA**: "Follow for more" / "Like if you agree" at 90% mark
- **Retention hooks**: "Wait till you hear the reply..." mid-video
- **Comment bait**: End with a question

## Phase 3: Monetization (Week 7–12)

### 3.1 Revenue Streams
| Stream | Timeline | Estimate (1M views/mo) |
|--------|----------|----------------------|
| YouTube AdSense | After 10M Shorts views/90d | $100–$300 |
| Affiliate links | Day 1 (in description) | $50–$200 |
| Sponsorships | 10K+ subs | $200–$500/video |
| Merchandise | 50K+ subs | Variable |
| Channel memberships | 30K+ subs | $100–$500/mo |

### 3.2 Analytics Loop
The system should feed data back into content decisions:
- Track which scripts get most retention (via YouTube Studio API)
- Auto-tag high-performing niches
- Prioritize Reddit posts from subreddits with best performance
- Abandon niches with <30% retention

## Advanced: ConsisID Integration (Phase 4, GPU Required)

Once monetization covers GPU costs (≈ $1–2/hr for A100):

```
Replace Pexels background with ConsisID-generated presenter video:
  ┌────────────┐    ┌────────────┐    ┌──────────────┐
  │ Reference  │───▶│  ConsisID  │───▶│ AI Presenter │
  │ Photo      │    │  Pipeline  │    │ Video        │
  └────────────┘    └────────────┘    └──────┬───────┘
                                             │
  ┌────────────┐    ┌────────────┐           │
  │ TTS Script │───▶│ Sync      │───────────▶│
  │            │    │ Audio→Lip │            │
  └────────────┘    └────────────┘            │
                                              ▼
                                     ┌────────────────┐
                                     │ Final Short    │
                                     │ (AI Presenter) │
                                     └────────────────┘
```

## Key Performance Indicators

| Metric | Good | Target | Great |
|--------|------|--------|-------|
| Shorts views/day | 500 | 5,000 | 50,000 |
| Subscriber gain/day | 10 | 100 | 1,000 |
| Uploads/day | 1 | 3 | 6 |
| Script approval rate | 30% | 50% | 70% |
| Average retention | 40% | 55% | 70% |
| Time to monetization | 6 months | 3 months | 6 weeks |

## Automation Checklist

- [ ] Set up .env with API keys
- [ ] Deploy Docker stack (API + Worker + UI)
- [ ] Create YouTube channel + OAuth client_secrets.json
- [ ] Run first Reddit import → review → generate → upload
- [ ] Schedule daily cron for worker (or systemd service)
- [ ] Set up Google Analytics / YouTube Studio monitoring
- [ ] Add 10 Kevin MacLeod tracks to assets/music/
- [ ] Create 5 thumbnail templates
- [ ] Write 10 "evergreen" scripts as backup
- [ ] Auto-post generated shorts to Twitter/Discord for cross-promotion

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-----------|--------|------------|
| YouTube API quota exceeded | High | Medium | Worker auto-pauses; manual upload fallback |
| Reddit API rate limit | Medium | Low | Cache posts locally; rotate subreddits |
| TTS voice gets stale | Medium | High | Rotate voices weekly |
| Content ID claims on music | Low | High | Use only royalty-free music (Kevin MacLeod) |
| AdSense rejection | Medium | High | Follow YouTube policies strictly; no reused content |
| Algorithm change | High | High | Diversify to TikTok/Reels simultaneously |
