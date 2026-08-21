#!/usr/bin/env python3
"""
Update video statuses and create upload guide for ready videos
"""
import sqlite3
from datetime import datetime

def update_ready_videos():
    conn = sqlite3.connect('data/youtube_journal.db')
    
    # Get channel IDs
    channels = {row[1]: row[0] for row in conn.execute("SELECT id, name FROM channels").fetchall()}
    
    # Update existing videos to "Ready to Upload" status
    ready_videos = [
        (channels['WhoDatCritter'], 'Octopus', 'Who dat critter? 🐙🧠 (This one has 3 HEARTS!) #shorts', 'Ready'),
        (channels['WhoDatCritter'], 'Penguin', 'Who dat critter? 🐧❄️ (Brain Teaser!) #shorts', 'Ready'),
        (channels['AttentionCooked'], 'Staring Contest', 'The 60-Second Staring Contest 🗿 (Only Sigmas Win) #shorts #brainrot', 'Ready'),
        (channels['AttentionCooked'], 'Ocean Hold Breath', 'Hold Your Breath: Ocean Edition 🌊💀 (99% DROWN) #shorts #brainrot', 'Ready')
    ]
    
    for channel_id, topic, title, status in ready_videos:
        conn.execute("""
            UPDATE videos 
            SET status = ?, title = ?
            WHERE channel_id = ? AND topic = ? AND status = 'Rendered'
        """, (status, title, channel_id, topic))
    
    conn.commit()
    
    # Show current status
    print("=== UPLOAD STATUS ===")
    result = conn.execute("""
        SELECT c.name, v.topic, v.title, v.status 
        FROM videos v 
        JOIN channels c ON v.channel_id = c.id 
        WHERE v.status IN ('Ready', 'Rendered')
        ORDER BY c.name, v.topic
    """).fetchall()
    
    for row in result:
        print(f"{row[0]}: {row[1]} -> {row[3]}")
    
    conn.close()

if __name__ == "__main__":
    update_ready_videos()