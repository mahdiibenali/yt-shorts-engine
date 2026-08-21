import sqlite3
import datetime
import os

DB_PATH = "data/youtube_journal.db"


def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create Channels Table
    c.execute('''
    CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        handle TEXT,
        niche TEXT,
        launch_date DATE
    )
    ''')

    # Create Videos Table
    c.execute('''
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id INTEGER,
        topic TEXT,
        title TEXT,
        status TEXT, -- 'Draft', 'Rendered', 'Uploaded'
        upload_date DATE,
        notes TEXT,
        FOREIGN KEY(channel_id) REFERENCES channels(id)
    )
    ''')
    conn.commit()
    return conn


def add_channel(name, handle, niche):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO channels (name, handle, niche, launch_date) VALUES (?, ?, ?, ?)",
                  (name, handle, niche, datetime.date.today().isoformat()))
        conn.commit()
        print(f"✅ Channel '{name}' added to journal.")
    except sqlite3.IntegrityError:
        print(f"⚠️ Channel '{name}' already exists in database.")
    finally:
        conn.close()


def log_video(channel_name, topic, title, status, upload_date=None, notes=""):
    """Log a video to the journal. Returns the video row id, or None if skipped."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT id FROM channels WHERE name = ?", (channel_name,))
    result = c.fetchone()
    if not result:
        print(f"❌ Error: Channel '{channel_name}' not found.")
        conn.close()
        return None

    channel_id = result[0]

    # Check if a video with the same channel_id and topic already exists
    c.execute("SELECT id, status FROM videos WHERE channel_id = ? AND topic = ?",
              (channel_id, topic))
    existing = c.fetchone()
    if existing:
        print(f"⚠️ Video '{topic}' already exists for '{channel_name}' (id={existing[0]}, status={existing[1]}). Skipping.")
        conn.close()
        return existing[0]

    c.execute("""
        INSERT INTO videos (channel_id, topic, title, status, upload_date, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (channel_id, topic, title, status, upload_date, notes))

    video_id = c.lastrowid
    conn.commit()
    conn.close()
    print(f"✅ Logged Video: '{title}' [{status}]")
    return video_id


def link_to_curiosity(video_name: str, journal_video_id: int):
    """Write the journal video ID into the matching curiosity graph node payload.

    This creates a cross-reference so analytics code can join the two stores
    by looking up ``payload.journal_id`` on any video node.
    """
    try:
        from curiosity.graph import GraphStore
        from curiosity.schema import dumps, loads
        store = GraphStore()
        node = store.find_node("video", video_name)
        if node is None:
            return  # video not yet in graph — will be added when generate_short runs
        payload = dict(node.get("payload") or {})
        if payload.get("journal_id") == journal_video_id:
            return  # already linked
        payload["journal_id"] = journal_video_id
        store.conn.execute(
            "UPDATE nodes SET payload = ? WHERE id = ?",
            (dumps(payload), node["id"]),
        )
        store.conn.commit()
        store.close()
    except Exception as e:
        print(f"⚠️  curiosity link skipped for '{video_name}': {e}")


def cleanup_duplicates():
    """Remove duplicate videos, keeping only the first entry (lowest id) per (channel_id, topic)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Find duplicates: rows whose id is NOT the minimum for their (channel_id, topic) group
    c.execute("""
        DELETE FROM videos
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM videos
            GROUP BY channel_id, topic
        )
    """)
    removed = c.rowcount
    conn.commit()
    conn.close()
    if removed:
        print(f"🧹 Cleaned up {removed} duplicate video(s).")
    else:
        print("✅ No duplicate videos found.")


def update_video_status(channel_name, topic, new_status):
    """Update the status of a video identified by channel name and topic."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT id FROM channels WHERE name = ?", (channel_name,))
    result = c.fetchone()
    if not result:
        print(f"❌ Error: Channel '{channel_name}' not found.")
        conn.close()
        return

    channel_id = result[0]
    c.execute("UPDATE videos SET status = ? WHERE channel_id = ? AND topic = ?",
              (new_status, channel_id, topic))

    if c.rowcount == 0:
        print(f"❌ Error: Video '{topic}' not found for channel '{channel_name}'.")
    else:
        print(f"✅ Updated '{topic}' status to '{new_status}'.")

    conn.commit()
    conn.close()


