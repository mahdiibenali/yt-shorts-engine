import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

st.set_page_config(page_title="Channel Dashboard", layout="wide")

st.title("📺 YouTube Shorts Empire Dashboard")

# Connect to database
@st.cache_resource
def get_db_connection():
    db_path = os.path.join('data', 'youtube_journal.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return conn

conn = get_db_connection()

# Load data
def load_data():
    channels_df = pd.read_sql_query("SELECT * FROM channels", conn)
    videos_df = pd.read_sql_query("SELECT * FROM videos", conn)
    return channels_df, videos_df

channels_df, videos_df = load_data()

# Merge for easier analysis if we have videos
if not videos_df.empty and not channels_df.empty:
    merged_df = pd.merge(videos_df, channels_df, left_on='channel_id', right_on='id', suffixes=('_video', '_channel'))
else:
    merged_df = pd.DataFrame()

# Create Tabs for the different concepts
tab1, tab2, tab3, tab4 = st.tabs(["📊 Empire Overview", "🧠 Concept 1: SigmaChoices", "👀 Concept 2: AttentionCooked", "🥊 Concept 3: BrainrotVersus"])

with tab1:
    st.header("Empire Overview")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Channels", len(channels_df))
    col2.metric("Total Videos Posted", len(videos_df[videos_df['status'] == 'Uploaded']) if not videos_df.empty else 0)
    col3.metric("Total Videos Planned/Rendered", len(videos_df[videos_df['status'] != 'Uploaded']) if not videos_df.empty else 0)

    st.markdown("---")

    col_charts1, col_charts2 = st.columns(2)

    with col_charts1:
        st.subheader("Videos by Channel")
        if not merged_df.empty:
            channel_counts = merged_df['name'].value_counts().reset_index()
            channel_counts.columns = ['Channel', 'Video Count']
            fig_pie = px.pie(channel_counts, values='Video Count', names='Channel', hole=0.4, 
                             color_discrete_sequence=px.colors.sequential.Plasma)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No videos logged yet.")

    with col_charts2:
        st.subheader("Video Status Distribution")
        if not videos_df.empty:
            status_counts = videos_df['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            fig_bar = px.bar(status_counts, x='Status', y='Count', color='Status',
                             color_discrete_map={'Uploaded': '#00CC96', 'Rendered': '#FFA15A', 'Draft': '#EF553B'})
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No videos logged yet.")

    st.markdown("---")
    
    st.subheader("Active Channels")
    st.dataframe(
        channels_df[['name', 'handle', 'niche', 'launch_date']], 
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Recent Videos Log")
    if not merged_df.empty:
        display_cols = ['name', 'title', 'topic', 'status', 'upload_date', 'notes']
        st.dataframe(
            merged_df[display_cols].sort_values('upload_date', ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "name": "Channel",
                "title": "Video Title",
                "topic": "Topic",
                "status": "Status",
                "upload_date": "Date",
                "notes": "Notes"
            }
        )
    else:
        st.info("No videos in database yet.")


with tab2:
    st.header("🧠 Concept 1: SigmaChoices (Comment Bait)")
    st.markdown("**Vibe:** Completely absurd dilemmas using pure brainrot slang. Forces people to argue in comments.")
    st.markdown("**Example:** 'Would you rather have infinite rizz BUT stuck in Ohio? OR level ten gyatt BUT hunted by Skibidi Toilet?'")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Planification")
        st.markdown("""
        - **Frequency:** 2 Shorts per day (Morning/Evening)
        - **Format:** Split screen (Top: Visual representation of choices, Bottom: GTA/Subway Surfers)
        - **Audio:** High energy AI voice, tense background music.
        - **CTA:** 'Comment A or B before CaseOh eats your house!'
        """)
    with col2:
        st.subheader("Channel Setup Status")
        st.checkbox("Create Channel: @SigmaChoices", value=False, key="sigma_channel")
        st.checkbox("Generate Profile Picture (Pollinations)", value=False, key="sigma_pfp")
        st.checkbox("Generate Banner", value=False, key="sigma_banner")
        st.checkbox("Write Pipeline Script (run_sigmachoices.py)", value=False, key="sigma_script")


with tab3:
    st.header("👀 Concept 2: AttentionCooked (Maximum Retention)")
    st.markdown("**Vibe:** Interactive challenges forcing viewers to keep watching. 'Don't blink', 'Hold your breath'.")
    st.markdown("**Example:** 'Hold your breath challenge: Brainrot Edition. Breathe in... NOW. Still holding it? Only true sigmas survive.'")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Planification")
        st.markdown("""
        - **Frequency:** 1 Short per day (Peak afternoon)
        - **Format:** Full screen fast-paced visual onslaught. Rapid cuts of meme characters.
        - **Audio:** Countdown timers, intense breathing sounds, sudden loud meme noises.
        - **CTA:** 'Did you pass? Subscribe if you survived.'
        """)
    with col2:
        st.subheader("Channel Setup Status")
        st.checkbox("Create Channel: @AttentionCooked", value=False, key="attention_channel")
        st.checkbox("Generate Profile Picture (Pollinations)", value=False, key="attention_pfp")
        st.checkbox("Generate Banner", value=False, key="attention_banner")
        st.checkbox("Write Pipeline Script (run_attentioncooked.py)", value=False, key="attention_script")


with tab4:
    st.header("🥊 Concept 3: BrainrotVersus (Absurd Powerscaling)")
    st.markdown("**Vibe:** Pitting meme characters against each other with ridiculous stats.")
    st.markdown("**Example:** 'Ohio Final Boss vs CaseOh. Size: CaseOh. Speed: Ohio Boss. Winner: CaseOh uses \"Banned from chat!\"'")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Planification")
        st.markdown("""
        - **Frequency:** 3 Shorts per week (High effort editing)
        - **Format:** Split screen vertical battle style. Left vs Right.
        - **Audio:** Booming anime-style AI announcer, heavy bass impact sound effects.
        - **CTA:** 'Who should fight next? Tell me in the comments!'
        """)
    with col2:
        st.subheader("Channel Setup Status")
        st.checkbox("Create Channel: @BrainrotVersus", value=False, key="versus_channel")
        st.checkbox("Generate Profile Picture (Pollinations)", value=False, key="versus_pfp")
        st.checkbox("Generate Banner", value=False, key="versus_banner")
        st.checkbox("Write Pipeline Script (run_brainrotversus.py)", value=False, key="versus_script")
