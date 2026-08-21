"""
Review UI - Streamlit-based Tinder-style swipe interface for script review.

Inspired by HA6Bots' client review system but rebuilt with modern tech.
Run with: streamlit run app/ui/review.py
"""
import os
import sys
import json
import requests
import html as html_module
import streamlit as st
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

API_BASE = os.environ.get("API_BASE", "http://localhost:8000/api")

# --- CUSTOM CSS FOR PREMIUM DARK MODE AESTHETICS ---
UI_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

/* Main App Wrapper */
.stApp {
    font-family: 'Outfit', sans-serif;
    background: linear-gradient(135deg, #09090e 0%, #110d21 50%, #05040a 100%);
    color: #e2e8f0;
}

/* Header styling */
h1 {
    font-weight: 800 !important;
    background: linear-gradient(90deg, #ff3b30 0%, #ff9500 50%, #ffcc00 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -1px;
}

/* Glassmorphism Cards */
.glass-card {
    background: rgba(255, 255, 255, 0.03) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 16px !important;
    padding: 20px !important;
    margin-bottom: 16px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
}

/* Status Badge styling */
.badge {
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
    display: inline-block;
    margin-bottom: 8px;
}
.badge-raw { background: rgba(255, 149, 0, 0.15); color: #ff9500; border: 1px solid rgba(255, 149, 0, 0.3); }
.badge-approved { background: rgba(52, 199, 89, 0.15); color: #34c759; border: 1px solid rgba(52, 199, 89, 0.3); }
.badge-completed { background: rgba(0, 122, 255, 0.15); color: #007aff; border: 1px solid rgba(0, 122, 255, 0.3); }
.badge-failed { background: rgba(255, 59, 48, 0.15); color: #ff3b30; border: 1px solid rgba(255, 59, 48, 0.3); }

/* Buttons styling */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4) !important;
}

/* Offline state box */
.offline-banner {
    padding: 20px;
    border-radius: 12px;
    background: rgba(255, 59, 48, 0.1);
    border: 1px solid rgba(255, 59, 48, 0.3);
    color: #ff8e87;
    margin-bottom: 25px;
}
</style>
"""

# --- ROBUST API WRAPPER WITH ERROR HANDLING ---
def api_request(method, endpoint, **kwargs):
    url = f"{API_BASE}{endpoint}"
    try:
        if method.upper() == "GET":
            resp = requests.get(url, timeout=5.0, **kwargs)
        elif method.upper() == "POST":
            resp = requests.post(url, timeout=5.0, **kwargs)
        elif method.upper() == "PUT":
            resp = requests.put(url, timeout=5.0, **kwargs)
        else:
            return None
        
        if resp.status_code == 200:
            return resp.json()
    except requests.exceptions.RequestException:
        pass
    return None

def get_scripts(status=None):
    endpoint = "/scripts"
    if status:
        endpoint += f"?status={status}"
    data = api_request("GET", endpoint)
    return data.get("scripts", []) if data else []

def get_script(script_id):
    return api_request("GET", f"/scripts/{script_id}")

def update_script(script_id, data):
    endpoint = f"/scripts/{script_id}/review"
    res = api_request("PUT", endpoint, json=data)
    return res is not None

def fetch_reddit(subreddit, limit):
    res = api_request("POST", "/content/reddit", json={
        "subreddit": subreddit,
        "limit": limit,
    })
    return res.get("scripts", []) if res else []


# --- INITIAL SETUP & CONFIG ---
st.set_page_config(page_title="YT Shorts Creator Studio", page_icon="🎥", layout="wide")
st.markdown(UI_STYLE, unsafe_allow_html=True)

# Main Title & Subtitle
st.title("🎥 YT Shorts Creator Studio")
st.markdown("Automate your viral content creation workflow with high-retention composition.")

# Check Server Health Status
health_check = api_request("GET", "/health")
is_online = health_check is not None

if not is_online:
    st.markdown(
        '<div class="offline-banner">'
        '<strong>🔴 REST API Server Offline:</strong> The generator backend could not be reached at '
        f'<code>{API_BASE}</code>.<br>'
        'Please start the API server in your terminal by running: '
        '<code>python run.py server</code>'
        '</div>',
        unsafe_allow_html=True
    )
    if st.button("🔄 Retry Connection"):
        st.rerun()
    st.stop()

# --- ONLINE APPLICATION INTERFACE ---
tab1, tab2, tab3 = st.tabs(["🔥 Review Queue", "📥 Import & Sourcing", "📊 Channel Stats"])

with tab1:
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("📥 Queue")
        st.caption("Review extracted content cards and queue them for final rendering.")
        raw_scripts = get_scripts(status="raw")
        
        for s in raw_scripts:
            # Render a custom glassmorphism card
            with st.container():
                st.markdown(
                    f'<div class="glass-card">'
                    f'<span class="badge badge-raw">RAW</span>'
                    f'<h4>{html_module.escape(s["title"][:75])}...</h4>'
                    f'<p style="font-size:0.85rem; opacity:0.6; margin-top:-8px;">Source: {html_module.escape(s["source"])} | ID: {s["id"][:8]}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                if st.button(f"🔎 Review details", key=f"review_{s['id']}", use_container_width=True):
                    st.session_state["reviewing_id"] = s["id"]
                    st.rerun()

        if not raw_scripts:
            st.info("No scripts awaiting review. Go to the 'Import & Sourcing' tab to fetch Reddit threads or generate scripts.")

    with col2:
        if "reviewing_id" in st.session_state:
            script_id = st.session_state["reviewing_id"]
            script = get_script(script_id)
            if script:
                st.subheader(f"⚡ Live Editor & Curation")
                
                # Editor Forms
                new_title = st.text_input("YouTube Title (Viral Hook)", value=script["title"])
                new_content = st.text_area("Narrator Script (Text read by TTS)", value=script["content"], height=250)
                new_tags = st.text_input("Tags / Keywords (comma-separated)", value=script.get("tags", "") or "")
                
                # Generate defaults
                default_desc = script.get("description", "")
                if not default_desc:
                    default_desc = f"#shorts {new_title}\n\nComment below what you think!"
                new_desc = st.text_area("Video Description", value=default_desc)

                st.markdown("---")
                
                # Tinder-style Choice Row
                col_a, col_b, col_c = st.columns([2, 2, 1])
                with col_a:
                    if st.button("🟢 Approve & Render", type="primary", use_container_width=True):
                        success = update_script(script_id, {
                            "script_id": script_id,
                            "approved": True,
                            "title": new_title,
                            "content": new_content,
                            "tags": new_tags,
                            "description": new_desc,
                        })
                        if success:
                            # Start generating automatically
                            requests.post(f"{API_BASE}/generate/{script_id}", json={"script_id": script_id})
                            st.success("Successfully queued! Background video composer has started rendering.")
                            del st.session_state["reviewing_id"]
                            st.rerun()
                        else:
                            st.error("Failed to update status on server.")
                with col_b:
                    if st.button("🔴 Reject / Skip", use_container_width=True):
                        update_script(script_id, {
                            "script_id": script_id,
                            "approved": False,
                        })
                        del st.session_state["reviewing_id"]
                        st.rerun()
                with col_c:
                    if st.button("Cancel", use_container_width=True):
                        del st.session_state["reviewing_id"]
                        st.rerun()
            else:
                st.error("Script data could not be fetched from API.")
                if st.button("Clear state"):
                    del st.session_state["reviewing_id"]
                    st.rerun()
        else:
            st.markdown(
                '<div style="text-align: center; padding: 50px; opacity: 0.5;">'
                '<h3>👈 Select a script to review details</h3>'
                '<p>Make edits to title, body copy, and tags before sending to rendering worker.</p>'
                '</div>',
                unsafe_allow_html=True
            )

with tab2:
    st.subheader("📥 Reddit Sourcing Engine")
    st.markdown("Import thread topics and reply comments dynamically from hot subreddits.")
    col1, col2 = st.columns(2)
    with col1:
        subreddit = st.text_input("Subreddit (e.g. AskReddit, AmItheAsshole, LifeProTips)", value="AskReddit")
    with col2:
        limit = st.number_input("Threads to scrape", min_value=1, max_value=25, value=5)

    if st.button("🚀 Scrape & Parse Reddit", type="primary"):
        with st.spinner("Accessing Reddit listings and caching comment chains..."):
            results = fetch_reddit(subreddit, limit)
            if results:
                st.success(f"Discovered {len(results)} new qualified script entries in r/{subreddit}!")
                for r in results[:4]:
                    st.markdown(f"- **{r['title'][:80]}** (Author: `u/{r.get('comment_list',[{}])[0].get('author','unknown')}`) - *Ready in Queue*")
            else:
                st.warning("No new unique posts found. They may have already been imported.")

    st.divider()
    
    col_manual, col_ai = st.columns(2)
    with col_manual:
        st.subheader("✍ Create Script Manually")
        with st.form("manual_script_form"):
            title = st.text_input("Short Title / Hook")
            content = st.text_area("TTS Narration Text (Plain script body)", height=150)
            tags = st.text_input("Tags (separated by comma)")
            submitted = st.form_submit_button("Save to Queue")
            if submitted:
                if title and content:
                    resp = requests.post(f"{API_BASE}/scripts", json={
                        "source": "manual",
                        "title": title,
                        "content": content,
                        "tags": tags,
                    })
                    if resp.status_code == 200:
                        st.success("Script saved to database raw queue!")
                    else:
                        st.error("Failed to save manually generated script.")
                else:
                    st.error("Title and Narration are required fields.")

    with col_ai:
        st.subheader("🤖 Generate Script using AI Writer")
        with st.form("ai_script_form"):
            theme = st.text_input("Niche Theme / Idea (e.g. 'Interesting facts about the Titanic')", placeholder="Type prompt...")
            style = st.selectbox("Style / Tone", ["engaging", "mysterious", "funny", "informative"])
            submitted_ai = st.form_submit_button("Generate AI Script")
            if submitted_ai:
                if theme:
                    with st.spinner("AI Script writer is composing high retention text..."):
                        resp = requests.post(f"{API_BASE}/content/ai-script", json={
                            "theme": theme,
                            "style": style
                        })
                        if resp.status_code == 200:
                            data = resp.json()
                            st.success("Generated!")
                            st.text_area("Preview", value=data["content"], height=120)
                            # Create a raw script automatically from it
                            requests.post(f"{API_BASE}/scripts", json={
                                "source": "ai_writer",
                                "title": f"AI: {theme[:50]}",
                                "content": data["content"],
                                "tags": f"ai, {style}, shorts, {theme[:20]}"
                            })
                            st.info("Added to Queue for review.")
                        else:
                            st.error("OpenAI backend is not configured or key is invalid.")
                else:
                    st.error("Theme is required.")

with tab3:
    st.subheader("📊 Pipeline Statistics")
    stats = api_request("GET", "/stats")
    if stats:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Database Scripts", stats["total_scripts"])
        c2.metric("Generating / Queue", stats["pending_generation"])
        c3.metric("Uploaded Videos", stats["uploaded"])
        c4.metric("Failed Processes", stats["failed"])
    
    st.subheader("🎬 Content Libraries")
    completed = get_scripts(status="completed")
    uploaded = get_scripts(status="uploaded")
    generating = get_scripts(status="generating")
    
    all_done = generating + completed + uploaded
    if all_done:
        for s in all_done:
            status_text = s["status"].upper()
            badge_class = "badge-raw"
            if s["status"] == "completed":
                badge_class = "badge-completed"
            elif s["status"] == "uploaded":
                badge_class = "badge-approved"
            elif s["status"] == "generating":
                badge_class = "badge-raw"
            elif s["status"] == "failed":
                badge_class = "badge-failed"
                
            with st.container():
                st.markdown(
                    f'<div class="glass-card">'
                    f'<span class="badge {badge_class}">{status_text}</span>'
                    f'<h4>{html_module.escape(s["title"])}</h4>'
                    f'<p style="font-size:0.85rem; opacity:0.6;">Script ID: {s["id"]} | Created: {s.get("created_at")}</p>'
                    f'</div>',
                    unsafe_allow_html=True
                )
    else:
        st.info("No videos compiled or in progress yet.")