def get_videos_by_channel(channel_name):
    """Return all videos for a given channel name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT id FROM channels WHERE name = ?", (channel_name,))
    result = c.fetchone()
    if not result:
        print(f"❌ Error: Channel '{channel_name}' not found.")
        conn.close()
        return []

    channel_id = result["id"]
    c.execute("SELECT * FROM videos WHERE channel_id = ? ORDER BY id", (channel_id,))
    videos = [dict(row) for row in c.fetchall()]
    conn.close()
    return videos


if __name__ == "__main__":
    today = datetime.date.today().isoformat()

    # Initialize the database
    init_db()

    # Clean up any duplicate videos
    cleanup_duplicates()

    # Add channels (idempotent — skips if already exists)
    add_channel("WhoDatCritter", "@WhoDatCritter", "Kids Guessing Game (Brainrot/Sludge)")
    add_channel("AttentionCooked", "@AttentionCooked", "Interactive Retention Tests")
    add_channel("SigmaChoices", "@SigmaChoices", "Brainrot Would You Rather")
    add_channel("BrainrotVersus", "@BrainrotVersus", "Meme Character Battles")

    # Log videos for WhoDatCritter (idempotent — skips if channel+topic already exists)
    log_video("WhoDatCritter", "Chameleon",
              "Who dat critter? 🦎👀 (99% FAIL this test!) #shorts",
              "Uploaded", upload_date=today,
              notes="First video! Used Pollinations AI, Edge TTS Ryan, and Subway Surfers split-screen.")
    log_video("WhoDatCritter", "Great White Shark",
              "Who dat critter? 🦈🦷 (99% FAIL this ocean test!) #shorts",
              "Uploaded", upload_date=today,
              notes="Deep sea theme. Uploaded.")
    log_video("WhoDatCritter", "Octopus",
              "Who dat critter? 🐙🧠 (This one has 3 HEARTS!) #shorts",
              "Uploaded", upload_date=today,
              notes="Three hearts, ink ninja, 8 arms with brains. Subway Surfers split.")
    log_video("WhoDatCritter", "Penguin",
              "Who dat critter? 🐧❄️ (Brain Teaser!) #shorts",
              "Uploaded", upload_date=today,
              notes="Coldest continent, torpedo swimmer, belly slide. Subway Surfers split.")
    log_video("WhoDatCritter", "Hummingbird",
              "Who dat critter? 🐦💨 (Fastest wings EVER!) #shorts",
              "Rendered", upload_date=today,
              notes="Hummingbird episode. Rendered and ready.")
    log_video("WhoDatCritter", "Electric Eel",
              "Who dat critter? ⚡🐍 (600 VOLTS of power!) #shorts",
              "Rendered", upload_date=today,
              notes="Electric Eel episode. Rendered and ready.")
    log_video("WhoDatCritter", "Axolotl",
              "Who dat critter? 🦎✨ (It can REGROW its brain!) #shorts",
              "Rendered", upload_date=today,
              notes="Axolotl episode. Rendered and ready.")
    log_video("WhoDatCritter", "Mantis Shrimp",
              "Who dat critter? 🦐👊 (Punches HARDER than a bullet!) #shorts",
              "Rendered", upload_date=today,
              notes="Mantis Shrimp episode. Rendered and ready.")

    # Log videos for AttentionCooked
    log_video("AttentionCooked", "Hold Your Breath",
              "Hold your breath challenge 💀 (99% FAIL) #shorts #brainrot",
              "Uploaded", upload_date=today,
              notes="Generated video for AttentionCooked. Full screen rapid cuts.")
    log_video("AttentionCooked", "Staring Contest",
              "The 60-Second Staring Contest 🗿 (Only Sigmas Win) #shorts #brainrot",
              "Rendered", upload_date=today,
              notes="Progressive psychological pressure. Andrew voice. Yellow captions.")
    log_video("AttentionCooked", "Ocean Hold Breath",
              "Hold Your Breath: Ocean Edition 🌊💀 (99% DROWN) #shorts #brainrot",
              "Rendered", upload_date=today,
              notes="Thalassophobia descent. Christopher voice. Cyan captions. 7 scenes.")

    # Fix statuses for pre-existing videos that may have had stale values
    update_video_status("WhoDatCritter", "Octopus", "Uploaded")
    update_video_status("WhoDatCritter", "Penguin", "Uploaded")
    update_video_status("AttentionCooked", "Hold Your Breath", "Uploaded")
    update_video_status("AttentionCooked", "Staring Contest", "Rendered")
    update_video_status("AttentionCooked", "Ocean Hold Breath", "Rendered")

    # Clean up legacy topic name if it still exists
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM channels WHERE name = ?", ("AttentionCooked",))
    ac = c.fetchone()
    if ac:
        c.execute("DELETE FROM videos WHERE channel_id = ? AND topic = ?",
                  (ac[0], "Hold Your Breath - Brainrot Edition"))
        if c.rowcount:
            print(f"🧹 Removed legacy topic 'Hold Your Breath - Brainrot Edition'.")
    conn.commit()
    conn.close()

    # Print summary
    print("\n" + "=" * 60)
    print("📊 DATABASE SUMMARY")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT * FROM channels ORDER BY id")
    channels = c.fetchall()
    print(f"\n📺 Channels ({len(channels)}):")
    for ch in channels:
        print(f"   [{ch[0]}] {ch[1]} ({ch[2]}) — {ch[3]}")

    c.execute("SELECT COUNT(*) FROM videos")
    total_videos = c.fetchone()[0]
    print(f"\n🎬 Total Videos: {total_videos}")

    for ch in channels:
        c.execute("""
            SELECT topic, status FROM videos
            WHERE channel_id = ? ORDER BY id
        """, (ch[0],))
        videos = c.fetchall()
        if videos:
            print(f"\n   📺 {ch[1]}:")
            for v in videos:
                print(f"      • {v[0]} [{v[1]}]")

    conn.close()
    print("\n" + "=" * 60)
    print("✅ Database is up to date.")
