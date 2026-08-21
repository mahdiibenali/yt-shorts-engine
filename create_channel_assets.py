#!/usr/bin/env python3
"""
Generate channel assets for SigmaChoices and BrainrotVersus
Profile pictures and banners using Pollinations AI
"""
import requests
import time
from pathlib import Path

# Create assets directory
ASSETS_DIR = Path("data/channel_assets")
ASSETS_DIR.mkdir(exist_ok=True)

def download_asset(prompt, filename, width=800, height=800):
    """Download channel asset from Pollinations"""
    print(f"🎨 Generating {filename}...")
    
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width={width}&height={height}&model=flux&nologo=true"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=120)
            response.raise_for_status()
            
            filepath = ASSETS_DIR / filename
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Downloaded: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(5)
    
    print(f"❌ Failed to generate {filename}")
    return None

def create_channel_assets():
    """Generate all channel assets"""
    
    print("🚀 Creating SigmaChoices Channel Assets...")
    
    # SigmaChoices Profile Picture (800x800)
    sigma_pfp_prompt = "3D render, ultra sigma Chad male face with glowing yellow question marks floating around head, wearing sunglasses, golden aura energy, purple and yellow neon colors, circular logo design, solid dark background, epic lighting, 8k"
    download_asset(sigma_pfp_prompt, "sigmachoices_pfp.jpg", 800, 800)
    
    # SigmaChoices Banner (2560x1440)  
    sigma_banner_prompt = "YouTube banner design, 'SIGMACHOICES' epic text logo, would you rather theme, split screen with glowing choice A and choice B, sigma energy aura, Ohio landscape background, purple gold neon colors, brainrot aesthetic, 2560x1440"
    download_asset(sigma_banner_prompt, "sigmachoices_banner.jpg", 2560, 1440)
    
    print("\n🥊 Creating BrainrotVersus Channel Assets...")
    
    # BrainrotVersus Profile Picture (800x800)
    versus_pfp_prompt = "3D render, epic battle arena logo with 'VS' in the center, surrounded by meme character silhouettes fighting, Ohio energy effects, dramatic lightning, red and blue neon colors, circular design, dark background, 8k"
    download_asset(versus_pfp_prompt, "brainrotversus_pfp.jpg", 800, 800)
    
    # BrainrotVersus Banner (2560x1440)
    versus_banner_prompt = "YouTube banner, 'BRAINROTVERSUS' bold battle text, epic meme character showdown, left vs right split screen, CaseOh vs Skibidi toilet in background, dramatic battle arena, red blue lightning effects, 2560x1440"
    download_asset(versus_banner_prompt, "brainrotversus_banner.jpg", 2560, 1440)
    
    print("\n✅ All channel assets generated!")
    print(f"📁 Assets saved to: {ASSETS_DIR}")
    
    return True

if __name__ == "__main__":
    create_channel_assets()