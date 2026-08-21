"""Batch video generator — produces multiple shorts across all channels.

Usage:
    python batch_generate.py                    # Generate ALL pending videos
    python batch_generate.py --channel sigma    # Only SigmaChoices
    python batch_generate.py --channel versus   # Only BrainrotVersus
    python batch_generate.py --channel critter  # Only WhoDatCritter
    python batch_generate.py --channel attention # Only AttentionCooked
    python batch_generate.py --channel money      # Only RichRules
    python batch_generate.py --list             # Just list what would be generated
"""

import argparse
import sqlite3
import sys
import os
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from generate_short import run as generate
from journal import init_db, add_channel, log_video, link_to_curiosity
from app.video.shot_library import synthesize_cinematic_prompt

# ──────────────────────────────────────────────────────────────
# Gameplay asset paths (bottom half of split-screen)
# ──────────────────────────────────────────────────────────────
SUBWAY_SURFERS = os.path.join("assets", "subway_surfers.mp4")
GTA_PARKOUR = os.path.join("assets", "gta_parkour.mp4")

# ──────────────────────────────────────────────────────────────
# VIDEO DEFINITIONS — each dict is one video to produce
# ──────────────────────────────────────────────────────────────

SIGMA_CHOICES_VIDEOS = [
    {
        "topic": "Infinite Rizz vs Gyatt",
        "title": "Infinite RIZZ but stuck in Ohio… OR Level 10 Gyatt? 🤔💀 #shorts #brainrot",
        "output": "SIGMA_RIZZ_VS_GYATT.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": GTA_PARKOUR,
        "font_size": 70,
        "highlight_color": (255, 0, 100, 255),
        "caption_position": "center",
        "script": """Would you rather have infinite rizz but you're permanently stuck in Ohio forever?
Or would you pick level ten gyatt but you're being hunted by Skibidi Toilet for the rest of your life?
Think about it. With infinite rizz you could charm anyone, but you're trapped in the most mid state ever.
Or with the gyatt, you'd have insane aura, but Skibidi Toilet is coming for you at three AM every single night.
Drop A for the rizz, drop B for the gyatt. Go! Comment right now before I steal your aura!
Subscribe if you survived this impossible choice!""",
        "prompts": [
            "Hyper-saturated brainrot meme collage, a gigachad silhouette radiating golden rizz energy particles from his body, neon pink and gold lightning bolts, floating heart emojis made of fire, versus symbol in the middle, dark background with matrix rain, drip aesthetic, extremely chaotic dopamine overload, 8k vertical",
            "3D render of a massive glowing Ohio state outline floating in a dark void, surrounded by corn fields that are on fire with neon green flames, a sad gigachad trapped inside looking through glowing bars, midwest wasteland vibe, everything is gray except for neon accents, brainrot aesthetic, 8k vertical",
            "Hyper-detailed 3D render of an enormous glowing purple gyatt energy orb floating in space, radiating concentric shockwaves of neon magenta light, sigma male silhouette standing in front of it absorbing the energy, lens flare, chromatic aberration, overwhelming aura energy, 8k vertical",
            "Chaotic brainrot scene, a massive Skibidi Toilet army charging through a neon-lit city at night, glowing red eyes, each toilet has a different meme face, explosions of confetti and glitch artifacts, a scared stick figure running in the foreground, maximum visual chaos, 8k vertical",
            "Split screen VS battle style graphic, left side shows golden RIZZ text with crown and sparkles, right side shows purple GYATT text with fire and lightning, massive glowing VS symbol in the center, neon explosions, comment section emojis raining down, tournament bracket energy, 8k vertical",
        ],
    },
    {
        "topic": "Ohio Superpowers vs Skibidi Immunity",
        "title": "Ohio Superpowers ⚡ OR Skibidi Immunity? 🚽🛡️ Only REAL Sigmas Choose Right #shorts",
        "output": "SIGMA_OHIO_VS_SKIBIDI.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": GTA_PARKOUR,
        "font_size": 70,
        "highlight_color": (0, 255, 200, 255),
        "caption_position": "center",
        "script": """Would you rather get Ohio superpowers? You can fly, shoot lasers, and summon corn.
But. Every. Single. Person. You meet thinks you're cringe.
Or would you pick total Skibidi Immunity? No toilet can ever touch you.
But you can never listen to music ever again. Complete silence forever.
Ohio powers mean you're basically a superhero nobody respects.
Skibidi immunity means you survive the apocalypse but life has no soundtrack.
Drop A for Ohio powers. Drop B for Skibidi shield. Choose now! Subscribe or I'm taking your phone!""",
        "prompts": [
            "Hyper-vibrant 3D render of a glowing superhero standing on top of a massive corn cob spaceship above Ohio flatlands, shooting neon green laser beams from his eyes, cape made of American flags, extremely dramatic dynamic angle, lens flare overload, meme energy radiating outward, 8k vertical",
            "Brainrot aesthetic, hundreds of people pointing and laughing at a sad superhero in the center, cringe alert neon signs flashing everywhere, floating embarrassment emojis, the superhero is powerful but everyone is roasting him, dark humor energy, neon pink and red lighting, 8k vertical",
            "A massive impenetrable glowing blue force field dome surrounding one person, while an army of Skibidi Toilets crashes against it and explodes into confetti, the person inside looks calm and unbothered, sigma energy, neon cyan shockwaves on impact, dramatic cinematic angle, 8k vertical",
            "A person sitting alone in a massive empty concert hall, every seat is empty, all speakers are broken and silent, a single tear falling in slow motion, the silence is overwhelming, grayscale with only neon blue accents, melancholic but dramatic, 8k vertical",
            "Epic tournament bracket battle screen, left side shows OHIO POWERS with lightning and corn icons, right side shows SKIBIDI SHIELD with toilet and forcefield icons, massive flaming VS in the center, comment emojis raining down, maximum engagement energy, 8k vertical",
        ],
    },
]

BRAINROT_VERSUS_VIDEOS = [
    {
        "topic": "Ohio Final Boss vs CaseOh",
        "title": "Ohio Final Boss VS CaseOh 💀 Who Would ACTUALLY Win? #shorts #brainrot",
        "output": "VERSUS_OHIO_VS_CASEOH.mp4",
        "voice": "en-US-ChristopherNeural",
        "gameplay": GTA_PARKOUR,
        "font_size": 70,
        "highlight_color": (255, 50, 50, 255),
        "caption_position": "center",
        "script": """Ohio Final Boss versus CaseOh. Who wins? Let's break it down.
Ohio Final Boss. Size? Seven feet of pure corn-fed nightmare fuel.
Speed? Faster than your Wi-Fi drops on a school night.
Special ability? Summons an army of possessed tractors.
CaseOh. Size? His gravitational pull has its own zip code.
Speed? He moves at the speed of content. Which is lightning fast.
Special ability? Banned from chat! One word and you're deleted.
And the winner is? CaseOh uses Banned From Chat and Ohio Boss gets ratio'd into the shadow realm!
Who should fight next? Tell me in the comments! Subscribe for more epic battles!""",
        "prompts": [
            "Epic anime-style battle arena, two massive silhouettes facing each other across a glowing neon battlefield, lightning crackling between them, floating VS text made of fire in the center, dramatic low angle camera, tournament bracket aesthetic, hyper-saturated red and blue lighting, 8k vertical",
            "3D render of a terrifying seven-foot tall corn monster hybrid humanoid standing in a burning Ohio cornfield at night, glowing red eyes, wearing overalls, possessed tractors floating behind him, neon green aura, horror boss fight energy, hyper-detailed, 8k vertical",
            "3D render of an impossibly massive round cartoon character sitting on a gaming chair that's cracking under the weight, radiating golden content creator aura, multiple screens floating around showing chat messages, a black hole forming underneath from sheer mass, comedic but epic energy, 8k vertical",
            "Chaotic battle scene, a massive glowing BAN HAMMER slamming down from the sky onto a cornfield, creating a shockwave that sends corn flying everywhere, the word RATIO floating in giant neon red letters, defeated boss dissolving into pixels, victory fireworks, maximum visual chaos, 8k vertical",
            "Winner announcement screen, massive golden WINNER text with confetti explosion, CaseOh character celebrating with a trophy shaped like a BAN button, Ohio Boss fading into shadow realm portal, epic victory music energy, sparkles and lens flares, 8k vertical",
        ],
    },
    {
        "topic": "Sigma Male vs Skibidi Toilet Army",
        "title": "Sigma Male VS Skibidi Toilet Army 🗿🚽 (1 vs 1000) #shorts #brainrot",
        "output": "VERSUS_SIGMA_VS_SKIBIDI.mp4",
        "voice": "en-US-ChristopherNeural",
        "gameplay": GTA_PARKOUR,
        "font_size": 70,
        "highlight_color": (150, 0, 255, 255),
        "caption_position": "center",
        "script": """One Sigma Male versus one thousand Skibidi Toilets. Who survives?
The Sigma Male. Aura level? Over nine thousand. He doesn't even flinch.
His grindset is so powerful it bends reality. He walks through walls.
But the Skibidi Army has numbers. One thousand toilets. All synchronized. All flushing in unison.
Their combined flush creates a vortex that could swallow an entire city.
Round one. The Sigma walks forward. Toilets charge. He puts in one earbud.
The Phonk music activates. Every toilet within fifty meters explodes.
Round two. The remaining toilets combine into one mega toilet.
But the Sigma simply whispers. I don't need validation. The mega toilet has an existential crisis and self-destructs.
Winner? The Sigma Male. Obviously. Subscribe for more impossible battles!""",
        "prompts": [
            "Cinematic anime battle scene, a lone muscular silhouette standing calm in a dark misty arena, glowing purple sigma eyes, one thousand tiny toilet silhouettes visible in the fog rushing forward, dramatic spotlighting, tournament announcement energy, hyper-saturated purple and gold, 8k vertical",
            "Close-up of a gigachad stone face with glowing neon purple eyes staring directly at camera, aura level counter showing 9000+ in glowing red numbers, radiating golden shockwave rings, sigma grindset text floating, stoic unflinching expression, dramatic dark background, 8k vertical",
            "Bird's eye aerial view of exactly one thousand cartoon Skibidi Toilets arranged in a massive army formation on a neon-lit battlefield, all glowing red, creating a synchronized vortex of swirling water in the center, terrifying scale, war aesthetic, 8k vertical",
            "Explosive action scene, a sigma male silhouette walking forward in slow motion with one earbud in, Phonk soundwave visualizer radiating outward from him, toilets exploding into confetti on both sides, neon purple shockwave, maximum cool factor, anime lens flare, 8k vertical",
            "A massive mega toilet made of 500 smaller toilets combined, towering over a city, having an existential crisis with floating thought bubbles showing question marks and sad faces, cracking and self-destructing with golden light beaming out, comedic epic finale, 8k vertical",
        ],
    },
]

ATTENTION_COOKED_VIDEOS = [
    {
        "topic": "Dont Laugh Cringe Edition",
        "title": "Don't Laugh Challenge: CRINGE Edition 😬💀 (Impossible) #shorts #brainrot",
        "output": "ATTENTION_CRINGE.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": None,  # Full screen for this one
        "font_size": 70,
        "highlight_color": (255, 255, 0, 255),
        "caption_position": "center",
        "script": """Don't laugh challenge. Cringe edition. If you laugh, you lose everything.
Ready? Here we go.
Your crush just saw your search history. All of it. Every single page.
Still holding it together? Okay. Try this one.
You accidentally sent your mom a meme that said she's mid.
Getting harder right? Last one. This is the one that breaks everyone.
Your teacher found your TikTok account. And showed it to the entire class.
Three. Two. One.
If you didn't laugh, you are literally not human. Subscribe if you survived this cringe apocalypse!""",
        "prompts": [
            "Extreme close-up of a person desperately trying not to laugh, cheeks inflated like balloons, tears streaming down, face turning bright red, veins popping, dramatic studio lighting against pure black background, hyper-detailed facial expression, comedic tension, 8k vertical",
            "Hyper-dramatic 3D render of a massive glowing phone screen floating in darkness showing a fake browser history with embarrassing searches highlighted in neon red, a horrified face reflection visible in the screen, cringe level meter maxing out, visual panic energy, 8k vertical",
            "A cartoon mom character with fire in her eyes holding a phone showing the word MID in massive neon letters, rage aura radiating outward, the house is shaking, earthquakes cracking the floor, dramatic anime zoom effect, comedic disaster energy, 8k vertical",
            "A classroom full of cartoon students all pointing at one screen and dying of laughter, tears and emojis flying everywhere, the teacher is holding a massive phone showing a TikTok logo, the main character melting into a puddle of embarrassment in the front, maximum cringe energy, 8k vertical",
            "Massive glowing SURVIVED text floating in a victorious explosion of confetti and fireworks, a golden crown descending, sigma aura radiating, trophy made of cringe tears, subscribe button pulsating with neon light, ultimate victory celebration, 8k vertical",
        ],
    },
]

# ──────────────────────────────────────────────────────────────
# WhoDatCritter — kids guessing-game shorts
# ──────────────────────────────────────────────────────────────
CRITTER_VIDEOS = [
    {
        "topic": "Capybara",
        "title": "Who dat critter? 🦫✨ (The CHILLest animal on Earth!) #shorts",
        "output": "CRITTER_CAPYBARA.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "script": """Can you guess which famous animal is the most relaxed creature in the entire universe? Three chill clues!
Clue one! This giant fuzzy friend is so friendly that birds, monkeys, and even ALLIGATORS just hang out with it without attacking!
Clue two! It's the largest rodent on planet Earth! Weighing up to one hundred and forty pounds!
Clue three! It loves taking warm baths with lemons floating on its head!
Did you guess it? Three... Two... One...
It's the CAPYBARA! OK I PULL UP! The ultimate icon of chill vibes! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            synthesize_cinematic_prompt(
                "HOOK_SILHOUETTE",
                "mysterious adorable fuzzy giant rodent silhouette surrounded by gentle steam",
                "lush misty tropical jungle at sunrise, golden light rays filtering through monstera leaves, glowing question mark icon"
            ),
            synthesize_cinematic_prompt(
                "HABITAT_STORY",
                "a relaxed capybara sitting in a natural thermal river",
                "a small cartoon alligator wearing sunglasses and colorful jungle birds resting peacefully beside it on warm river rocks"
            ),
            synthesize_cinematic_prompt(
                "COMPARISON_INFOGRAPHIC",
                "massive friendly capybara standing next to a tiny tiny hamster",
                "clean pastel environmental backdrop with clear scale metrics, zero visual clutter"
            ),
            synthesize_cinematic_prompt(
                "EXTREME_MACRO",
                "close-up of wet capybara snout with water droplets and a bright yellow citrus fruit resting on top",
                "steaming hot spring water, golden hour backlight creating warm rim glow on brown fur"
            ),
            synthesize_cinematic_prompt(
                "HERO_REVEAL",
                "heroic capybara sitting peacefully like a Zen master on a mossy stone under a soft rainbow",
                "pristine DisneyNature landscape background, low angle camera looking up, subtle rim lighting"
            )
        ],
    },
    {
        "topic": "Pistol Shrimp",
        "title": "Who dat critter? 🦐🔊 (LOUDER than a jet engine!) #shorts",
        "output": "CRITTER_PISTOL_SHRIMP.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "script": """Can you guess which tiny sea creature creates a sound LOUDER than a jet engine? Three noisy clues!
Clue one! Snapping its claw shut creates a shockwave bubble that reaches temperatures as hot as the surface of the SUN!
Clue two! The sound of its claw snap reaches two hundred and eighteen decibels! That can stun fish instantly!
Clue three! It's less than two inches long, but loud enough to disrupt navy submarine sonar equipment!
Can you guess it? Three... Two... One...
It's the PISTOL SHRIMP! The noisiest little cowboy in the ocean deep! Subscribe for more mind-blowing creature facts!""",
        "prompts": [
            synthesize_cinematic_prompt(
                "HOOK_SILHOUETTE",
                "mysterious tiny sea creature claw silhouette glowing with cyan energy",
                "deep oceanic abyss, bioluminescent particles floating in blue darkness"
            ),
            synthesize_cinematic_prompt(
                "EXTREME_MACRO",
                "macro high-speed camera shot of an oversized shrimp claw snapping shut",
                "glowing plasma bubble forming underwater with shockwave rings pushing sea water"
            ),
            synthesize_cinematic_prompt(
                "COMPARISON_INFOGRAPHIC",
                "heroic tiny pistol shrimp claw next to a massive jet engine turbine",
                "soundwave decibel gauge hitting red zone 218 dB, high contrast clean graphics"
            ),
            synthesize_cinematic_prompt(
                "OVERHEAD_DRONE",
                "ocean floor perspective of a sleek navy submarine sonar radar screen glowing red",
                "concentric acoustic soundwave ripples expanding outward from a tiny sea reef"
            ),
            synthesize_cinematic_prompt(
                "HERO_REVEAL",
                "heroic bright red pistol shrimp standing proudly on a glowing coral reef",
                "low angle dynamic hero shot, underwater volumetric sunlight rays, National Geographic documentary feel"
            )
        ],
    },
    {
        "topic": "Narwhal",
        "title": "Who dat critter? 🦄🌊 (It has an 8-FOOT UNICORN HORN!) #shorts",
        "output": "CRITTER_NARWHAL.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "script": """Can you guess which ocean creature is known as the UNICORN of the sea? Three magical clues!
Clue one! Its amazing spiral horn is actually a giant TOOTH! And it can grow up to eight feet long, that's as long as a car!
Clue two! It lives in the freezing cold Arctic ocean, where the water is colder than your freezer!
Clue three! That horn is packed with millions of tiny nerves, so it works like a super-sensitive antenna that can feel the water all around it!
Did you guess it? Three... Two... One...
It's the NARWHAL! Sailors long ago believed these magical horns came from real unicorns! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            synthesize_cinematic_prompt(
                "HOOK_SILHOUETTE",
                "mysterious whale-like silhouette rising from dark arctic water with a single long spiral tusk glowing with soft blue light",
                "deep polar ocean at twilight, drifting ice floes, a glowing question mark icon floating above the surface"
            ),
            synthesize_cinematic_prompt(
                "COMPARISON_INFOGRAPHIC",
                "an elegant narwhal tusk standing upright beside a white family car to show how long it grows",
                "clean icy pastel environmental backdrop with clear scale metrics, zero visual clutter"
            ),
            synthesize_cinematic_prompt(
                "OVERHEAD_DRONE",
                "a pod of narwhals swimming through a narrow open breathing hole in a vast frozen arctic sea",
                "majestic geometric ice patterns and deep blue water channels from a high top-down drone view"
            ),
            synthesize_cinematic_prompt(
                "EXTREME_MACRO",
                "ultra close-up of the spiral grooves on a narwhal tusk with delicate glowing nerve strands running through the ivory",
                "cold blue water background with frosty particles, directional polar sunlight catching every ridge"
            ),
            synthesize_cinematic_prompt(
                "HERO_REVEAL",
                "a majestic narwhal breaching out of the arctic water with its long spiral tusk raised toward a glowing aurora sky",
                "golden hour arctic seascape, low angle dynamic hero shot, aurora borealis ribbons, DisneyNature documentary feel"
            )
        ],
    },
    {
        "topic": "Sea Otter",
        "title": "Who dat critter? 🦦🌊 (It holds HANDS while it sleeps!) #shorts",
        "output": "CRITTER_SEA_OTTER.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "sea otter",
        "reveal_search": "Sea otter",
        "script": """Can you guess which furry ocean friend is so cute it holds HANDS while it sleeps? Three fuzzy clues!
Clue one! To keep from drifting away, it sleeps floating on its back and holds paws with its best friend!
Clue two! It's a clever chef with a tool belt! It cracks open clams and sea urchins using a rock as its hammer!
Clue three! It has the thickest fur of any animal on Earth, with up to ONE MILLION hairs in every square inch!
Did you guess it? Three... Two... One...
It's the SEA OTTER! The fluffiest little hand-holder of the Pacific ocean! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            synthesize_cinematic_prompt(
                "HOOK_SILHOUETTE",
                "two mysterious furry sea creature silhouettes floating on their backs holding paws together",
                "calm misty ocean at dawn, kelp fronds in the foreground, a glowing question mark icon in the sky"
            ),
            synthesize_cinematic_prompt(
                "HABITAT_STORY",
                "a fluffy sea otter floating on its back in a lush giant kelp forest",
                "sunbeams piercing emerald green underwater canopy, gentle waves, small fish schooling in the background"
            ),
            synthesize_cinematic_prompt(
                "EXTREME_MACRO",
                "close-up of a sea otter's furry paws cracking open a clam using a smooth grey stone as a hammer",
                "wet fur with glistening water droplets, sunlight sparkle, clean shallow water backdrop"
            ),
            synthesize_cinematic_prompt(
                "COMPARISON_INFOGRAPHIC",
                "a sea otter's ultra-fluffy patch of fur beside a regular dog fur patch showing a million-hair density gauge",
                "clean pastel environmental backdrop with a huge fur-density meter, zero visual clutter"
            ),
            synthesize_cinematic_prompt(
                "HERO_REVEAL",
                "a happy sea otter floating on its back in calm golden water holding its own paws, belly up, relaxed smile",
                "warm golden hour Pacific coastline, low angle hero shot, DisneyNature documentary feel"
            )
        ],
    },
    {
        "topic": "Pangolin",
        "title": "Who dat critter? 🦔🛡️ (The only MAMMAL covered in SCALES!) #shorts",
        "output": "CRITTER_PANGOLIN.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "pangolin",
        "reveal_search": "Pangolin",
        "script": """Can you guess which gentle creature is basically a walking pinecone? Three fuzzy clues!
Clue one! It's the only mammal in the world covered in tough, overlapping scales, just like a pinecone!
Clue two! When danger comes, it rolls into an unbreakable armor ball that even lions can't pry open!
Clue three! Its super sticky tongue is longer than its whole body, perfect for slurping up thousands of ants!
Did you guess it? Three... Two... One...
It's the PANGOLIN! The most trafficked animal on Earth, and our spiky little armor-baller! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            synthesize_cinematic_prompt(
                "HOOK_SILHOUETTE",
                "a mysterious low armored creature silhouette walking across a dirt path at dusk, scales catching the last light",
                "misty jungle at twilight, a glowing question mark icon in the sky"
            ),
            synthesize_cinematic_prompt(
                "HABITAT_STORY",
                "a pangolin calmly sniffing through leaf litter in a savanna woodland",
                "warm golden sunlight filtering through acacia trees, termite mound in the distance"
            ),
            synthesize_cinematic_prompt(
                "EXTREME_MACRO",
                "extreme close-up of a pangolin's diamond-shaped overlapping keratin scales",
                "macro detail, water droplets on glossy scales, soft bokeh background"
            ),
            synthesize_cinematic_prompt(
                "COMPARISON_INFOGRAPHIC",
                "a pangolin rolled into a perfect armored ball beside a cartoon pinecone showing how tough it is",
                "clean pastel infographic backdrop, big ARMOR BALL label, zero visual clutter"
            ),
            synthesize_cinematic_prompt(
                "HERO_REVEAL",
                "a happy pangolin walking proudly across a sunlit termite mound with its long tongue flicking out",
                "warm golden hour, low angle hero shot, DisneyNature documentary feel"
            )
        ],
    },
    {
        "topic": "Red Panda",
        "title": "Who dat critter? 🦊🎋 (It's NOT a panda... and has a fake THUMB!) #shorts",
        "output": "CRITTER_RED_PANDA.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "red panda",
        "reveal_search": "Red panda",
        "script": """Can you guess which fluffy climber is basically a giant living teddy bear? Three fuzzy clues!
Clue one! Even though it's called a panda, it's not a bear at all — it's actually closer to a raccoon!
Clue two! It munches bamboo all day, and it has a special wrist bone that works just like a thumb!
Clue three! It wraps its big striped tail around itself like a cozy blanket while it sleeps!
Did you guess it? Three... Two... One...
It's the RED PANDA! The cutest bamboo-snacking tree acrobat you've ever seen! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            synthesize_cinematic_prompt(
                "HOOK_SILHOUETTE",
                "a fluffy red-orange creature silhouette sitting high on a tree branch munching bamboo",
                "misty mountain forest at dawn, a glowing question mark icon in the sky"
            ),
            synthesize_cinematic_prompt(
                "HABITAT_STORY",
                "a red panda napping curled up in the fork of a tree in a Himalayan bamboo forest",
                "soft morning light, green bamboo leaves, gentle mist"
            ),
            synthesize_cinematic_prompt(
                "EXTREME_MACRO",
                "close-up of a red panda's face with huge amber eyes and a tiny dark nose",
                "extreme macro, fluffy cheek fur, soft forest bokeh"
            ),
            synthesize_cinematic_prompt(
                "COMPARISON_INFOGRAPHIC",
                "a red panda holding bamboo next to a giant panda silhouette showing they are not the same animal",
                "clean pastel infographic backdrop, big NOT A BEAR label, zero visual clutter"
            ),
            synthesize_cinematic_prompt(
                "HERO_REVEAL",
                "a happy red panda sitting on a mossy log waving one paw, fluffy striped tail curled around it",
                "warm golden hour mountain meadow, low angle hero shot, DisneyNature documentary feel"
            )
        ],
    },
    {
        "topic": "Sea Horse",
        "title": "Who dat critter? 🐴🌊 (The DAD has the BABIES!) #shorts",
        "output": "CRITTER_SEA_HORSE.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "sea horse",
        "reveal_search": "Seahorse",
        "script": """Can you guess which tiny ocean dancer has the most surprising family secret of all? Three fuzzy clues!
Clue one! It's the only animal in the world where the DAD carries the babies and gives birth!
Clue two! Its curly tail works like a monkey's, grabbing onto seaweed so it never drifts away!
Clue three! It has NO stomach at all — food passes straight through its tiny tube mouth!
Did you guess it? Three... Two... One...
It's the SEA HORSE! The daddiest dad in the whole ocean! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            synthesize_cinematic_prompt(
                "HOOK_SILHOUETTE",
                "a mysterious tiny curled creature silhouette dancing upright in swaying seagrass, tail spiraled",
                "deep blue twilight ocean, a glowing question mark icon floating in the water"
            ),
            synthesize_cinematic_prompt(
                "HABITAT_STORY",
                "a seahorse gliding upright through a colorful coral reef garden",
                "sunbeams piercing turquoise water, soft current, tiny fish schooling behind"
            ),
            synthesize_cinematic_prompt(
                "EXTREME_MACRO",
                "extreme close-up of a seahorse's crowned head and curly prehensile tail gripping seaweed",
                "macro detail, shimmering iridescent scales, gentle water bokeh"
            ),
            synthesize_cinematic_prompt(
                "COMPARISON_INFOGRAPHIC",
                "a father seahorse releasing tiny baby seahorses beside a confused cartoon dad with an apron",
                "clean pastel infographic backdrop, big DAD GIVES BIRTH label, zero visual clutter"
            ),
            synthesize_cinematic_prompt(
                "HERO_REVEAL",
                "a proud golden seahorse facing the camera with its curly tail anchored, tiny babies swirling around",
                "warm golden hour reef, low angle hero shot, DisneyNature documentary feel"
            )
        ],
    },
    {
        "topic": "Sloth",
        "title": "Who dat critter? 🦥🍃 (It's SO slow, PLANTS grow on it!) #shorts",
        "output": "CRITTER_SLOTH.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "sloth",
        "reveal_search": "Sloth",
        "script": """Can you guess which sleepy tree-hugger is the chillest animal on Earth? Three fuzzy clues!
Clue one! It moves so slowly that tiny algae and plants actually grow in its fur!
Clue two! It can take a whole MONTH to digest just one single leaf!
Clue three! It can hold its breath underwater for longer than a dolphin can!
Did you guess it? Three... Two... One...
It's the SLOTH! The original slow-motion champion! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            synthesize_cinematic_prompt(
                "HOOK_SILHOUETTE",
                "a mysterious fuzzy creature silhouette hanging upside down from a rainforest branch, moving in slow motion",
                "misty green rainforest at dawn, a glowing question mark icon in the canopy"
            ),
            synthesize_cinematic_prompt(
                "HABITAT_STORY",
                "a mysterious fuzzy creature silhouette napping draped over a branch in a lush tropical rainforest, pure dark silhouette with no facial features visible",
                "soft green dappled light, hanging vines, gentle rain mist"
            ),
            synthesize_cinematic_prompt(
                "EXTREME_MACRO",
                "extreme macro close-up of three long curved claws gripping a mossy branch in shadow, algae-tinted fuzzy fur, mysterious, no face visible",
                "macro detail, deep shadow, soft jungle bokeh"
            ),
            synthesize_cinematic_prompt(
                "COMPARISON_INFOGRAPHIC",
                "a mysterious creature silhouette munching a single leaf beside a giant slow-motion hourglass showing one month",
                "clean pastel infographic backdrop, big ONE LEAF A MONTH label, zero visual clutter"
            ),
            synthesize_cinematic_prompt(
                "HERO_REVEAL",
                "a happy sloth hanging from a vine with its long claws hooked, giving a lazy grin",
                "warm golden hour canopy, low angle hero shot, DisneyNature documentary feel"
            )
        ],
    },
    {
        "topic": "Wombat",
        "title": "Who dat critter? 🐻❓ (Its POOP comes out in CUBES!) #shorts",
        "output": "CRITTER_WOMBAT.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "wombat",
        "reveal_search": "Wombat",
        "script": """Can you guess which chunky burrow-builder makes the weirdest poo in the animal kingdom? Three fuzzy clues!
Clue one! It's the only animal whose poop comes out as perfect little CUBES!
Clue two! It has a super hard plate of bone on its bottom, so it uses its butt as armor!
Clue three! Its pouch opens backwards, so dirt doesn't fill it while it digs!
Did you guess it? Three... Two... One...
It's the WOMBAT! The cube-popping, butt-armored digger of Australia! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            synthesize_cinematic_prompt(
                "HOOK_SILHOUETTE",
                "a mysterious chunky furry creature silhouette waddling out of a dirt burrow at dusk",
                "Australian outback at twilight, a glowing question mark icon in the sky"
            ),
            synthesize_cinematic_prompt(
                "HABITAT_STORY",
                "a wombat digging a burrow in golden eucalyptus grassland",
                "warm afternoon light, rolling hills, gum trees in the distance"
            ),
            synthesize_cinematic_prompt(
                "EXTREME_MACRO",
                "close-up of a wombat's sturdy cube-shaped hindquarters and thick furred back",
                "macro detail, coarse fur, soft bushland bokeh"
            ),
            synthesize_cinematic_prompt(
                "COMPARISON_INFOGRAPHIC",
                "a wombat beside a tower of perfect cube-shaped bricks labeled with a huge CUBE POO stamp",
                "clean pastel infographic backdrop, big CUBE POOP label, zero visual clutter"
            ),
            synthesize_cinematic_prompt(
                "HERO_REVEAL",
                "a happy wombat standing proudly at its burrow entrance, front paws tucked, confident grin",
                "warm golden hour outback, low angle hero shot, DisneyNature documentary feel"
            )
        ],
    },
    {
        "topic": "Platypus",
        "title": "Who dat critter? 🦆🦫 (A mammal that LAYS EGGS... and GLOWS!) #shorts",
        "output": "CRITTER_PLATYPUS.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "platypus",
        "reveal_search": "Platypus",
        "script": """Can you guess which animal looks like a science experiment that actually worked? Three fuzzy clues!
Clue one! It's a MAMMAL, but it lays EGGS like a chicken!
Clue two! It has a duck's bill, a beaver's tail, webbed feet, AND it's venomous!
Clue three! Shine a UV light on it, and it GLOWS blue-green in the dark!
Did you guess it? Three... Two... One...
It's the PLATYPUS! Nature's strangest, glowiest mashup! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            synthesize_cinematic_prompt(
                "HOOK_SILHOUETTE",
                "a mysterious duck-billed creature silhouette swimming in a dark river with a glowing question mark reflection",
                "moonlit Australian riverbank, mist, a glowing question mark icon in the night sky"
            ),
            synthesize_cinematic_prompt(
                "HABITAT_STORY",
                "a platypus swimming through clear water in an Australian creek, ripples trailing",
                "golden afternoon light, gum trees overhanging the water, soft current"
            ),
            synthesize_cinematic_prompt(
                "EXTREME_MACRO",
                "extreme close-up of a platypus's leathery duck-like bill and sleek waterproof fur",
                "macro detail, water droplets, soft riverbank bokeh"
            ),
            synthesize_cinematic_prompt(
                "COMPARISON_INFOGRAPHIC",
                "a platypus in the middle of a mashup diagram with a duck bill, beaver tail and webbed feet icons",
                "clean pastel infographic backdrop, big EGG-LAYING MAMMAL label, zero visual clutter"
            ),
            synthesize_cinematic_prompt(
                "HERO_REVEAL",
                "a happy platypus gliding on the water surface at golden hour, glossy fur catching the light",
                "warm golden hour river, low angle hero shot, DisneyNature documentary feel"
            )
        ],
    },
    {
        "topic": "Giraffe",
        "title": "Who dat critter? 🦒🌅 (The TALLEST animal on Earth!) #shorts",
        "output": "CRITTER_GIRAFFE.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "giraffe",
        "reveal_search": "Giraffe",
        "description": "Can you guess the tallest animal on Earth? 🦒\n\nGuess the mystery animal from 3 clues:\n1️⃣ Its neck alone can grow 6.5 feet tall — taller than your whole living room ceiling!\n2️⃣ It only sleeps about 30 minutes a day — and usually standing up!\n3️⃣ Its dark purple tongue is nearly 2 feet long, perfect for grabbing the tastiest leaves high up in the trees!\n\nThink you know it? Drop your guess in the comments before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!\n🔔 Turn on notifications so you never miss a reveal!",
        "tags": "who dat critter, animal guessing game, guess the animal, giraffe, giraffe facts, tallest animal, fun animal facts, animal quiz for kids, kids quiz, animal trivia, educational kids video, safari animals, animals for kids, viral shorts",
        "script": """Can you guess which animal is the tallest on planet Earth? Three tall clues!
Clue one! Its neck alone can grow up to six and a half feet long, taller than your whole living room ceiling!
Clue two! It barely sleeps, only about thirty minutes a day, and it usually sleeps standing up!
Clue three! Its dark purple tongue is nearly two feet long, perfect for grabbing the tastiest leaves high up in the trees!
Did you guess it? Three... Two... One...
It's the GIRAFFE! The tallest spotty skyscraper of the savanna! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low Dutch angle, 35mm wide lens, deep depth of field, a towering dark silhouette with an impossibly long neck rising through golden dawn mist, head lost in the canopy, a faint glowing question mark, strong backlit rim light, warm amber haze, no features visible, mysterious, film grain",
            "Eye-level wide shot, 50mm lens, the dark silhouette of an impossibly long neck rising beside the dark silhouette of a small single-story house on a golden savanna at sunset, both in shadow, no features visible, dramatic height contrast, warm golden backlight, soft atmospheric haze, mysterious mood, film grain",
            "Eye-level shot, 50mm lens, the dark silhouette of a long-legged animal standing asleep in tall golden grass at dusk, head resting low, backlit by a deep orange sky, no features visible, mysterious peaceful mood, cinematic haze, film grain",
            "Extreme close-up, macro lens, the dark silhouette of a long thin ribbon shape reaching up toward fresh green tree leaves, warm golden backlight, pure silhouette with no animal features visible, soft blurry background, cinematic detail, film grain",
            "Low-angle shot, 50mm lens, the majestic dark silhouette of a long-necked animal walking across a golden savanna at sunset, warm rim light tracing its outline, mystery silhouette, no features visible, film grain",
        ],
    },
    {
        "topic": "Cuttlefish",
        "title": "Who dat critter? 🦑🎨 (It has 3 HEARTS and BLUE blood!) #shorts",
        "output": "CRITTER_CUTTLEFISH.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "cuttlefish",
        "reveal_search": "Cuttlefish",
        "description": "Can you guess the ocean's master of disguise? 🦑\n\nGuess the mystery animal from 3 sneaky clues:\n1️⃣ It has THREE hearts and blue-green blood!\n2️⃣ It can change its color, pattern, AND even its skin texture in a split second to blend into the seafloor!\n3️⃣ Its eyes have W-shaped pupils that let it see in front AND behind at the same time!\n\nThink you know it? Drop your guess in the comments before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!\n🔔 Turn on notifications so you never miss a reveal!",
        "tags": "who dat critter, guess the animal, ocean animals, cuttlefish, cuttlefish facts, sea animals for kids, marine animals, fun animal facts, animal quiz for kids, underwater animals, camouflage, animals with 3 hearts, educational kids video, viral shorts",
        "script": """Can you guess which ocean animal is a master of disguise? Three sneaky clues!
Clue one! It has THREE hearts and blue-green blood!
Clue two! It can change its color, pattern, and even its skin texture in a split second to blend into the seafloor!
Clue three! Its eyes have W-shaped pupils that let it see what's happening in front and behind at the same time!
Did you guess it? Three... Two... One...
It's the CUTTLEFISH! The sneakiest shape-shifter of the sea! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key underwater shot, 35mm wide lens, a mysterious oval silhouette with wavy fin edges gliding through dark blue water, bioluminescent particles drifting, a faint glowing question mark, deep ocean twilight, no features visible, cinematic haze, film grain",
            "Wide underwater shot, 50mm lens, the dark silhouette of an oval sea creature gliding through a dark reef at night, three small glowing red heart shapes hovering above it, pure silhouette with no details, bioluminescent glow, sunbeams piercing deep blue water, mysterious mood, film grain",
            "Close-up underwater, 50mm lens, the dark silhouette of an oval sea creature blending into dark sand, its outline rippling with shifting texture, no colors or features visible, deep blue darkness, mysterious camouflage mood, film grain",
            "Extreme macro close-up underwater, a single large dark eye with a faint W-shaped slit pupil glowing in deep black water, surrounded by darkness, no other features visible, mysterious, cinematic detail, film grain",
            "Low-angle underwater shot, the dark silhouette of an oval sea creature with rippling fin edges gliding above a glowing coral reef, volumetric light rays, silhouette only with no features, turquoise darkness, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Axolotl",
        "title": "Who dat critter? 😊🦎 (It NEVER grows up... and can REGROW its brain!) #shorts",
        "output": "CRITTER_AXOLOTL.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "axolotl",
        "reveal_search": "Axolotl",
        "description": "Can you guess the smiling water monster that never grows up? 😊\n\nGuess the mystery animal from 3 clues:\n1️⃣ It stays a BABY its whole life — while other salamanders grow up, it keeps its feathery gills forever!\n2️⃣ It can regrow body parts! Lose a leg, or even part of its heart or brain, and it just grows back!\n3️⃣ It's named after an Aztec god of fire and lightning — and it looks like it's ALWAYS smiling!\n\nThink you know it? Drop your guess in the comments before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!\n🔔 Turn on notifications so you never miss a reveal!",
        "tags": "who dat critter, animal guessing game, guess the animal, axolotl, axolotl facts, axolotl regeneration, mexican salamander, fun animal facts, animal quiz for kids, kids quiz, animal trivia, educational kids video, amphibians, animals for kids, viral shorts",
        "script": """Can you guess which smiling water monster never grows up? Three axolotl-tastic clues!
Clue one! It stays a baby its whole life! While other salamanders grow up, it keeps its feathery gills forever!
Clue two! It can regrow body parts! Lose a leg, or even part of its heart or brain, and it just grows back!
Clue three! It's named after an Aztec god of fire and lightning, and it looks like it's always smiling!
Did you guess it? Three... Two... One...
It's the AXOLOTL! The cutest little science miracle from Mexico! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key underwater shot, 35mm wide lens, a mysterious round-headed creature silhouette with feathery frills drifting in dark water, a faint glowing question mark, deep blue twilight, no features visible, mysterious, cinematic haze, film grain",
            "Side-profile shot, 50mm lens, the dark silhouette of a small frilled creature floating above dark mud at night, beside the taller silhouette of a grown salamander, both pure shadow, no features visible, dramatic contrast, mysterious mood, film grain",
            "Close-up shot, 50mm lens, the dark silhouette of a delicate tail and tiny leg floating in dark water with glowing particles drifting toward the tip, pure silhouette, no features visible, healing glow energy, mysterious mood, film grain",
            "Wide shot, 35mm lens, a small frilled creature silhouette resting on dark volcanic rock with steam rising, a faint glowing light behind it, ancient temple vibes, pure silhouette with no details, mysterious mood, film grain",
            "Low-angle shot, 50mm lens, the majestic dark silhouette of a smiling frilled creature rising above dark water, warm golden backlight, mystery silhouette, no features visible, film grain",
        ],
    },
    {
        "topic": "Octopus",
        "title": "Who dat critter? 🐙🧠 (It has NINE brains and BLUE blood!) #shorts",
        "output": "CRITTER_OCTOPUS.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "octopus",
        "reveal_search": "Octopus",
        "description": "Can you guess the ocean's sneakiest genius? 🐙\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has NINE brains — one main brain plus a mini brain in each of its eight arms!\n2️⃣ It has THREE hearts and BLUE blood!\n3️⃣ It can squeeze through anything bigger than its eyeball, change its color and texture in a flash, and even regrow lost arms!\n\nThink you know it? Drop your guess in the comments before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!\n🔔 Turn on notifications so you never miss a reveal!",
        "tags": "who dat critter, guess the animal, ocean animals, octopus, octopus facts, sea animals for kids, marine animals, smartest sea animal, fun animal facts, animal quiz for kids, underwater animals, animals with 9 brains, educational kids video, viral shorts",
        "script": """Can you guess the ocean's sneakiest genius? Three tentacular clues!
Clue one! It has NINE brains! One main brain, plus a mini brain in each of its eight arms!
Clue two! It has THREE hearts and BLUE blood!
Clue three! It can squeeze through anything bigger than its eyeball, change its color and texture in a flash, and even regrow lost arms!
Did you guess it? Three... Two... One...
It's the OCTOPUS! The eight-armed escape artist of the deep! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key underwater shot, 35mm wide lens, a mysterious eight-armed creature silhouette drifting through dark blue water, arms flowing like ribbons, a faint glowing question mark, bioluminescent particles, no features visible, mysterious, cinematic haze, film grain",
            "Wide underwater shot, 50mm lens, the dark silhouette of a round-headed eight-armed creature hiding inside a rocky crevice, small fish silhouettes swimming past, pure shadow, no details visible, deep blue darkness, mysterious mood, film grain",
            "Close-up underwater, 50mm lens, the dark silhouette of a single long curved arm reaching out of a dark crack, pure silhouette with no features, subtle glow at the tip, mysterious mood, film grain",
            "Split-shot underwater, 35mm lens, the dark silhouette of a compact creature squeezing through a tiny gap in dark coral, only the outline visible, no features, dramatic contrast, mysterious mood, film grain",
            "Low-angle underwater shot, 50mm lens, the majestic dark silhouette of an eight-armed creature gliding above glowing coral, volumetric light rays, silhouette only, turquoise darkness, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Mantis Shrimp",
        "title": "Who dat critter? 🥊🎨 (The PUNCHER that can SEE colors you can't!) #shorts",
        "output": "CRITTER_MANTIS_SHRIMP.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "mantis shrimp",
        "reveal_search": "Mantis shrimp",
        "description": "Can you guess the ocean's flashiest boxer? 🥊\n\nGuess the mystery animal from 3 clues:\n1️⃣ It can PUNCH as fast as a bullet — its strike is so quick it creates tiny flashes of light and heat underwater!\n2️⃣ It has the most amazing eyes in the animal kingdom — it sees colors we can't even imagine!\n3️⃣ It lives in a burrow and hunts like a sneaky little boxer!\n\nThink you know it? Drop your guess in the comments before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!\n🔔 Turn on notifications so you never miss a reveal!",
        "tags": "who dat critter, guess the animal, ocean animals, mantis shrimp, mantis shrimp punch, mantis shrimp eyes, sea creatures for kids, marine animals, amazing animals, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the ocean's flashiest boxer? Three punchy clues!
Clue one! It can punch as fast as a bullet! Its strike is so quick it creates tiny flashes of light and heat underwater!
Clue two! It has the most amazing eyes in the animal kingdom! It sees colors we can't even imagine!
Clue three! It lives in a burrow and hunts like a sneaky little boxer!
Did you guess it? Three... Two... One...
It's the MANTIS SHRIMP! The tiny ocean boxer with super vision! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key underwater shot, 35mm wide lens, the dark silhouette of a compact crustacean with folded pincer claws hovering in dark blue water, a faint glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Close-up underwater, 50mm lens, the dark silhouette of a folded crustacean claw held up like a boxer's fist, pure shadow, no details, dramatic rim light, mysterious mood, film grain",
            "Close-up underwater, 50mm lens, the dark silhouette of a stalked eye staring out from a dark rock burrow, pure silhouette with no features, subtle glow reflections, mysterious mood, film grain",
            "Wide underwater shot, 35mm lens, the dark silhouette of a compact crustacean darting out of a sandy burrow after a small fish, splash of sand particles, no features visible, mysterious mood, film grain",
            "Low-angle underwater shot, 50mm lens, the bold dark silhouette of a crustacean warrior facing the camera with folded claws, golden backlight, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Honey Badger",
        "title": "Who dat critter? 🦡💪 (The SCARIEST little animal on the planet!) #shorts",
        "output": "CRITTER_HONEY_BADGER.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "honey badger",
        "reveal_search": "Honey badger",
        "description": "Can you guess the animal that doesn't care... about ANYTHING? 😤\n\nGuess the mystery animal from 3 clues:\n1️⃣ It's small, but it fights lions and even stands up to giant snakes!\n2️⃣ It has thick, loose skin that makes it super hard to hurt!\n3️⃣ It LOVES honey — and it will raid beehives full of angry bees without fear!\n\nThink you know it? Drop your guess in the comments before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!\n🔔 Turn on notifications so you never miss a reveal!",
        "tags": "who dat critter, guess the animal, honey badger, honey badger don't care, toughest animal, animal facts, fearless animals, african animals, fun animal facts, animal quiz for kids, animal trivia, educational kids video, viral shorts",
        "script": """Can you guess the animal that doesn't care about anything? Three fearless clues!
Clue one! It's small, but it fights lions, and even stands up to giant snakes!
Clue two! It has thick, loose skin that makes it super hard to hurt!
Clue three! It LOVES honey, and it will raid beehives full of angry bees without fear!
Did you guess it? Three... Two... One...
It's the HONEY BADGER! The toughest little animal on Earth! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key shot, 50mm lens, the dark silhouette of a small squat weasel-like creature standing on dark African savanna grass, a faint glowing question mark, night blue tones, no features visible, mysterious, cinematic haze, film grain",
            "Wide shot, 35mm lens, the dark silhouette of a small fearless creature charging toward a much taller dark lion silhouette on the savanna, pure shadows, no details, dramatic tension, mysterious mood, film grain",
            "Close-up shot, 50mm lens, the dark silhouette of a tough little creature with a thick raised back turning away, pure silhouette with no features, warm rim light, mysterious mood, film grain",
            "Wide shot, 35mm lens, the dark silhouette of a small creature bravely raiding a round beehive hanging from a branch, swarm of dark bee specks swirling, no features visible, mysterious mood, film grain",
            "Low-angle shot, 50mm lens, the bold dark silhouette of a small fearless creature standing its ground with raised back, golden backlight, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Fennec Fox",
        "title": "Who dat critter? 🦊👂 (The animal with HUGE ears that lives in the DESERT!) #shorts",
        "output": "CRITTER_FENNEC_FOX.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "fennec fox",
        "reveal_search": "Fennec fox",
        "description": "Can you guess the desert animal with the biggest ears? 🦊\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has HUGE ears — the biggest ears compared to its body size of any animal!\n2️⃣ Its big ears keep it cool in the desert and help it hear prey digging underground!\n3️⃣ It's the world's smallest fox — but it can jump super high!\n\nThink you know it? Drop your guess in the comments before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!\n🔔 Turn on notifications so you never miss a reveal!",
        "tags": "who dat critter, guess the animal, fennec fox, desert animals, foxes, animal ears, cute animals, fox facts, fun animal facts, animal quiz for kids, desert wildlife, educational kids video, viral shorts",
        "script": """Can you guess the desert animal with the biggest ears? Three fuzzy clues!
Clue one! It has HUGE ears! The biggest ears compared to its body size of any animal!
Clue two! Its big ears keep it cool in the desert, and help it hear prey digging underground!
Clue three! It's the world's smallest fox, but it can jump super high!
Did you guess it? Three... Two... One...
It's the FENNEC FOX! The desert's big-eared acrobat! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key shot, 50mm lens, the dark silhouette of a small fox with enormous upright ears standing on desert sand dunes, a faint glowing question mark, dusk purple tones, no features visible, mysterious, cinematic haze, film grain",
            "Close-up shot, 50mm lens, the dark silhouette of a huge fox ear against a glowing desert moon, pure silhouette with no details, warm rim light, mysterious mood, film grain",
            "Wide shot, 35mm lens, the dark silhouette of a small big-eared fox leaping high over a desert dune, kicked sand particles trailing, no features visible, mysterious mood, film grain",
            "Wide shot, 50mm lens, the dark silhouette of a big-eared fox standing perfectly still above a dune, listening, another small dark creature burrowing below, no features visible, mysterious mood, film grain",
            "Low-angle shot, 50mm lens, the majestic dark silhouette of a big-eared fox on a dune ridge against the setting sun, silhouette only, no features, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Koala",
        "title": "Who dat critter? 🐨😴 (The animal that sleeps 20 hours a day!) #shorts",
        "output": "CRITTER_KOALA.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "koala",
        "reveal_search": "Koala",
        "description": "Can you guess the super sleepy tree cuddler? 🐨\n\nGuess the mystery animal from 3 clues:\n1️⃣ It sleeps up to 20 hours a day — it's one of the sleepiest animals ever!\n2️⃣ It only eats one food, and that food has a funny name!\n3️⃣ It carries its baby in a pouch and hugs trees to stay cool!\n\nThink you know it? Drop your guess in the comments before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!\n🔔 Turn on notifications so you never miss a reveal!",
        "tags": "who dat critter, guess the animal, koala, koala facts, sleepy animals, australian animals, marsupials, cute animals, fun animal facts, animal quiz for kids, animal trivia, educational kids video, viral shorts",
        "script": """Can you guess the super sleepy tree cuddler? Three dozy clues!
Clue one! It sleeps up to twenty hours a day! One of the sleepiest animals ever!
Clue two! It only eats one food, and that food has a funny name!
Clue three! It carries its baby in a pouch, and hugs trees to stay cool!
Did you guess it? Three... Two... One...
It's the KOALA! Australia's cuddly, sleepy leaf lover! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key shot, 50mm lens, the dark silhouette of a round fuzzy animal with big ears perched high in a eucalyptus tree, a faint glowing question mark, night teal tones, no features visible, mysterious, cinematic haze, film grain",
            "Close-up shot, 50mm lens, the dark silhouette of a fuzzy round ear and the back of a round head snuggled against a tree branch, pure silhouette, no details, warm rim light, mysterious mood, film grain",
            "Wide shot, 35mm lens, the dark silhouette of a round fuzzy animal dozing curled up in the fork of a tall tree, leaves swaying gently, no features visible, mysterious mood, film grain",
            "Close-up shot, 50mm lens, the dark silhouette of a fuzzy paw reaching up to pluck a leaf from a eucalyptus branch, pure silhouette with no details, mysterious mood, film grain",
            "Low-angle shot, 50mm lens, the calm dark silhouette of a round fuzzy animal resting against a tree trunk hugging the trunk, golden backlight through leaves, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Kiwi Bird",
        "title": "Who dat critter? 🥝🐦 (The bird that CAN'T fly and has a BEAK like a needle!) #shorts",
        "output": "CRITTER_KIWI_BIRD.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "kiwi",
        "reveal_search": "Kiwi (bird)",
        "description": "Can you guess the round bird with no wings? 🥝\n\nGuess the mystery animal from 3 clues:\n1️⃣ It's a bird that CAN'T fly — it has tiny wings hidden under its fluffy feathers!\n2️⃣ It has a long, thin beak with nostrils at the TIP, so it can sniff out food underground!\n3️⃣ It's from New Zealand, and it's named after a fruit!\n\nThink you know it? Drop your guess in the comments before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!\n🔔 Turn on notifications so you never miss a reveal!",
        "tags": "who dat critter, guess the animal, kiwi bird, birds that can't fly, new zealand animals, kiwi facts, flightless birds, fun animal facts, animal quiz for kids, bird facts for kids, animal trivia, educational kids video, viral shorts",
        "script": """Can you guess the round bird with no wings? Three feathery clues!
Clue one! It's a bird that CAN'T fly! It has tiny wings hidden under its fluffy feathers!
Clue two! It has a long thin beak with nostrils at the tip, so it can sniff out food underground!
Clue three! It's from New Zealand, and it's named after a fruit!
Did you guess it? Three... Two... One...
It's the KIWI! New Zealand's adorable night bird! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key shot, 50mm lens, the dark silhouette of a round fuzzy flightless bird with a long thin beak probing dark forest floor leaves, a faint glowing question mark, night forest tones, no features visible, mysterious, cinematic haze, film grain",
            "Close-up shot, 50mm lens, the dark silhouette of a long curved beak tip sniffing among dark ferns, pure silhouette, no details, mysterious mood, film grain",
            "Wide shot, 35mm lens, the dark silhouette of a round fuzzy bird scurrying through dark fern forest at night, mossy logs, no features visible, mysterious mood, film grain",
            "Close-up shot, 50mm lens, the dark silhouette of a fluffy round body with tiny hidden wing stubs, pure silhouette with no features, warm rim light, mysterious mood, film grain",
            "Low-angle shot, 50mm lens, the proud dark silhouette of a round flightless bird standing in a moonlit forest clearing, golden rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Blobfish",
        "title": "Who dat critter? 😮🫧 (The famous funny fish that lives REALLY deep!) #shorts",
        "output": "CRITTER_BLOBFISH.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "blobfish",
        "reveal_search": "Blobfish",
        "description": "Can you guess the internet's favorite funny fish? 😮\n\nGuess the mystery animal from 3 clues:\n1️⃣ It's famous for its funny, droopy face!\n2️⃣ It lives SO deep in the ocean, where the water pressure is crushing!\n3️⃣ It doesn't swim much at all — it just floats along, waiting for food to drift by!\n\nThink you know it? Drop your guess in the comments before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!\n🔔 Turn on notifications so you never miss a reveal!",
        "tags": "who dat critter, guess the animal, blobfish, blobfish facts, weird animals, deep sea creatures, funny fish, ocean animals, deep sea animals, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the internet's favorite funny fish? Three deep-sea clues!
Clue one! It's famous for its funny, droopy face!
Clue two! It lives SO deep in the ocean, where the water pressure is crushing!
Clue three! It doesn't swim much at all! It just floats along, waiting for food to drift by!
Did you guess it? Three... Two... One...
It's the BLOBFISH! The deep sea's famous grumpy blob! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key underwater shot, 50mm lens, the dark silhouette of a round jelly-like blob creature drifting in the pitch-dark deep ocean, a faint glowing question mark, deep blue-black tones, no features visible, mysterious, cinematic haze, film grain",
            "Wide underwater shot, 50mm lens, the dark silhouette of a round blobby creature floating weightlessly above a dark seabed, tiny glowing particles around, no features visible, mysterious mood, film grain",
            "Close-up underwater, 50mm lens, the dark silhouette of a round squishy head with a droopy downturned mouth drifting in darkness, pure silhouette with no details, mysterious mood, film grain",
            "Wide underwater shot, 35mm lens, the dark silhouette of a round blob creature bobbing slowly among dark rocks and drifting snow-like particles, no features visible, mysterious mood, film grain",
            "Low-angle underwater shot, 50mm lens, the comical dark silhouette of a round droopy blob creature hanging in the dark abyss, warm golden backlight from above, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Electric Eel",
        "title": "Who dat critter? ⚡🐍 (The animal that SHOCKS like a TASER!) #shorts",
        "output": "CRITTER_ELECTRIC_EEL.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "electric eel",
        "reveal_search": "Electric eel",
        "description": "Can you guess the river monster with a SUPERPOWER? ⚡\n\nGuess the mystery animal from 3 clues:\n1️⃣ It can make ELECTRICITY — enough to light up Christmas tree lights!\n2️⃣ It's not a true eel — it's actually related to fish like carp!\n3️⃣ It lives in murky South American rivers and hunts using its electric powers!\n\nThink you know it? Drop your guess in the comments before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!\n🔔 Turn on notifications so you never miss a reveal!",
        "tags": "who dat critter, guess the animal, electric eel, electric eel facts, electric animals, river animals, amazon animals, animals with superpowers, fun animal facts, animal quiz for kids, animal trivia, educational kids video, viral shorts",
        "script": """Can you guess the river monster with a superpower? Three shocking clues!
Clue one! It can make ELECTRICITY! Enough to light up Christmas tree lights!
Clue two! It's not a true eel! It's actually related to fish like carp!
Clue three! It lives in murky South American rivers, and hunts using its electric powers!
Did you guess it? Three... Two... One...
It's the ELECTRIC EEL! The river's living battery! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key underwater shot, 50mm lens, the dark silhouette of a long snake-like fish gliding through murky green-brown river water, a faint glowing question mark, lightning-like cracks of light around it, no features visible, mysterious, cinematic haze, film grain",
            "Wide underwater shot, 50mm lens, the dark silhouette of a long snake-like fish with small glowing electric arcs flickering around its tail, dark murky water, no features visible, mysterious mood, film grain",
            "Close-up underwater, 50mm lens, the dark silhouette of a long snakelike head drifting in dark water with electric sparks crackling around it, pure silhouette with no details, mysterious mood, film grain",
            "Wide underwater shot, 35mm lens, the dark silhouette of a long creature coiling through dark flooded forest roots, small blue glows pulsing, no features visible, mysterious mood, film grain",
            "Low-angle underwater shot, 50mm lens, the powerful dark silhouette of a long snake-like fish rising from murky water, golden rim light with electric sparks, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Peregrine Falcon",
        "title": "Who dat critter? 🦅💨 (The FASTEST animal on Earth — it dives at 390 KM/H!) #shorts",
        "output": "CRITTER_PEREGRINE_FALCON.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "peregrine falcon",
        "reveal_search": "Peregrine falcon",
        "description": "Can you guess the fastest animal in the world? 🦅\n\nGuess the mystery animal from 3 clues:\n1️⃣ It's the FASTEST animal on Earth — it can dive at over 390 kilometres per hour!\n2️⃣ It's a bird of prey, and it catches other birds mid-air!\n3️⃣ It has special notches in its beak and lives on every continent except Antarctica!\n\nThink you know it? Drop your guess in the comments before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!\n🔔 Turn on notifications so you never miss a reveal!",
        "tags": "who dat critter, guess the animal, peregrine falcon, fastest animal, fastest bird, birds of prey, falcon facts, speed animals, fun animal facts, animal quiz for kids, bird facts for kids, educational kids video, viral shorts",
        "script": """Can you guess the fastest animal in the world? Three speedy clues!
Clue one! It's the FASTEST animal on Earth! It can dive at over three hundred and ninety kilometres per hour!
Clue two! It's a bird of prey, and it catches other birds mid-air!
Clue three! It has special notches in its beak, and lives on every continent except Antarctica!
Did you guess it? Three... Two... One...
It's the PEREGRINE FALCON! The fastest animal on the planet! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key shot, 50mm lens, the dark silhouette of a sleek bird with folded wings plummeting straight down through grey-blue sky, a faint glowing question mark, speed streaks behind it, no features visible, mysterious, cinematic haze, film grain",
            "Wide shot, 35mm lens, the dark silhouette of a diving bird plunging toward a smaller dark bird silhouette far below, motion blur, stormy sky, no features visible, mysterious mood, film grain",
            "Close-up shot, 50mm lens, the dark silhouette of a hooked beak and streamlined head in mid-dive, pure silhouette, no details, dramatic rim light, mysterious mood, film grain",
            "Wide shot, 35mm lens, the dark silhouette of a perched sleek bird on a cliff ledge above clouds, city lights faint below, no features visible, mysterious mood, film grain",
            "Low-angle shot, 50mm lens, the majestic dark silhouette of a bird with swept-back wings soaring across the setting sun, golden rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Archerfish",
        "title": "Who dat critter? 🐟💦 (The SNIPER that shoots water to hunt!) #shorts",
        "output": "CRITTER_ARCHERFISH.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "archerfish",
        "reveal_search": "Archerfish",
        "description": "Can you guess the fish with a SNIPER skill? 🐟\n\nGuess the mystery animal from 3 clues:\n1️⃣ It shoots SPITS OF WATER from its mouth to knock bugs off leaves above the water!\n2️⃣ It can learn from watching other fish do it!\n3️⃣ It lives in mangrove forests and even shoots at prey far above the surface!\n\nThink you know it? Drop your guess in the comments before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!\n🔔 Turn on notifications so you never miss a reveal!",
        "tags": "who dat critter, guess the animal, archerfish, fish facts, cool fish, mangrove animals, fish that shoot water, amazing animals, fun animal facts, animal quiz for kids, animal trivia, educational kids video, viral shorts",
        "script": """Can you guess the fish with a sniper skill? Three splashy clues!
Clue one! It shoots SPITS OF WATER from its mouth, to knock bugs off leaves above the water!
Clue two! It can learn from watching other fish do it!
Clue three! It lives in mangrove forests, and even shoots at prey far above the surface!
Did you guess it? Three... Two... One...
It's the ARCHERFISH! The jungle river's water sniper! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key underwater shot, 50mm lens, the dark silhouette of a sleek fish near the water surface aiming upward, a faint glowing question mark, hanging mangrove roots, no features visible, mysterious, cinematic haze, film grain",
            "Wide shot, 50mm lens, the dark silhouette of a fish sending a thin jet of water up toward a leaf with a bug silhouette, droplets sparkling, no features visible, mysterious mood, film grain",
            "Close-up underwater, 50mm lens, the dark silhouette of a fish face breaking the surface with a raised mouth, a small water drop arc above, pure silhouette with no details, mysterious mood, film grain",
            "Wide underwater shot, 35mm lens, the dark silhouette of a school of sleek fish gliding among mangrove roots, shafts of moonlight through the water, no features visible, mysterious mood, film grain",
            "Low-angle underwater shot, 50mm lens, the proud dark silhouette of a sleek fish holding still at the surface aiming upward, golden sun backlight through water, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Dung Beetle",
        "title": "Who dat critter? 🪲💪 (The strongest animal... that LOVES poop!) #shorts",
        "output": "CRITTER_DUNG_BEETLE.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "dung beetle",
        "reveal_search": "Dung beetle",
        "description": "Can you guess the super-strong insect with a funny secret? 🪲\n\nGuess the mystery animal from 3 clues:\n1️⃣ It's the STRONGEST animal for its size — it can pull over 1,100 times its own body weight!\n2️⃣ It rolls something round along the ground... and it has a VERY funny smell!\n3️⃣ It uses the stars and the Milky Way to find its way home!\n\nThink you know it? Drop your guess in the comments before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!\n🔔 Turn on notifications so you never miss a reveal!",
        "tags": "who dat critter, guess the animal, dung beetle, dung beetle facts, strongest animal, insects for kids, beetle facts, amazing insects, funny animal facts, animal quiz for kids, insect trivia, educational kids video, viral shorts",
        "script": """Can you guess the super-strong insect with a funny secret? Three powerful clues!
Clue one! It's the STRONGEST animal for its size! It can pull over one thousand one hundred times its own body weight!
Clue two! It rolls something round along the ground, and it has a very funny smell!
Clue three! It uses the stars and the Milky Way to find its way home!
Did you guess it? Three... Two... One...
It's the DUNG BEETLE! The tiny super-strong star navigator! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key shot, 50mm lens, the dark silhouette of a small round beetle rolling a round ball across dark savanna earth at night, a faint glowing question mark, starry sky, no features visible, mysterious, cinematic haze, film grain",
            "Wide shot, 35mm lens, the dark silhouette of a tiny beetle pushing a round ball as big as itself over a small ridge, kicked dirt particles, night sky with the Milky Way, no features visible, mysterious mood, film grain",
            "Close-up shot, 50mm lens, the dark silhouette of a small beetle straining with raised front legs against a round ball, pure silhouette, no details, dramatic rim light, mysterious mood, film grain",
            "Wide shot, 35mm lens, the dark silhouette of a round ball rolling on its own down a slope at night, tiny beetle following, moonlight, no features visible, mysterious mood, film grain",
            "Low-angle shot, 50mm lens, the heroic dark silhouette of a tiny beetle lifting a round ball high against the glowing Milky Way, golden rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Leafy Sea Dragon",
        "title": "Who dat critter? 🌿🐉 (The animal that looks like a DRAGON made of LEAVES!) #shorts",
        "output": "CRITTER_LEAFY_SEA_DRAGON.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "leafy sea dragon",
        "reveal_search": "Leafy seadragon",
        "description": "Can you guess the magical leaf dragon of the sea? 🌿\n\nGuess the mystery animal from 3 clues:\n1️⃣ It looks like a DRAGON made of floating leaves!\n2️⃣ Its leaf-like parts are NOT for swimming — they're camouflage to hide from predators!\n3️⃣ In its family, it's the DADDY who carries and looks after the eggs!\n\nThink you know it? Drop your guess in the comments before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!\n🔔 Turn on notifications so you never miss a reveal!",
        "tags": "who dat critter, guess the animal, leafy sea dragon, sea dragon, ocean animals, seahorse family, camouflage animals, weird sea creatures, fun animal facts, animal quiz for kids, sea animal facts, educational kids video, viral shorts",
        "script": """Can you guess the magical leaf dragon of the sea? Three hidden clues!
Clue one! It looks like a DRAGON made of floating leaves!
Clue two! Its leaf-like parts are NOT for swimming! They're camouflage to hide from predators!
Clue three! In its family, it's the DADDY who carries and looks after the eggs!
Did you guess it? Three... Two... One...
It's the LEAFY SEA DRAGON! The ocean's living leaf dragon! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key underwater shot, 50mm lens, the dark silhouette of a delicate leaf-covered dragon-like creature drifting through dark kelp forest water, a faint glowing question mark, drifting leaf particles, no features visible, mysterious, cinematic haze, film grain",
            "Wide underwater shot, 50mm lens, the dark silhouette of a leaf-covered creature hidden among swaying dark seaweed, nearly invisible, no features visible, mysterious mood, film grain",
            "Close-up underwater, 50mm lens, the dark silhouette of a horse-like snout and flowing leafy frills drifting in dark water, pure silhouette with no details, mysterious mood, film grain",
            "Wide underwater shot, 35mm lens, the dark silhouette of a leafy creature gliding gracefully past a cluster of dark rocks and kelp, soft glow above, no features visible, mysterious mood, film grain",
            "Low-angle underwater shot, 50mm lens, the regal dark silhouette of a leaf-dragon rising through sunlit emerald water, golden light rays, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Mimic Octopus",
        "title": "Who dat critter? 🐙🎭 (It PRETENDS to be other animals!) #shorts",
        "output": "CRITTER_MIMIC_OCTOPUS.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "mimic octopus",
        "reveal_search": "Mimic octopus",
        "description": "Can you guess the master of disguise? 🎭\n\nGuess the mystery animal from 3 clues:\n1️⃣ It can SHAPESHIFT to look like a lionfish, flatfish, and sea snake!\n2️⃣ It lives on the sandy seafloor of Southeast Asia!\n3️⃣ It has EIGHT arms and THREE hearts!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, guess the animal, mimic octopus, octopus facts, shapeshifter animal, ocean animals, weird sea creatures, animal disguise, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the ocean's master of disguise? Three sneaky clues!
Clue one! This incredible creature can shapeshift its body to look like a lionfish, a flatfish, AND a sea snake!
Clue two! It lives on sandy seafloors in Southeast Asia and uses disguise to trick predators!
Clue three! It has eight arms, three hearts, and is so smart it learns new disguises by WATCHING other animals!
Did you guess it? Three... Two... One...
It's the MIMIC OCTOPUS! The ocean's greatest actor! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key underwater shot, 50mm lens, the dark silhouette of a flat eight-armed creature pressed against sandy seafloor, a faint glowing question mark, sand particles drifting, no features visible, mysterious, cinematic haze, film grain",
            "Wide underwater shot, 35mm lens, the dark silhouette of a tentacled creature spreading its arms wide mimicking a flatfish shape, dark sandy bottom, no features visible, mysterious mood, film grain",
            "Close-up underwater, 50mm lens, the dark silhouette of curling tentacles arranged like venomous spines around a central body, pure silhouette no details, mysterious mood, film grain",
            "Wide underwater shot, 35mm lens, the dark silhouette of a long-armed creature slithering in an S-shape mimicking a sea snake, dark water, no features visible, mysterious mood, film grain",
            "Low-angle underwater shot, 50mm lens, the dark silhouette of an eight-armed creature rising from the sand with arms spread dramatically, golden light rays above, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Tardigrade",
        "title": "Who dat critter? 🐻‍❄️💀 (It can SURVIVE in OUTER SPACE!) #shorts",
        "output": "CRITTER_TARDIGRADE.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "tardigrade",
        "reveal_search": "Tardigrade",
        "description": "Can you guess the world's toughest animal? 💀\n\nGuess the mystery animal from 3 clues:\n1️⃣ It can survive in OUTER SPACE with no suit!\n2️⃣ It's also called a WATER BEAR and is microscopic!\n3️⃣ It can live for 30 YEARS with no food or water!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, guess the animal, tardigrade, water bear, toughest animal, microscopic animals, space survival, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the world's toughest living thing? Three incredible clues!
Clue one! This tiny creature can survive in the vacuum of OUTER SPACE with no suit, no oxygen, and no protection!
Clue two! It's microscopic, has eight stubby legs, and is nicknamed the WATER BEAR because of how it walks!
Clue three! When things get dangerous, it shuts its whole body down and can survive for THIRTY YEARS with no food or water!
Did you guess it? Three... Two... One...
It's the TARDIGRADE! Earth's most indestructible creature! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Extreme macro shot, 100mm lens, the dark microscopic silhouette of a tiny eight-legged chubby creature on a glass slide, a glowing question mark, electron microscope aesthetic, pure darkness background, no features visible, mysterious, film grain",
            "Wide macro shot, the dark silhouette of a fat eight-legged creature curled into a survival ball in the vacuum of space, stars behind, no features visible, mysterious mood, film grain",
            "Close-up macro, the dark silhouette of eight stubby legs walking slowly on moss fibres, pure silhouette no details, cinematic microscope light, mysterious mood, film grain",
            "Wide macro shot, the dark silhouette of a tiny barrel-shaped creature surrounded by ice crystals in darkness, pure silhouette no features, mysterious mood, film grain",
            "Dramatic macro shot, the dark silhouette of a tiny creature standing on a planet surface with stars and Earth visible behind, golden rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Bombardier Beetle",
        "title": "Who dat critter? 🪲💥 (It SHOOTS boiling chemicals from its BUTT!) #shorts",
        "output": "CRITTER_BOMBARDIER_BEETLE.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "bombardier beetle",
        "reveal_search": "Bombardier beetle",
        "description": "Can you guess the exploding beetle? 💥\n\nGuess the mystery animal from 3 clues:\n1️⃣ It shoots boiling hot chemicals from its body at 100°C!\n2️⃣ It can fire up to 500 BLASTS per second at enemies!\n3️⃣ It mixes two chemicals inside its body to create a tiny EXPLOSION!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, guess the animal, bombardier beetle, exploding beetle, beetle facts, insect defense, chemical explosion, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the insect that carries a chemical weapon? Three explosive clues!
Clue one! This tiny insect can shoot boiling hot liquid at one hundred degrees Celsius from its own body!
Clue two! It fires up to FIVE HUNDRED blasts per second, making a popping sound like a tiny machine gun!
Clue three! It mixes two different chemicals inside special chambers in its abdomen to create a controlled EXPLOSION!
Did you guess it? Three... Two... One...
It's the BOMBARDIER BEETLE! Nature's tiniest bomb squad! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key macro shot, 50mm lens, the dark silhouette of a round beetle on dark forest floor, a glowing question mark, mysterious smoke wisps, no features visible, mysterious, cinematic haze, film grain",
            "Close-up macro, the dark silhouette of a beetle with its abdomen raised and a tiny explosion blast shooting outward, pure silhouette no details, dramatic backlight, mysterious mood, film grain",
            "Wide macro shot, the dark silhouette of a beetle standing defensively with a tiny puff of smoke behind it, dark ground, no features visible, mysterious mood, film grain",
            "Close-up macro, the dark silhouette of a beetle's abdomen with two tiny chamber openings, chemical reaction sparks, pure silhouette, mysterious mood, film grain",
            "Low-angle macro shot, the heroic dark silhouette of a beetle firing a dramatic explosion blast at a shadow predator, golden backlight, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Aye-Aye",
        "title": "Who dat critter? 🖕🌙 (Its MIDDLE FINGER is THREE TIMES longer than the rest!) #shorts",
        "output": "CRITTER_AYE_AYE.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "aye-aye",
        "reveal_search": "Aye-aye",
        "description": "Can you guess the creepiest primate? 🌙\n\nGuess the mystery animal from 3 clues:\n1️⃣ Its middle finger is THREE TIMES longer than its other fingers!\n2️⃣ It uses that long finger to tap on trees and find bugs by SOUND!\n3️⃣ It only lives on the island of Madagascar!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, guess the animal, aye-aye, madagascar animal, weird primate, long finger animal, nocturnal animals, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the world's weirdest-looking primate? Three bizarre clues!
Clue one! This creature has a middle finger that is THREE TIMES longer than its other fingers!
Clue two! It uses that freakishly long finger to tap on tree bark and listen for hollow spots where bugs are hiding!
Clue three! It only lives on one island in the world and many locals there consider it a bad omen!
Did you guess it? Three... Two... One...
It's the AYE-AYE! Madagascar's most mysterious creature! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key night shot, 50mm lens, the dark silhouette of a large-eared creature clinging to a tree branch at night, a glowing question mark, moonlight background, no features visible, mysterious, cinematic haze, film grain",
            "Close-up night shot, the dark silhouette of one impossibly long bony finger tapping on tree bark, pure silhouette no details, dramatic rim moonlight, mysterious mood, film grain",
            "Wide night shot, the dark silhouette of a round-eared creature perched on a branch with enormous reflective eyes, pure silhouette, dark jungle background, no features visible, mysterious mood, film grain",
            "Close-up night shot, the dark silhouette of a hand with one grotesquely long middle finger extended probing into tree bark, pure silhouette, mysterious mood, film grain",
            "Low-angle night shot, the dramatic dark silhouette of a large-eared creature on a branch against a full moon, golden rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Immortal Jellyfish",
        "title": "Who dat critter? 🪼♾️ (The ONLY animal that can NEVER die of old age!) #shorts",
        "output": "CRITTER_IMMORTAL_JELLYFISH.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "immortal jellyfish",
        "reveal_search": "Turritopsis dohrnii",
        "description": "Can you guess the only IMMORTAL animal? ♾️\n\nGuess the mystery animal from 3 clues:\n1️⃣ It is biologically IMMORTAL — it never dies of old age!\n2️⃣ When it gets sick or old it transforms back into a BABY!\n3️⃣ It is smaller than a human fingernail and lives in the ocean!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, guess the animal, immortal jellyfish, turritopsis dohrnii, immortal animal, jellyfish facts, ocean animals, forever young animal, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the only truly immortal animal on Earth? Three mind-blowing clues!
Clue one! This creature is biologically immortal. It literally cannot die of old age!
Clue two! When it gets sick, injured, or just old, it reverses its entire body back into a baby and starts life all over again!
Clue three! It is smaller than your fingernail, completely transparent, and drifts through tropical oceans right now!
Did you guess it? Three... Two... One...
It's the IMMORTAL JELLYFISH! The animal that lives forever! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key underwater shot, 50mm lens, the dark translucent silhouette of a tiny bell-shaped creature drifting in dark water, a glowing question mark, bioluminescent particles, no features visible, mysterious, cinematic haze, film grain",
            "Wide underwater shot, the dark silhouette of a tiny jellyfish transforming into a smaller younger form, shrinking in dark water, pure silhouette no details, mysterious mood, film grain",
            "Close-up underwater, the dark silhouette of trailing tentacles hanging from a tiny bell shape, bioluminescent glow around edges, pure silhouette, mysterious mood, film grain",
            "Wide underwater shot, the dark silhouette of a tiny creature drifting up through dark deep ocean water toward a distant light, no features visible, mysterious mood, film grain",
            "Low-angle underwater shot, the dramatic dark silhouette of a tiny jellyfish floating against a deep ocean abyss, golden bioluminescent rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Shoebill Stork",
        "title": "Who dat critter? 👟🦕 (It looks like a DINOSAUR with a SHOE on its face!) #shorts",
        "output": "CRITTER_SHOEBILL_STORK.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "shoebill",
        "reveal_search": "Shoebill",
        "description": "Can you guess the prehistoric-looking bird? 🦕\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has a massive SHOE-shaped beak that can snap up CROCODILES!\n2️⃣ It stands completely STILL for hours waiting to ambush prey!\n3️⃣ It looks so ancient that scientists call it a living dinosaur!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, guess the animal, shoebill stork, shoebill bird, dinosaur bird, prehistoric bird, weird birds, African birds, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the bird that looks like it walked straight out of the dinosaur age? Three prehistoric clues!
Clue one! This giant bird has a massive shoe-shaped beak powerful enough to catch and crush baby CROCODILES!
Clue two! It hunts by standing completely STILL in a swamp for hours, then strikes like lightning in under one second!
Clue three! It is so ancient-looking that scientists say it is one of the closest living links to actual dinosaurs!
Did you guess it? Three... Two... One...
It's the SHOEBILL STORK! Africa's living dinosaur! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key swamp shot, 50mm lens, the dark silhouette of a tall bird standing motionless in dark misty water, a glowing question mark, swamp fog, no features visible, mysterious, cinematic haze, film grain",
            "Close-up swamp shot, the dark silhouette of a massive wide shoe-shaped beak seen from the side, pure silhouette no details, dramatic rim light, mysterious mood, film grain",
            "Wide swamp shot, the dark silhouette of a huge still bird standing in shallow dark water among reeds, no features visible, mysterious mood, film grain",
            "Close-up swamp shot, the dark silhouette of a large head with a massive prehistoric beak striking downward toward dark water, pure silhouette, mysterious mood, film grain",
            "Low-angle swamp shot, the towering dark silhouette of a massive bird spreading its wings against a misty orange sunset swamp, golden rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Pistol Shrimp",
        "title": "Who dat critter? 🔫🦐 (Makes a SOUND louder than a GUN underwater!) #shorts",
        "output": "CRITTER_PISTOL_SHRIMP_V2.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "pistol shrimp",
        "reveal_search": "Alpheid shrimp",
        "description": "Can you guess the loudest tiny creature in the ocean? 🔫\n\nGuess the mystery animal from 3 clues:\n1️⃣ Its snap creates a bubble HOTTER than the surface of the SUN!\n2️⃣ It can stun or kill prey with pure sound and shockwave!\n3️⃣ It is only 3-5cm long but makes the loudest sound in the ocean!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, pistol shrimp, alpheid shrimp, loudest ocean animal, shrimp facts, sonoluminescence, ocean animals, weird sea creatures, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the ocean's tiniest assassin? Three explosive clues!
Clue one! When this tiny creature snaps its claw, it creates a shockwave bubble that reaches temperatures hotter than the SURFACE OF THE SUN!
Clue two! That bubble collapses so fast it creates a flash of light AND a shockwave powerful enough to stun or kill fish!
Clue three! It is only three to five centimetres long but its snap reaches two hundred and eighteen decibels, louder than a gunshot!
Did you guess it? Three... Two... One...
It's the PISTOL SHRIMP! The ocean's most dangerous tiny weapon! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key underwater macro shot, 50mm lens, the dark silhouette of a tiny shrimp with one oversized claw on a dark rocky seafloor, a glowing question mark, sand particles drifting, no features visible, mysterious, cinematic haze, film grain",
            "Close-up underwater macro, the dark silhouette of a single massive claw snapping shut creating a shockwave ring in dark water, pure silhouette no details, dramatic backlight, mysterious mood, film grain",
            "Wide underwater shot, the dark silhouette of a tiny shrimp backed into a rock crevice with its huge claw raised defensively, no features visible, mysterious mood, film grain",
            "Close-up underwater macro, the dark silhouette of a shockwave bubble collapse near the claw tip, tiny flash of light, pure silhouette, mysterious mood, film grain",
            "Low-angle underwater shot, the dramatic dark silhouette of a tiny shrimp firing its claw at a shadow fish, shockwave rings expanding, golden backlight, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Naked Mole Rat",
        "title": "Who dat critter? 🐀👑 (It CANNOT get cancer and never feels PAIN!) #shorts",
        "output": "CRITTER_NAKED_MOLE_RAT.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "naked mole rat",
        "reveal_search": "Naked mole-rat",
        "description": "Can you guess the weirdest mammal alive? 👑\n\nGuess the mystery animal from 3 clues:\n1️⃣ Scientists have NEVER found a single one with cancer in 40 years of research!\n2️⃣ It cannot feel certain kinds of PAIN because it is missing a key nerve chemical!\n3️⃣ It lives underground in colonies like ants, with one queen who does all the breeding!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, naked mole rat, cancer resistant animal, weird mammals, underground animals, mammal colony, fun animal facts, animal quiz for kids, educational kids video, viral shorts, immortal animal",
        "script": """Can you guess the weirdest and most medically incredible mammal on Earth? Three unbelievable clues!
Clue one! Scientists have studied thousands of these animals for over forty years and have NEVER found a single case of cancer!
Clue two! It is missing a key chemical that transmits certain pain signals, so it literally cannot feel some types of pain!
Clue three! It lives underground in colonies exactly like ants and bees, with one queen who is the only one allowed to have babies!
Did you guess it? Three... Two... One...
It's the NAKED MOLE RAT! The mammal that broke all the rules of biology! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key underground shot, 50mm lens, the dark silhouette of a wrinkled hairless rodent with huge buck teeth in a dark tunnel, a glowing question mark, soil particles drifting, no features visible, mysterious, cinematic haze, film grain",
            "Wide underground shot, the dark silhouette of a small wrinkled creature moving through a dark underground tunnel, pure silhouette no details, dramatic rim light, mysterious mood, film grain",
            "Close-up underground shot, the dark silhouette of a large-toothed snout with protruding incisors gnawing at dark earth, pure silhouette, mysterious mood, film grain",
            "Wide underground shot, the dark silhouette of a hairless rodent curled near a queen creature slightly larger than the rest, no features visible, mysterious mood, film grain",
            "Low-angle underground shot, the dark silhouette of a small wrinkled creature standing upright on its hind legs in a glowing underground chamber, golden rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Blue-Ringed Octopus",
        "title": "Who dat critter? 💙🐙 (One of the DEADLIEST animals on Earth — fits in your HAND!) #shorts",
        "output": "CRITTER_BLUE_RINGED_OCTOPUS.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "blue-ringed octopus",
        "reveal_search": "Blue-ringed octopus",
        "description": "Can you guess the world's most venomous octopus? 💙\n\nGuess the mystery animal from 3 clues:\n1️⃣ It's small enough to fit in your HAND but carries enough venom to kill 26 adults!\n2️⃣ Its glowing blue rings only APPEAR when it feels threatened!\n3️⃣ There is NO antivenom for its bite — it is completely untreatable!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, blue ringed octopus, most venomous octopus, deadliest animals, ocean animals, venomous sea creatures, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the most deadly creature that fits in the palm of your hand? Three terrifying clues!
Clue one! This tiny ocean animal carries enough venom to kill twenty-six adult humans in minutes!
Clue two! It hides its glowing electric-blue rings until the very moment it feels threatened — then they flash like a warning!
Clue three! Scientists have never found an antivenom — if it bites you, there is absolutely no cure!
Did you guess it? Three... Two... One...
It's the BLUE-RINGED OCTOPUS! The ocean's most deadly tiny predator! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key underwater macro shot, 50mm lens, the dark silhouette of a small golf-ball sized octopus resting on a rock, a faint glowing question mark, dark shallow reef water, no features visible, mysterious, cinematic haze, film grain",
            "Close-up underwater macro, the dark silhouette of a small octopus with faint glowing ring shapes barely visible on its skin, pure silhouette, dark water, mysterious mood, film grain",
            "Wide underwater shot, the dark silhouette of a tiny octopus tucked inside a small shell crevice, no features visible, dark reef background, mysterious mood, film grain",
            "Close-up underwater macro, the dark silhouette of a tiny beak-like mouth at the centre of a small octopus body, pure silhouette, no details, mysterious mood, film grain",
            "Low-angle underwater shot, the dramatic dark silhouette of a tiny octopus spreading all eight arms wide against a glowing ocean surface, golden light rays, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Wolverine Animal",
        "title": "Who dat critter? 🐾💀 (It can FIGHT a BEAR and WIN!) #shorts",
        "output": "CRITTER_WOLVERINE.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "wolverine",
        "reveal_search": "Wolverine (animal)",
        "description": "Can you guess the fearless furry fighter? 💀\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has been documented chasing BEARS and WOLVES away from their kills!\n2️⃣ It weighs only 15kg but has the bite force of an animal ten times its size!\n3️⃣ It lives in the frozen Arctic and can travel 50km in a single day!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, wolverine animal, fearless animal, strongest animal, arctic animals, weasel family, animal fights, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the most fearless animal pound for pound on the entire planet? Three fierce clues!
Clue one! Despite weighing only fifteen kilograms this animal has been documented chasing full-grown BEARS and WOLVES away from their food!
Clue two! It has a bite force powerful enough to crush frozen bone and it will fight literally ANYTHING without backing down!
Clue three! It lives in the frozen Arctic tundra and can run through deep snow for fifty kilometres in a single day without resting!
Did you guess it? Three... Two... One...
It's the WOLVERINE! Nature's most fearless fighter! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key arctic shot, 50mm lens, the dark silhouette of a stocky low-slung muscular animal walking through dark snow, a glowing question mark, blizzard particles, no features visible, mysterious, cinematic haze, film grain",
            "Wide arctic shot, the dark silhouette of a powerful compact animal with a bushy tail trudging through deep snow in a dark pine forest, pure silhouette no details, mysterious mood, film grain",
            "Close-up arctic shot, the dark silhouette of a broad flat skull with powerful jaw muscles seen from the side, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide arctic shot, the dark silhouette of a small but incredibly muscular animal standing over a large dark shadow carcass in snow, no features visible, mysterious mood, film grain",
            "Low-angle arctic shot, the heroic dark silhouette of a stocky powerful animal on a snow ridge against a dark northern lights sky, golden rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Fossa",
        "title": "Who dat critter? 🐱🦁 (Madagascar's APEX predator that looks like a CAT-LION!) #shorts",
        "output": "CRITTER_FOSSA.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "fossa",
        "reveal_search": "Fossa (animal)",
        "description": "Can you guess Madagascar's mysterious apex predator? 🦁\n\nGuess the mystery animal from 3 clues:\n1️⃣ It is the top predator of Madagascar and hunts lemurs through the trees!\n2️⃣ It looks like a cross between a cat, a dog, and a small lion!\n3️⃣ It is related to the MONGOOSE, not cats or dogs!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, fossa, madagascar animal, apex predator, weird animals, cat lion animal, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the mysterious apex predator of Madagascar? Three wild clues!
Clue one! This animal is the top predator of an entire island and it hunts lemurs by leaping through the treetops at terrifying speed!
Clue two! It looks exactly like a cross between a mountain lion, a cat, and a dog, but scientists say it is actually related to none of them!
Clue three! Its closest relative is actually the MONGOOSE, which makes it one of the most confusing animals in the entire world!
Did you guess it? Three... Two... One...
It's the FOSSA! Madagascar's ultimate mystery predator! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key jungle night shot, 50mm lens, the dark silhouette of a long lithe cat-like predator on a tree branch, a glowing question mark, moonlit jungle background, no features visible, mysterious, cinematic haze, film grain",
            "Wide jungle shot, the dark silhouette of a sleek powerful animal leaping between dark tree branches at night, no features visible, mysterious mood, film grain",
            "Close-up jungle shot, the dark silhouette of a long narrow cat-like face with rounded ears and a slightly dog-like snout, pure silhouette no details, mysterious mood, film grain",
            "Wide jungle shot, the dark silhouette of a long-tailed predator crouching on a thick branch above dark undergrowth, no features visible, mysterious mood, film grain",
            "Low-angle jungle shot, the commanding dark silhouette of a lean powerful predator standing on a jungle floor against a dark canopy, golden rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Platypus Venom",
        "title": "Who dat critter? 🦆☠️ (The cute animal that has VENOM SPURS on its LEGS!) #shorts",
        "output": "CRITTER_PLATYPUS_VENOM.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "platypus",
        "reveal_search": "Platypus venom",
        "description": "Can you guess the venomous egg-laying mammal? ☠️\n\nGuess the mystery animal from 3 clues:\n1️⃣ It is one of only FIVE mammals that lays eggs!\n2️⃣ The male has venomous SPURS on its hind legs powerful enough to cause excruciating pain for months!\n3️⃣ It hunts underwater with its eyes CLOSED using electric sensors in its bill!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, platypus, venomous platypus, egg laying mammal, weird animals, Australia animals, electric sense animal, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the mammal so weird that scientists thought it was a JOKE when they first saw it? Three bizarre clues!
Clue one! It is one of only five mammals on Earth that actually LAYS EGGS instead of giving birth to live babies!
Clue two! The males have hidden venomous spurs on their back legs so painful that the agony can last for MONTHS and there is no painkiller that stops it!
Clue three! It hunts completely underwater with its eyes shut tight, finding prey purely through electric sensors built into its rubbery bill!
Did you guess it? Three... Two... One...
It's the PLATYPUS! The mammal that broke every single rule of biology! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key river shot, 50mm lens, the dark silhouette of a flat-billed duck-like creature with a beaver tail half-submerged in dark water, a glowing question mark, ripples, no features visible, mysterious, cinematic haze, film grain",
            "Underwater shot, the dark silhouette of a flat-billed creature gliding through dark murky water with eyes closed, pure silhouette no details, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a wide flat duck-like bill touching dark water surface, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a hind leg with a small sharp spur visible in profile, pure silhouette no details, mysterious mood, film grain",
            "Low-angle river shot, the dark silhouette of a strange flat-billed beaver-tailed creature emerging from dark water onto a riverbank, golden rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Lyrebird",
        "title": "Who dat critter? 🎵🐦 (It can PERFECTLY copy a CHAINSAW, camera, and car alarm!) #shorts",
        "output": "CRITTER_LYREBIRD.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "lyrebird",
        "reveal_search": "Lyrebird",
        "description": "Can you guess the world's greatest mimic? 🎵\n\nGuess the mystery animal from 3 clues:\n1️⃣ It can perfectly imitate a chainsaw, a camera shutter, and a car alarm!\n2️⃣ It lives in Australian rainforests and uses its incredible voice to attract mates!\n3️⃣ Its tail feathers are shaped exactly like an ancient Greek musical instrument!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, lyrebird, best mimic bird, sound copying animal, Australian bird, chainsaw bird, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the bird with the most incredible voice on the entire planet? Three musical clues!
Clue one! This bird can produce a perfect copy of a chainsaw, a camera shutter clicking, and a car alarm — sounds it hears in the forest from humans nearby!
Clue two! It memorises hundreds of sounds from its environment and combines them into a song to impress potential partners!
Clue three! Its spectacular tail feathers are shaped exactly like the lyre, an ancient Greek musical instrument played by gods in mythology!
Did you guess it? Three... Two... One...
It's the LYREBIRD! Australia's living music machine! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key rainforest shot, 50mm lens, the dark silhouette of a medium-sized bird with an extravagant fan-shaped tail standing on a forest floor, a glowing question mark, misty trees, no features visible, mysterious, cinematic haze, film grain",
            "Wide rainforest shot, the dark silhouette of a bird with a magnificently spread fan tail in a clearing, pure silhouette no details, soft backlight, mysterious mood, film grain",
            "Close-up rainforest shot, the dark silhouette of a bird's open beak with sound wave ripples emanating from it, pure silhouette, mysterious mood, film grain",
            "Wide rainforest shot, the dark silhouette of a bird with a lyre-shaped tail walking slowly through dark undergrowth, no features visible, mysterious mood, film grain",
            "Low-angle rainforest shot, the dramatic dark silhouette of a bird with full fan tail displayed against a misty golden forest background, golden rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Goblin Shark",
        "title": "Who dat critter? 🦷👻 (The deep sea shark with a JAW that SHOOTS out of its face!) #shorts",
        "output": "CRITTER_GOBLIN_SHARK.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "goblin shark",
        "reveal_search": "Goblin shark",
        "description": "Can you guess the scariest deep sea shark? 👻\n\nGuess the mystery animal from 3 clues:\n1️⃣ Its jaw can LAUNCH forward out of its face to catch prey!\n2️⃣ It lives 1,300 metres deep in complete darkness!\n3️⃣ Its skin is translucent pink because you can SEE its blood vessels through it!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, goblin shark, deep sea shark, weird sharks, slingshot jaw shark, deep ocean animals, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the nightmare shark from the deepest darkest part of the ocean? Three terrifying clues!
Clue one! When this shark attacks, its entire jaw LAUNCHES forward out of its face like a slingshot to snatch prey it could never reach normally!
Clue two! It lives over one thousand three hundred metres below the surface in total darkness where no sunlight ever reaches!
Clue three! Its skin is a ghostly translucent pink because you can literally SEE its blood vessels glowing through its body!
Did you guess it? Three... Two... One...
It's the GOBLIN SHARK! The ocean's most terrifying living fossil! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key deep ocean shot, 50mm lens, the dark silhouette of a long-snouted shark with a protruding blade-like nose drifting through black water, a glowing question mark, bioluminescent particles, no features visible, mysterious, cinematic haze, film grain",
            "Wide deep ocean shot, the dark silhouette of a shark with an unusually long flat snout cruising through absolute darkness, pure silhouette no details, mysterious mood, film grain",
            "Close-up deep ocean shot, the dark silhouette of a long blade-like rostrum extending far in front of a blunt head, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Close-up deep ocean shot, the dark silhouette of a jaw extending outward from a shark face on a spring-like mechanism, pure silhouette no details, mysterious mood, film grain",
            "Low-angle deep ocean shot, the ghostly dark silhouette of a long-snouted shark rising from total darkness toward a faint light above, golden bioluminescent rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Cassowary",
        "title": "Who dat critter? 🦕🔵 (The most DANGEROUS bird alive — kicks like a VELOCIRAPTOR!) #shorts",
        "output": "CRITTER_CASSOWARY.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "cassowary",
        "reveal_search": "Cassowary",
        "description": "Can you guess the world's most dangerous bird? 🦕\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has a dagger-like claw 12cm long that can disembowel a human in one kick!\n2️⃣ It has a bony helmet called a CASQUE on its head — no one knows exactly what it is for!\n3️⃣ It looks exactly like a velociraptor and lives in Australia and New Guinea!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, cassowary, most dangerous bird, velociraptor bird, Australian animals, deadly birds, dagger claw bird, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the bird that looks like a real-life velociraptor? Three prehistoric clues!
Clue one! This bird has a dagger-shaped claw twelve centimetres long on each foot, capable of delivering a single kick powerful enough to kill a human!
Clue two! It has a mysterious bony helmet called a casque growing from the top of its head and after a hundred years of research scientists STILL do not know what it is for!
Clue three! It cannot fly, runs at fifty kilometres per hour, and looks so much like a prehistoric raptor that it is literally called a living dinosaur!
Did you guess it? Three... Two... One...
It's the CASSOWARY! The world's most dangerous living bird! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key rainforest shot, 50mm lens, the dark silhouette of a massive flightless bird with a helmet-like protrusion on its head walking through dark jungle, a glowing question mark, misty trees, no features visible, mysterious, cinematic haze, film grain",
            "Wide rainforest shot, the dark silhouette of a very large bird with a prominent bony head crest and powerful legs standing in dark undergrowth, pure silhouette no details, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a thick powerful leg with a long dagger-like claw visible in profile, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide rainforest shot, the dark silhouette of a tall heavy bird running at speed through dark jungle, motion blur, no features visible, mysterious mood, film grain",
            "Low-angle rainforest shot, the towering dark silhouette of a massive helmeted bird against a dark canopy, golden rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Mantis Shrimp Color",
        "title": "Who dat critter? 🌈🦐 (It can see colors that DON'T EXIST to human eyes!) #shorts",
        "output": "CRITTER_MANTIS_SHRIMP_COLOR.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "mantis shrimp",
        "reveal_search": "Mantis shrimp",
        "description": "Can you guess the animal that sees the most colors? 🌈\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has 16 types of color receptors — humans only have 3!\n2️⃣ It can see ultraviolet, infrared, and colors that literally have no name in human language!\n3️⃣ Its punch is also faster than a bullet — we did a video on that too!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, mantis shrimp, mantis shrimp color vision, 16 color receptors, most colors animal, rainbow animal, ocean animals, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the animal that sees a world of color you cannot even imagine? Three mind-bending clues!
Clue one! This animal has sixteen different types of colour receptors in its eyes. Humans only have three!
Clue two! It can see ultraviolet light, infrared light, and entire ranges of colour that have absolutely no name in any human language because no human has ever seen them!
Clue three! We already did a video about how it punches faster than a bullet. Did you catch that one?
Did you guess it? Three... Two... One...
It's the MANTIS SHRIMP! The animal that lives in a universe of colour we will never see! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key underwater shot, 50mm lens, the dark silhouette of a long streamlined crustacean with large compound eyes on stalks peeking from a dark burrow, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Close-up underwater shot, the dark silhouette of a pair of large stalked eyes scanning in opposite directions, pure silhouette no details, dramatic backlight, mysterious mood, film grain",
            "Wide underwater shot, the dark silhouette of a torpedo-shaped crustacean hovering in dark water, no features visible, mysterious mood, film grain",
            "Close-up underwater shot, the dark silhouette of an open raptorial claw raised and ready to strike, pure silhouette, mysterious mood, film grain",
            "Low-angle underwater shot, the dramatic dark silhouette of a mantis shrimp rising from a dark reef burrow with large eyes glinting, golden backlight, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Sun Bear",
        "title": "Who dat critter? 🐻☀️ (The smallest bear — with a tongue LONGER than your HAND!) #shorts",
        "output": "CRITTER_SUN_BEAR.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "sun bear",
        "reveal_search": "Sun bear",
        "description": "Can you guess the world's smallest bear? ☀️\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has a tongue 25cm long — longer than most human hands — for extracting honey!\n2️⃣ It is the world's smallest bear, only 70cm tall!\n3️⃣ It has a golden or orange crescent-shaped patch on its chest shaped like a rising sun!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, sun bear, smallest bear, honey bear, long tongue animal, Southeast Asia animals, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the world's smallest and strangest bear? Three golden clues!
Clue one! This bear has a tongue twenty-five centimetres long — longer than most human hands — perfectly designed to reach deep inside beehives and slurp out honey!
Clue two! It is the tiniest bear species on the planet, standing only seventy centimetres tall, but it has the longest claws relative to its body of any bear!
Clue three! It has a bright golden crescent shaped exactly like a rising sun on its chest, which is how it got its name!
Did you guess it? Three... Two... One...
It's the SUN BEAR! The world's most underrated bear! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key jungle shot, 50mm lens, the dark silhouette of a small stocky bear-like animal with large paws climbing a dark tree trunk, a glowing question mark, jungle background, no features visible, mysterious, cinematic haze, film grain",
            "Wide jungle shot, the dark silhouette of a compact bear with large curved claws gripping a tree branch, pure silhouette no details, mysterious mood, film grain",
            "Close-up jungle shot, the dark silhouette of a small bear face with an absurdly long thin tongue extended outward, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide jungle shot, the dark silhouette of a small bear rooting through dark undergrowth, no features visible, mysterious mood, film grain",
            "Low-angle jungle shot, the dark silhouette of a small bear standing upright on its hind legs against a dark jungle background, golden rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Okapi",
        "title": "Who dat critter? 🦓🦒 (Zebra legs... but it is NOT a zebra!) #shorts",
        "output": "CRITTER_OKAPI.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "okapi",
        "reveal_search": "Okapi",
        "description": "Can you guess the forest animal with zebra legs? 🦓\n\nGuess the mystery animal from 3 clues:\n1️⃣ Its legs look JUST like a zebra, but it is actually a cousin of the GIRAFFE!\n2️⃣ It has a long blue tongue so it can wash its own eyes and ears!\n3️⃣ It is so secretive that scientists did not even know it existed until 1901!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, okapi, forest giraffe, zebra legs animal, weird animals, african animals, animal facts for kids, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the mystery animal that looks like it was made by accident? Three wild clues!
Clue one! Its legs are covered in black and white stripes exactly like a zebra, but scientists say its closest living relative is actually the GIRAFFE!
Clue two! Its tongue is so long it can reach its own ears AND wash its own eyes like a living windshield wiper!
Clue three! It is so shy and secretive that no scientist even knew this animal existed until the year nineteen oh one!
Did you guess it? Three... Two... One...
It's the OKAPI! The forest giraffe that pretended to be a zebra! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key rainforest shot, 50mm lens, the dark silhouette of a horse-like animal with bold striped legs standing in dark jungle mist, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Close-up shot, 50mm lens, the dark silhouette of a long dark tongue reaching up toward its own ear, pure silhouette no details, dramatic rim light, mysterious mood, film grain",
            "Wide rainforest shot, 35mm lens, the dark silhouette of a striped-legged animal grazing between dark tree trunks, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a zebra-striped leg stepping carefully through dark undergrowth, pure silhouette, mysterious mood, film grain",
            "Low-angle rainforest shot, the dark silhouette of a shy long-necked animal peeking from behind a dark tree, golden rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Saiga Antelope",
        "title": "Who dat critter? 🤥👃 (The animal with the WEIRDEST nose in the world!) #shorts",
        "output": "CRITTER_SAIGA.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "saiga antelope",
        "reveal_search": "Saiga antelope",
        "description": "Can you guess the animal with the strangest nose on Earth? 🤥\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has a huge droopy nose that hangs down over its mouth like a balloon!\n2️⃣ That weird nose heats up the freezing winter air before it reaches its lungs!\n3️⃣ It lives on the cold windy grasslands of Asia and can run super fast!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, saiga antelope, weird nose animal, weirdest animals, grassland animals, asian animals, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the animal with the most ridiculous nose on the entire planet? Three funny clues!
Clue one! This animal has a giant droopy nose that hangs down over its mouth, looking like a big squishy balloon!
Clue two! That enormous nose is actually a superpower — it warms up the freezing winter air before it hits its lungs!
Clue three! It gallops across the cold windy plains of Asia in huge herds and can outrun almost anything!
Did you guess it? Three... Two... One...
It's the SAIGA ANTELOPE! The animal with the nose that breaks all the rules! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key steppe shot, 50mm lens, the dark silhouette of a small antelope with a huge droopy bulbous nose standing in cold grassland mist, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Close-up shot, 50mm lens, the dark silhouette of an oversized droopy nose hanging over a small mouth, pure silhouette no details, dramatic rim light, mysterious mood, film grain",
            "Wide steppe shot, 35mm lens, the dark silhouette of a herd of strange-nosed antelopes galloping across dark open plains, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of warm breath steaming out of a huge round nose in freezing air, pure silhouette, mysterious mood, film grain",
            "Low-angle steppe shot, the heroic dark silhouette of a strange-nosed antelope standing tall on a grassy ridge against a golden dusty sky, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Maned Wolf",
        "title": "Who dat critter? 🦊🦵 (A fox on STILTS — with legs taller than you!) #shorts",
        "output": "CRITTER_MANED_WOLF.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "maned wolf",
        "reveal_search": "Maned wolf",
        "description": "Can you guess the leggiest animal in South America? 🦵\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has the LONGEST legs compared to its body of any wild animal — like a fox on stilts!\n2️⃣ It is not really a wolf, not really a fox — it is its OWN special family!\n3️⃣ Its favourite fruit smells like TOMATOES and is called the wolf's apple!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, maned wolf, fox on stilts, long legs animal, south american animals, weird animals, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the animal that looks like a fox that drank a growth potion? Three tall clues!
Clue one! This animal has the longest legs compared to its body of ANY wild animal — a fox standing on stilts!
Clue two! Even though it is called a wolf, it is not a wolf and not a fox — it belongs to its own super special animal family!
Clue three! It LOVES a red fruit called the wolf's apple that smells just like ripe tomatoes!
Did you guess it? Three... Two... One...
It's the MANED WOLF! The leggiest loner of the South American grasslands! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key savanna shot, 50mm lens, the dark silhouette of a long-legged reddish animal with tall ears standing in tall dark grass at dusk, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide shot, 35mm lens, the dark silhouette of an incredibly leggy animal strolling through golden savanna grass, no features visible, mysterious mood, film grain",
            "Close-up shot, 50mm lens, the dark silhouette of a long fox-like snout and tall pointed ears, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of four impossibly long skinny legs in a row as the animal walks, no features visible, mysterious mood, film grain",
            "Low-angle savanna shot, the commanding dark silhouette of a maned wolf on a grassy ridge against a golden sunset, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Japanese Spider Crab",
        "title": "Who dat critter? 🦀😱 (A crab with LEGS LONGER than a CAR!) #shorts",
        "output": "CRITTER_JAPANESE_SPIDER_CRAB.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "japanese spider crab",
        "reveal_search": "Japanese spider crab",
        "description": "Can you guess the biggest crab in the world? 🦀\n\nGuess the mystery animal from 3 clues:\n1️⃣ Its legs can stretch over 3 METRES — longer than a small car!\n2️⃣ It is the LARGEST crab on Earth and can live to be 100 years old!\n3️⃣ It lives super deep on the ocean floor near Japan!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, japanese spider crab, biggest crab, giant crab, largest crustacean, ocean animals, weird sea creatures, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the ocean's biggest nightmare crab? Three giant clues!
Clue one! This crab's legs can stretch out more than three metres — that is longer than a small car, from bumper to bumper!
Clue two! It is officially the largest crab species on Earth, and a really old one can live for over one hundred years!
Clue three! It lives on the dark ocean floor near Japan, deep below where sunlight ever reaches!
Did you guess it? Three... Two... One...
It's the JAPANESE SPIDER CRAB! The leggiest giant of the deep sea! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key deep ocean shot, 50mm lens, the dark silhouette of a giant crab with impossibly long spindly legs standing on dark seabed, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide deep ocean shot, 35mm lens, the dark silhouette of a huge long-legged crab towering over tiny dark rocks, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a giant crab body with thin knobbly legs stretching in every direction, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of long spindly crab legs side by side next to the shadow of a car for scale, no features visible, mysterious mood, film grain",
            "Low-angle deep ocean shot, the dark silhouette of a colossal long-legged crab rising above the dark seabed, golden bioluminescent rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Vampire Squid",
        "title": "Who dat critter? 🦑🧛 (The creature with a CAPE — straight out of a horror movie!) #shorts",
        "output": "CRITTER_VAMPIRE_SQUID.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "vampire squid",
        "reveal_search": "Vampire squid",
        "description": "Can you guess the deep-sea vampire? 🦑\n\nGuess the mystery animal from 3 clues:\n1️⃣ Its name means vampire, but it does NOT drink blood — it eats floating ocean snow!\n2️⃣ When scared, it wraps its arms around itself like a CAPE and glows in the dark!\n3️⃣ It lives deeper than any other squid, in the blackest parts of the ocean!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, vampire squid, deep sea animals, weird ocean creatures, glowing animals, octopus squid, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the deep-sea creature that looks like a vampire's worst nightmare? Three spooky clues!
Clue one! Its name means vampire squid, but it does NOT drink blood — it quietly eats tiny bits of food drifting down like snow!
Clue two! When it feels scared, it flips its webbed arms over its head like a cape and glows with blue lights to confuse predators!
Clue three! It lives in the deepest, darkest zone of the ocean where almost no other squid can survive!
Did you guess it? Three... Two... One...
It's the VAMPIRE SQUID! The cape-wearing ghost of the deep sea! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key deep ocean shot, 50mm lens, the dark silhouette of a small round creature with a webbed cape-like body floating in black water, a glowing question mark, bioluminescent particles, no features visible, mysterious, cinematic haze, film grain",
            "Wide deep ocean shot, the dark silhouette of a caged creature with its arms wrapped over its head like a cloak, pure silhouette no details, mysterious mood, film grain",
            "Close-up deep ocean shot, the dark silhouette of two enormous round eyes glowing faintly through a dark cape, pure silhouette, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a small round creature drifting through slowly falling marine snow in darkness, no features visible, mysterious mood, film grain",
            "Low-angle deep ocean shot, the ghostly dark silhouette of a caped creature floating upward toward a faint light above, blue bioluminescent rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Gharial",
        "title": "Who dat critter? 🐊👃 (A crocodile with a SNOUT like a sword!) #shorts",
        "output": "CRITTER_GHARIAL.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "gharial",
        "reveal_search": "Gharial",
        "description": "Can you guess the strangest crocodile on Earth? 🐊\n\nGuess the mystery animal from 3 clues:\n1️⃣ Its snout is super long and skinny, like a sword, and has a funny bump on the tip!\n2️⃣ It only eats FISH — it is the one crocodile that will NOT eat you!\n3️⃣ It lives in the rivers of India and its name means 'pot' because of that nose bump!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, gharial, weird crocodile, long snout animal, indian animals, river animals, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the crocodile that looks like a dinosaur cosplayer? Three slippery clues!
Clue one! This crocodile has an extra long skinny snout shaped exactly like a sword, with a funny round bump on the very tip!
Clue two! It is the ONLY crocodile in the world that eats only fish — its jaws are far too skinny to even try to bite a human!
Clue three! It lives in the rivers of India, and its name comes from a word meaning pot, thanks to that silly nose bump!
Did you guess it? Three... Two... One...
It's the GHARIAL! The gentle pot-nosed crocodile of India! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key river shot, 50mm lens, the dark silhouette of a long skinny-snouted reptile lying in dark slow river water, a glowing question mark, mist, no features visible, mysterious, cinematic haze, film grain",
            "Close-up shot, 50mm lens, the dark silhouette of a long sword-like snout with a round bulb at the tip resting above the water, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide river shot, 35mm lens, the dark silhouette of a long snouted reptile sliding silently through dark water, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a narrow jaw filled with thin needle teeth breaking the surface, pure silhouette, mysterious mood, film grain",
            "Low-angle river shot, the dark silhouette of a long-snouted giant rising from dark water against a golden riverbank, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Proboscis Monkey",
        "title": "Who dat critter? 🐒👃 (The monkey with a HONKIN' giant nose!) #shorts",
        "output": "CRITTER_PROBOSCIS_MONKEY.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "proboscis monkey",
        "reveal_search": "Proboscis monkey",
        "description": "Can you guess the monkey with the biggest nose? 🐒\n\nGuess the mystery animal from 3 clues:\n1️⃣ The male has a GIANT floppy nose that hangs right over his mouth!\n2️⃣ When he is excited or scared, that big nose honks and boings like a horn!\n3️⃣ It lives ONLY on the island of Borneo and is an amazing swimmer!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, proboscis monkey, big nose monkey, borneo animals, weird monkeys, long nosed monkey, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the monkey with a nose that would make Pinocchio jealous? Three big clues!
Clue one! The male of this species has an enormous floppy nose that hangs all the way down over his mouth!
Clue two! When he gets excited, scared or angry, that giant nose fills with air and makes a loud honking sound!
Clue three! It lives only on the island of Borneo, and it is a fantastic swimmer that dives right into rivers!
Did you guess it? Three... Two... One...
It's the PROBOSCIS MONKEY! The honking nose of Borneo! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key rainforest shot, 50mm lens, the dark silhouette of a monkey with a huge drooping nose sitting on a dark tree branch, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Close-up shot, 50mm lens, the dark silhouette of a big floppy nose hanging over a monkey mouth, pure silhouette no details, dramatic rim light, mysterious mood, film grain",
            "Wide rainforest shot, 35mm lens, the dark silhouette of a big-nosed monkey leaping between dark trees, no features visible, mysterious mood, film grain",
            "Wide river shot, the dark silhouette of a big-nosed monkey swimming across a dark river with only its head above water, no features visible, mysterious mood, film grain",
            "Low-angle rainforest shot, the dark silhouette of a large-nosed monkey perched on a branch against a golden misty canopy, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Anglerfish",
        "title": "Who dat critter? 🐟🔦 (The fish that CARRIES its own flashlight!) #shorts",
        "output": "CRITTER_ANGLERFISH.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "anglerfish",
        "reveal_search": "Anglerfish",
        "description": "Can you guess the fish with a built-in light? 🐟\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has a glowing LURE hanging in front of its mouth like a fishing rod!\n2️⃣ It lives in the pitch-black deep ocean where sunlight NEVER reaches!\n3️⃣ The female carries a tiny male attached to her body forever!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, anglerfish, deep sea fish, glowing fish, scary fish, deep ocean animals, weird sea creatures, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the deep-sea nightmare with its own torch? Three glowing clues!
Clue one! This fish has a fishing rod on its head with a glowing lure that dangles right in front of its huge teeth-filled mouth!
Clue two! It lives in the deepest darkest part of the ocean where no sunlight ever reaches, so it makes its own light!
Clue three! The male is tiny and attaches himself to the female's body, becoming part of her forever!
Did you guess it? Three... Two... One...
It's the ANGLERFISH! The living flashlight of the abyss! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key deep ocean shot, 50mm lens, the dark silhouette of a round fish with huge jaws and a small glowing lure hanging from its head, a glowing question mark, black water, no features visible, mysterious, cinematic haze, film grain",
            "Close-up shot, the dark silhouette of an enormous toothy mouth open wide in total darkness, only the tiny glowing lure visible, pure silhouette, mysterious mood, film grain",
            "Wide deep ocean shot, the dark silhouette of a scary fish drifting in pitch black water with its glowing lure casting a tiny halo, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a female anglerfish with a tiny male attached to her side, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Low-angle deep ocean shot, the terrifying dark silhouette of an anglerfish rising from the abyss with its lure glowing, golden bioluminescent rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Star-Nosed Mole",
        "title": "Who dat critter? 🐀🌷 (The animal with 22 fingers on its NOSE!) #shorts",
        "output": "CRITTER_STAR_NOSED_MOLE.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "star-nosed mole",
        "reveal_search": "Star-nosed mole",
        "description": "Can you guess the animal with a star on its nose? ⭐\n\nGuess the mystery animal from 3 clues:\n1️⃣ Its nose has 22 tiny pink tentacles that look like a flower or a star!\n2️⃣ It uses those tentacles to find food in total darkness faster than any animal alive!\n3️⃣ It can eat in less than a QUARTER of a second — the fastest eater on Earth!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, star nosed mole, weird animals, fastest eater, animal with tentacles, underground animals, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the animal with a sea anemone stuck to its face? Three starry clues!
Clue one! This little animal's nose is covered in twenty two tiny pink tentacles that spread out like a star or a flower!
Clue two! Those tentacles are a superpower — it can smell and feel its food in total underground darkness faster than any animal on Earth!
Clue three! It is the fastest eater in the animal kingdom, able to decide and swallow a meal in less than a quarter of a second!
Did you guess it? Three... Two... One...
It's the STAR-NOSED MOLE! The tiny nose-flower of the underground! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key underground shot, 50mm lens, the dark silhouette of a small mole with a star of pink tentacles on its nose digging in dark soil, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Close-up shot, 50mm lens, the dark silhouette of a strange star-shaped nose of fleshy tentacles poking out of dark earth, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide underground shot, 35mm lens, the dark silhouette of a small star-nosed creature tunneling through a dark dirt passage, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of the little creature's tentacle-star nose reaching into dark water, pure silhouette, mysterious mood, film grain",
            "Low-angle underground shot, the dark silhouette of a small mole with its star nose raised sniffing in a dark chamber, golden rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Binturong",
        "title": "Who dat critter? 🐻🍿 (It smells EXACTLY like buttered popcorn!) #shorts",
        "output": "CRITTER_BINTURONG.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "binturong",
        "reveal_search": "Binturong",
        "description": "Can you guess the animal that smells like the movies? 🍿\n\nGuess the mystery animal from 3 clues:\n1️⃣ It smells exactly like BUTTERED POPCORN when you get close!\n2️⃣ It is called the bearcat, but it is really neither a bear nor a cat!\n3️⃣ It has a super-grippy tail like an extra hand and lives high in the trees of Asia!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, binturong, bearcat, popcorn animal, smells like popcorn, asian animals, tree animals, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the rainforest animal that smells like movie night? Three tasty clues!
Clue one! This animal gives off a smell EXACTLY like buttered popcorn because of a special scent it makes in its skin!
Clue two! People call it a bearcat, but scientists say it is actually neither a bear nor a cat — it is its own special animal!
Clue three! Its long fluffy tail works like a fifth hand, and it sleeps and eats high up in the trees of Southeast Asia!
Did you guess it? Three... Two... One...
It's the BINTURONG! The popcorn-scented bearcat of the canopy! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key rainforest shot, 50mm lens, the dark silhouette of a big fluffy dark-furred animal with a long curling tail sitting on a tree branch, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Close-up shot, the dark silhouette of a round fluffy face with small ears and gentle eyes hanging upside down from a branch, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide rainforest shot, 35mm lens, the dark silhouette of a bushy-tailed creature moving along a high dark tree branch at night, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a huge fluffy tail coiled around a thick tree branch like a hand, pure silhouette, mysterious mood, film grain",
            "Low-angle rainforest shot, the dark silhouette of a fluffy bearcat peering down from a high branch against a golden moonlit canopy, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Quokka",
        "title": "Who dat critter? 😁📸 (The happiest animal in the world!) #shorts",
        "output": "CRITTER_QUOKKA.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "quokka",
        "reveal_search": "Quokka",
        "description": "Can you guess the world's happiest animal? 😁\n\nGuess the mystery animal from 3 clues:\n1️⃣ It looks like it is ALWAYS smiling, so people call it the happiest animal on Earth!\n2️⃣ It is a small marsupial that carries its baby in a pouch like a kangaroo!\n3️⃣ It lives on a tiny island in Australia and loves posing for selfies!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, quokka, happiest animal, smiling animal, australian animals, selfie animal, marsupials, cute animals, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the animal that never stops smiling? Three cheerful clues!
Clue one! This little animal looks like it is grinning ALL the time, and everyone calls it the happiest animal in the world!
Clue two! It is a marsupial, which means it carries its tiny baby around in a warm pouch, just like a kangaroo!
Clue three! It lives on a small island off Australia, where it is famous for walking right up to tourists and posing for selfies!
Did you guess it? Three... Two... One...
It's the QUOKKA! The selfie-taking smiley face of Australia! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key island shot, 50mm lens, the dark silhouette of a small round smiling marsupial sitting on dark grass, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Close-up shot, the dark silhouette of a round chubby face with a big happy upturned mouth and round ears, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide island shot, 35mm lens, the dark silhouette of a small smiling creature hopping across a dark beach at dusk, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a little paw raised like it is waving, pure silhouette, mysterious mood, film grain",
            "Low-angle island shot, the dark silhouette of a small smiling marsupial sitting upright against a golden sunset sky, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Tapir",
        "title": "Who dat critter? 🐷🐘 (A pig... with an ELEPHANT trunk!) #shorts",
        "output": "CRITTER_TAPIR.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "tapir",
        "reveal_search": "Tapir",
        "description": "Can you guess the animal with a mini elephant trunk? 🐘\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has a short bendy trunk on its face that it uses like a little elephant!\n2️⃣ It is a fantastic swimmer and dives underwater to walk along the riverbed!\n3️⃣ Baby tapirs are born with stripes, so they look like little watermelons!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, tapir, elephant trunk animal, jungle animals, baby tapir, swimming mammal, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the animal that looks like a pig with an elephant's nose? Three trunk-ful clues!
Clue one! This animal has a short flexible trunk on its face that it uses to grab leaves and sniff like a mini elephant!
Clue two! It is an amazing swimmer — it will even dive underwater and walk along the bottom of the river using its toes like flippers!
Clue three! Baby tapirs are born with stripes and spots, so they look like walking watermelons to hide in the forest!
Did you guess it? Three... Two... One...
It's the TAPIR! The swimming pig-nosed tank of the jungle! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key jungle shot, 50mm lens, the dark silhouette of a stout round animal with a short trunk standing in dark forest water, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Close-up shot, the dark silhouette of a short bendy trunk reaching up to grab a leaf, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Underwater shot, the dark silhouette of a chunky trunked animal walking along a dark riverbed, bubbles rising, no features visible, mysterious mood, film grain",
            "Wide jungle shot, the dark silhouette of a striped baby tapir following a large adult through dark undergrowth, no features visible, mysterious mood, film grain",
            "Low-angle river shot, the dark silhouette of a trunked animal emerging from dark water onto a misty bank, golden rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Manatee",
        "title": "Who dat critter? 🐄🌊 (The gentle 'sea cow' that NEVER stops eating!) #shorts",
        "output": "CRITTER_MANATEE.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "manatee",
        "reveal_search": "Manatee",
        "description": "Can you guess the ocean's gentlest giant? 🐄\n\nGuess the mystery animal from 3 clues:\n1️⃣ It is called a 'sea cow' and is a super slow, gentle giant of the water!\n2️⃣ It eats about 10% of its body weight in plants EVERY single day!\n3️⃣ It is so relaxed that it breathes only every few minutes — and naps at the surface!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, manatee, sea cow, gentle giant, ocean animals, slowest animal, manatee facts, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the ocean's chillest giant? Three mellow clues!
Clue one! This giant is called a sea cow, and it is one of the slowest, gentlest creatures in the whole ocean!
Clue two! It spends most of its day munching underwater plants — it eats about ten percent of its own body weight in food every single day!
Clue three! It is so relaxed that it only takes a breath every few minutes, and you will often see it floating and napping at the water's surface!
Did you guess it? Three... Two... One...
It's the MANATEE! The ocean's cuddly, snack-loving sea cow! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key shallow water shot, 50mm lens, the dark silhouette of a huge round slow animal with a paddle tail drifting in murky warm water, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide water shot, 35mm lens, the dark silhouette of a giant round gentle creature floating at the surface with only its back showing, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a round wrinkled whiskery face with a snout breaking the water, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide underwater shot, the dark silhouette of a large slow animal grazing on dark water plants, bubbles rising, no features visible, mysterious mood, film grain",
            "Low-angle water shot, the dark silhouette of a giant sea cow swimming up toward sunlit water with golden rays, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Glass Frog",
        "title": "Who dat critter? 🐸🩷 (You can SEE THROUGH its belly!) #shorts",
        "output": "CRITTER_GLASS_FROG.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "glass frog",
        "reveal_search": "Glass frog",
        "description": "Can you guess the see-through frog? 🐸\n\nGuess the mystery animal from 3 clues:\n1️⃣ Its tummy is see-through, so you can watch its heart beat and its organs work!\n2️⃣ It is tiny — smaller than a marshmallow — and lives in rainforest trees!\n3️⃣ The dad guards the eggs until they hatch, staying on duty all night!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, glass frog, see through animal, transparent animals, rainforest animals, tiny frog, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the frog that is secretly a science experiment? Three see-through clues!
Clue one! This little frog's belly is completely see-through — you can actually WATCH its heart beating and food being digested!
Clue two! It is tiny, smaller than a marshmallow, and it spends its days clinging to leaves high in the rainforest!
Clue three! The dad is a super dad — he guards the eggs all night, keeping them wet until the babies hatch!
Did you guess it? Three... Two... One...
It's the GLASS FROG! The tiny see-through heartbeater of the jungle! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key rainforest shot, 50mm lens, the dark silhouette of a tiny frog clinging to a dark leaf with a faintly glowing translucent belly, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Close-up macro shot, the dark silhouette of a small translucent frog whose organs are faintly visible through its belly, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide rainforest shot, 35mm lens, the dark silhouette of a tiny frog on a big dark leaf high above the jungle floor, no features visible, mysterious mood, film grain",
            "Close-up macro shot, the dark silhouette of a tiny frog sitting on top of a cluster of glowing eggs on a leaf, pure silhouette, mysterious mood, film grain",
            "Low-angle rainforest shot, the dark silhouette of a tiny frog on a leaf against a golden moonlit canopy, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Tarsier",
        "title": "Who dat critter? 👀🙈 (The animal with EYES bigger than its BRAIN!) #shorts",
        "output": "CRITTER_TARSIER.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "tarsier",
        "reveal_search": "Tarsier",
        "description": "Can you guess the animal with the biggest eyes? 👀\n\nGuess the mystery animal from 3 clues:\n1️⃣ Each of its eyes is as big as its whole BRAIN — the biggest eye-to-body ratio of any mammal!\n2️⃣ Its eyes are so huge they cannot move, so it swivels its whole head almost all the way around!\n3️⃣ It is a tiny night hunter that jumps like a little frog to catch insects!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, tarsier, big eyes animal, biggest eyes, night animals, southeast asia animals, weird mammals, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the animal with the most enormous eyes in the world? Three huge clues!
Clue one! Each one of this animal's eyes is actually the same size as its entire brain — the biggest eye-to-body ratio of any mammal on Earth!
Clue two! Because its eyes are locked in their sockets, it turns its whole head around like an owl, almost a full circle, to look around!
Clue three! It is a tiny night-time hunter that hops between trees like a little frog and catches insects with lightning-fast hands!
Did you guess it? Three... Two... One...
It's the TARSIER! The big-eyed night jumper of the jungle! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key jungle night shot, 50mm lens, the dark silhouette of a tiny primate with two enormous round eyes clinging to a dark tree trunk, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Close-up shot, the dark silhouette of two giant round eyes taking up most of a small face, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide jungle shot, the dark silhouette of a tiny long-fingered animal leaping between dark tree branches at night, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a small head swivelling around to look backward over its shoulder, pure silhouette, mysterious mood, film grain",
            "Low-angle jungle shot, the dark silhouette of a big-eyed creature perched on a branch against a golden moonlit sky, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Slow Loris",
        "title": "Who dat critter? 🥺🙈 (The CUTEST animal... with a SECRET WEAPON!) #shorts",
        "output": "CRITTER_SLOW_LORIS.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "slow loris",
        "reveal_search": "Slow loris",
        "description": "Can you guess the cutest animal with a toxic secret? 🥺\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has HUGE adorable eyes and moves in slow motion, like a little furry toy!\n2️⃣ But do not be fooled — it has a toxic bite made from a poison gland in its elbow!\n3️⃣ It is one of the only venomous MAMMALS in the world!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, slow loris, cute animal, venomous mammal, toxic animal, night animals, asian animals, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the cutest animal that is secretly deadly? Three sneaky clues!
Clue one! This tiny furry animal has giant round eyes and moves in slow motion, like an adorable living teddy bear!
Clue two! But it hides a secret weapon — a poison gland in its elbow that it licks to make a toxic bite!
Clue three! It is one of only a handful of venomous mammals anywhere in the world!
Did you guess it? Three... Two... One...
It's the SLOW LORIS! The cutest little venom-dispenser in the forest! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key jungle night shot, 50mm lens, the dark silhouette of a tiny round furry primate with enormous glowing eyes holding a tree branch, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Close-up shot, the dark silhouette of two huge shiny eyes on a round fluffy face, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide jungle shot, 35mm lens, the dark silhouette of a small slow creature moving along a dark branch in a moonlit jungle, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a little face with its head turned to show a raised arm and elbow, pure silhouette, mysterious mood, film grain",
            "Low-angle jungle shot, the dark silhouette of a round-eyed creature peeking around a branch against a golden moonlit canopy, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Secretary Bird",
        "title": "Who dat critter? 🦅🦵 (The bird that STOMPS snakes to death!) #shorts",
        "output": "CRITTER_SECRETARY_BIRD.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "secretary bird",
        "reveal_search": "Secretary bird",
        "description": "Can you guess the snake-hunting bird? 🦅\n\nGuess the mystery animal from 3 clues:\n1️⃣ It hunts SNAKES by stomping them with its long powerful legs — faster than a blink!\n2️⃣ It has long eyelashes like a movie star and feathers that look like quill pens!\n3️⃣ It lives in African grasslands and can kick with a force ten times its own weight!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, secretary bird, snake hunter, stomping bird, african birds, birds with eyelashes, big birds, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the bird that is basically a martial artist? Three stomping clues!
Clue one! This tall bird hunts snakes by stomping them with its long legs, kicking faster than your eye can follow!
Clue two! It has gorgeous long eyelashes like a movie star, and the feathers on its head look exactly like old-fashioned quill pens!
Clue three! It patrols the African grasslands on foot, and its stomp lands with a force ten times its own body weight!
Did you guess it? Three... Two... One...
It's the SECRETARY BIRD! The snake-kicking supermodel of the savanna! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key savanna shot, 50mm lens, the dark silhouette of a tall bird with long legs and a little crown of feathers walking through dry grass, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide savanna shot, 35mm lens, the dark silhouette of a long-legged bird marching across golden grassland at dusk, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a proud bird face with a hooked beak and long eyelashes, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a tall bird kicking down at a snake shape in the grass, dust flying, no features visible, mysterious mood, film grain",
            "Low-angle savanna shot, the heroic dark silhouette of a crown-feathered bird striding through tall grass against a golden sunset, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Yeti Crab",
        "title": "Who dat critter? 🦞🧔 (The crab with a fluffy YETI beard!) #shorts",
        "output": "CRITTER_YETI_CRAB.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "yeti crab",
        "reveal_search": "Yeti crab",
        "description": "Can you guess the hairy deep-sea crab? 🦞\n\nGuess the mystery animal from 3 clues:\n1️⃣ Its claws are covered in fluffy golden hair, like it is wearing a furry coat!\n2️⃣ It FARMS its own food — it grows bacteria in its fur and eats it!\n3️⃣ It lives near boiling-hot vents on the deep seafloor!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, yeti crab, hairy crab, deep sea animals, hydrothermal vents, weird sea creatures, ocean animals, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the deep-sea crab that looks like a fuzzy monster? Three hairy clues!
Clue one! This crab's claws are covered in thick fluffy golden hair, making it look like it is wearing a furry coat!
Clue two! It is a tiny farmer — it grows its own food by letting bacteria grow on its fur, then eats the garden it grew!
Clue three! It lives beside boiling hot vents on the deep seafloor, in water that would cook almost anything else!
Did you guess it? Three... Two... One...
It's the YETI CRAB! The fuzzy farmer of the abyss! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key deep sea shot, 50mm lens, the dark silhouette of a small crab with fluffy hairy claws standing on dark volcanic rock near glowing vents, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Close-up shot, the dark silhouette of a crab claw covered in thick bristly hair, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide deep sea shot, 35mm lens, the dark silhouette of a hairy crab beside a chimney vent pouring dark smoke into black water, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a small furry crab waving its hairy claws in dark water, pure silhouette, mysterious mood, film grain",
            "Low-angle deep sea shot, the dark silhouette of a hairy little crab on a rocky vent against a faint orange glow from the deep, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Snow Leopard",
        "title": "Who dat critter? 🐆❄️ (The GHOST of the mountains that cannot roar!) #shorts",
        "output": "CRITTER_SNOW_LEOPARD.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "snow leopard",
        "reveal_search": "Snow leopard",
        "description": "Can you guess the ghost of the mountains? 🐆\n\nGuess the mystery animal from 3 clues:\n1️⃣ It lives so high in the snowy mountains that it is almost never seen — people call it the ghost cat!\n2️⃣ Its huge fluffy tail is as long as its whole body and wraps around it like a scarf!\n3️⃣ It CANNOT roar like a lion — it purrs and chuffs instead!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, snow leopard, ghost cat, mountain animals, big cats, snow leopard facts, animals with long tails, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the most mysterious big cat in the world? Three snowy clues!
Clue one! This cat lives so high in the freezing mountains that people almost never see it — rangers call it the ghost of the mountains!
Clue two! Its enormous fluffy tail is as long as its whole body, and it wraps around itself like a scarf to keep warm in blizzards!
Clue three! Unlike lions and tigers, it CANNOT roar — instead it makes soft chuffing sounds and purrs!
Did you guess it? Three... Two... One...
It's the SNOW LEOPARD! The purring ghost of the frozen peaks! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key mountain shot, 50mm lens, the dark silhouette of a large cat with a long fluffy tail padding through dark snow at twilight, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide mountain shot, 35mm lens, the dark silhouette of a big cat with a huge tail walking along a snowy ridge above dark cliffs, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a round leopard face with pale eyes, breath steaming, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a curled-up sleeping cat with its enormous tail wrapped around its face, no features visible, mysterious mood, film grain",
            "Low-angle mountain shot, the majestic dark silhouette of a snow leopard leaping across rocks against a golden frozen sky, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Manta Ray",
        "title": "Who dat critter? 🐟🪽 (The ocean glider with the BIGGEST brain of any fish!) #shorts",
        "output": "CRITTER_MANTA_RAY.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "manta ray",
        "reveal_search": "Manta ray",
        "description": "Can you guess the ocean's gentle flying giant? 🪽\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has enormous wing-like fins that let it GLIDE through the water like a bird!\n2️⃣ It has the BIGGEST brain of any fish and can even recognise itself in a mirror!\n3️⃣ Despite its huge mouth, it only eats tiny plankton!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, manta ray, ocean animals, smartest fish, giant ray, gliding animal, sea animals for kids, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the ocean's most graceful giant? Three gliding clues!
Clue one! This huge ocean animal has enormous wing-like fins and glides through the water like a bird flying through the sky!
Clue two! It has the biggest brain of any fish, and scientists proved it can even recognise its own reflection in a mirror!
Clue three! Even though its mouth is enormous, it only ever eats tiny floating plankton, like a gentle underwater vacuum!
Did you guess it? Three... Two... One...
It's the MANTA RAY! The smartest glider in the ocean! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key open ocean shot, 50mm lens, the dark silhouette of a huge flat animal with wing-like fins gliding through deep blue water, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide ocean shot, 35mm lens, the dark silhouette of an enormous winged ray soaring past a school of small dark fish, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a wide flat head with forward-facing fins like little horns, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a giant ray doing a graceful somersault near the dark surface, no features visible, mysterious mood, film grain",
            "Low-angle ocean shot, the majestic dark silhouette of a manta ray soaring upward toward golden sunlit water, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Echidna",
        "title": "Who dat critter? 🦔🥚 (It's a spiky anteater that LAYS EGGS!) #shorts",
        "output": "CRITTER_ECHIDNA.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "echidna",
        "reveal_search": "Echidna",
        "description": "Can you guess the spiky egg-laying mammal? 🦔\n\nGuess the mystery animal from 3 clues:\n1️⃣ It is covered in sharp spines, like a walking cactus!\n2️⃣ It is one of only two mammals in the world that LAY EGGS!\n3️⃣ It slurps up ants and termites with a super long sticky tongue!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, echidna, egg laying mammal, spiky animal, anteater, australian animals, fun animal facts, animal quiz for kids, educational kids video, viral shorts",
        "script": """Can you guess the spiky animal that lays eggs? Three prickly clues!
Clue one! This animal is covered in thousands of sharp spines, like a walking cactus!
Clue two! It is one of only two mammals in the world that lay eggs instead of giving birth!
Clue three! It has no teeth, but it uses a super long sticky tongue to slurp up ants and termites!
Did you guess it? Three... Two... One...
It's the ECHIDNA! Australia's spiky little egg-laying hedgehog! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key bushland shot, 50mm lens, the dark silhouette of a small round spiky animal shuffling through dry grass, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide outback shot, 35mm lens, the dark silhouette of a spiky ball-shaped animal crossing a dusty track at dusk, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a long thin snout with a sticky tongue curling out, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a spiky animal digging into the ground with strong front claws, no features visible, mysterious mood, film grain",
            "Low-angle bushland shot, the dark silhouette of a spiky echidna rolling into a protective ball against golden sunset light, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Kakapo",
        "title": "Who dat critter? 🦜🌙 (The fat owl parrot that SMELLS like flowers!) #shorts",
        "output": "CRITTER_KAKAPO.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "kakapo",
        "reveal_search": "Kakapo",
        "description": "Can you guess the night parrot with a sweet smell? 🦜\n\nGuess the mystery animal from 3 clues:\n1️⃣ It is the HEAVIEST parrot in the world and cannot fly!\n2️⃣ It is awake at night and smells a bit like flowers and honey!\n3️⃣ It only lives in New Zealand, and fewer than 250 are left!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, kakapo, flightless parrot, night parrot, new zealand animals, rare animals, owl parrot, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the chubby parrot that cannot fly? Three feathery clues!
Clue one! This is the heaviest parrot on Earth, and it cannot fly at all!
Clue two! It only comes out at night and smells like flowers and honey!
Clue three! It lives only in New Zealand, and there are fewer than 250 left in the whole world!
Did you guess it? Three... Two... One...
It's the KAKAPO! The adorable mossy night owl-parrot! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key forest shot, 50mm lens, the dark silhouette of a large round flightless bird waddling through ferns in moonlight, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide forest shot, 35mm lens, the dark silhouette of a big mossy bird sitting motionless on a low branch, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a round owl-like face with huge dark eyes, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a chubby parrot sniffing flowers on the forest floor at night, no features visible, mysterious mood, film grain",
            "Low-angle forest shot, the dark silhouette of a kakapo stretching its stubby wings under moonlight, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Coconut Crab",
        "title": "Who dat critter? 🦀🌴 (The biggest crab on land — it climbs TREES!) #shorts",
        "output": "CRITTER_COCONUT_CRAB.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "coconut crab",
        "reveal_search": "Coconut crab",
        "description": "Can you guess the giant tree-climbing crab? 🦀\n\nGuess the mystery animal from 3 clues:\n1️⃣ It is the LARGEST land crab on Earth, bigger than a dinner plate!\n2️⃣ It can climb tall palm trees to snack on coconuts!\n3️⃣ It can live for up to 60 years and stretch its legs over a metre wide!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, coconut crab, giant crab, tree climbing crab, biggest crab, island animals, crabs, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the giant crab that climbs trees? Three shell-tapping clues!
Clue one! This crab is the biggest land-living crab on Earth, big enough to sit on a dinner plate with room to spare!
Clue two! Its claws are so strong they can crack open a coconut, and it climbs palm trees to get one!
Clue three! It can live for sixty years and stretch its legs over a metre wide!
Did you guess it? Three... Two... One...
It's the COCONUT CRAB! The gentle giant of tropical islands! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key tropical night shot, 50mm lens, the dark silhouette of an enormous crab with long legs climbing a palm tree trunk, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide island shot, 35mm lens, the dark silhouette of a dinner-plate-sized crab crossing the sand near the shore, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a massive claw cracking open a coconut, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a giant crab perched high in a palm crown, no features visible, mysterious mood, film grain",
            "Low-angle island shot, the dark silhouette of a coconut crab stretching its huge legs against a twilight sky, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Blue Dragon",
        "title": "Who dat critter? 🐉🌊 (The tiny ocean dragon that EATS stingers!) #shorts",
        "output": "CRITTER_BLUE_DRAGON.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "blue dragon",
        "reveal_search": "Blue dragon sea slug",
        "description": "Can you guess the ocean's tiny blue dragon? 🐉\n\nGuess the mystery animal from 3 clues:\n1️⃣ It looks like a tiny blue dragon with wing-like arms, but it is actually a sea slug!\n2️⃣ It floats upside down on the ocean surface, riding the wind and currents!\n3️⃣ It eats deadly man-o-war stingers and keeps their venom to defend itself!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, blue dragon sea slug, glaucus atlanticus, ocean animals, weird sea creatures, sea slug, venomous animals, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the tiny dragon that floats on the ocean? Three blue clues!
Clue one! This creature looks exactly like a miniature blue dragon with feathery wings, but it is really a sea slug!
Clue two! It spends its whole life floating upside down on the ocean surface, carried by the wind and currents!
Clue three! It eats the venomous tentacles of man-o-war jellyfish and keeps their stinging power for itself!
Did you guess it? Three... Two... One...
It's the BLUE DRAGON! The most beautiful stinger in the sea! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key ocean surface shot, 50mm lens, the dark silhouette of a tiny winged creature floating on rippling water, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide ocean shot, 35mm lens, the dark silhouette of a small dragon-like shape drifting on blue waves, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of feathery finger-like arms spread wide like tiny wings, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a tiny blue creature floating upside down on the surface, no features visible, mysterious mood, film grain",
            "Low-angle ocean shot, the dark silhouette of a delicate blue dragon riding a gentle wave crest, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Pink Fairy Armadillo",
        "title": "Who dat critter? 🦔💗 (The tiny armadillo with a PINK shell!) #shorts",
        "output": "CRITTER_PINK_FAIRY_ARMADILLO.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "pink fairy armadillo",
        "reveal_search": "Pink fairy armadillo",
        "description": "Can you guess the tiniest armored digger? 🦔\n\nGuess the mystery animal from 3 clues:\n1️⃣ It is the SMALLEST armadillo in the world, about the size of a guinea pig!\n2️⃣ Its back has a beautiful pale pink shell!\n3️⃣ It lives underground in sandy deserts and is almost never seen!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, pink fairy armadillo, smallest armadillo, desert animals, burrowing animals, pink shell animal, rare animals, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the tiniest armored animal in the world? Three sandy clues!
Clue one! This animal is the smallest armadillo species, growing only to the size of a guinea pig!
Clue two! Its back is covered in a lovely pale pink shell, just like a real fairy!
Clue three! It spends nearly its whole life burrowing through desert sand and is almost never spotted!
Did you guess it? Three... Two... One...
It's the PINK FAIRY ARMADILLO! The rosy little digger of the desert! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key desert shot, 50mm lens, the dark silhouette of a small armored animal with a domed shell shuffling through sand, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide desert shot, 35mm lens, the dark silhouette of a tiny armadillo burrowing into a sandy mound, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a small rounded shell with scalloped edges, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a tiny armored creature disappearing into a sand tunnel, no features visible, mysterious mood, film grain",
            "Low-angle desert shot, the dark silhouette of a delicate armored animal pausing on a dune under golden light, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Red-Lipped Batfish",
        "title": "Who dat critter? 🐟💋 (It WALKS on the seafloor with big red lips!) #shorts",
        "output": "CRITTER_BATFISH.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "red-lipped batfish",
        "reveal_search": "Red-lipped batfish",
        "description": "Can you guess the fish with movie-star lips? 💋\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has bright RED lips that look like it is wearing lipstick!\n2️⃣ It does not swim much — it WALKS along the seafloor using its fins like legs!\n3️⃣ It lives near the Galapagos Islands in deep dark water!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, red lipped batfish, batfish, weird fish, galapagos animals, deep sea fish, fish that walk, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the fish that wears bright red lipstick? Three fancy clues!
Clue one! This fish has big bright red lips, as if it just put on lipstick for a night out!
Clue two! It rarely swims — instead it walks along the ocean floor using its fins like little legs!
Clue three! It lives in the deep water around the Galapagos Islands, far from where divers usually go!
Did you guess it? Three... Two... One...
It's the RED-LIPPED BATFISH! The most fashionable fish in the sea! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key deep sea shot, 50mm lens, the dark silhouette of a small flat fish standing on the seafloor, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide ocean floor shot, 35mm lens, the dark silhouette of a fish with wing-like fins walking across the sand, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a pouty fish face with big glossy lips, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a batfish strutting along the seabed like it is on a runway, no features visible, mysterious mood, film grain",
            "Low-angle deep sea shot, the dark silhouette of a batfish facing the camera with fins planted, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Dumbo Octopus",
        "title": "Who dat critter? 🐙👂 (It has cute EARS like a baby elephant!) #shorts",
        "output": "CRITTER_DUMBO_OCTOPUS.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "dumbo octopus",
        "reveal_search": "Dumbo octopus",
        "description": "Can you guess the octopus with adorable ears? 🐙\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has two floppy fins on its head that look just like big ears!\n2️⃣ It lives deeper than almost any other octopus, over 4,000 metres down!\n3️⃣ It was named after the famous flying baby elephant with big ears!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, dumbo octopus, deep sea octopus, deepest living octopus, ocean animals, weird sea creatures, octopus facts, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the deep-sea octopus with floppy ears? Three adorable clues!
Clue one! This octopus has two soft fins that stick out like big ears on the sides of its head!
Clue two! It holds the record for the deepest-living octopus, found more than four thousand metres below the surface!
Clue three! It is named after Dumbo, the baby elephant who could fly using his giant ears!
Did you guess it? Three... Two... One...
It's the DUMBO OCTOPUS! The cutest creature of the deep! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key deep ocean shot, 50mm lens, the dark silhouette of a small round octopus with ear-like fins floating in the abyss, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide deep sea shot, 35mm lens, the dark silhouette of a tiny octopus drifting over a dark seabed, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a soft round head with two floppy fins like big ears, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a small octopus flapping its ear fins as it glides, no features visible, mysterious mood, film grain",
            "Low-angle deep sea shot, the dark silhouette of a small octopus swimming upward past a faint bioluminescent glow, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Frilled Shark",
        "title": "Who dat critter? 🦈🐍 (The eel-like shark from the DINOSAUR age!) #shorts",
        "output": "CRITTER_FRILLED_SHARK.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "frilled shark",
        "reveal_search": "Frilled shark",
        "description": "Can you guess the living fossil shark? 🦈\n\nGuess the mystery animal from 3 clues:\n1️⃣ It looks like a snake with a shark's tail and a frilly gill collar!\n2️⃣ It has 300 needle-sharp teeth arranged in 25 rows!\n3️⃣ Its ancestors swam the oceans 80 MILLION years ago!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, frilled shark, living fossil shark, ancient shark, deep sea shark, eel shark, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the shark that looks like a sea serpent? Three ancient clues!
Clue one! This shark has a long snake-like body and frilly gills around its neck, like a scaly collar!
Clue two! Its mouth is packed with three hundred needle-sharp teeth arranged in twenty-five rows!
Clue three! Sharks just like it were swimming the oceans eighty million years ago, even before the dinosaurs disappeared!
Did you guess it? Three... Two... One...
It's the FRILLED SHARK! A living fossil from the deep! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key deep ocean shot, 50mm lens, the dark silhouette of a long snake-like shark with a frilly collar gliding through the abyss, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide deep sea shot, 35mm lens, the dark silhouette of an eel-like shark with rippling frills swimming in black water, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a narrow head with rows of needle teeth and a frilled gill collar, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a frilled shark curling its serpent-like body through the deep, no features visible, mysterious mood, film grain",
            "Low-angle deep sea shot, the dark silhouette of a frilled shark moving toward faint blue light, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Gerenuk",
        "title": "Who dat critter? 🦌🦒 (It stands on TWO LEGS to eat like a giraffe!) #shorts",
        "output": "CRITTER_GERENUK.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "gerenuk",
        "reveal_search": "Gerenuk",
        "description": "Can you guess the giraffe-necked antelope? 🦌\n\nGuess the mystery animal from 3 clues:\n1️⃣ It is a gazelle with an extra-long neck, nicknamed the giraffe-necked antelope!\n2️⃣ It can stand up on its HIND LEGS to reach high leaves!\n3️⃣ It lives in the dry scrublands of Africa and can go a long time without water!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, gerenuk, giraffe necked antelope, african animals, standing on hind legs, gazelle facts, antelope facts, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the antelope that stands up on two legs? Three stretchy clues!
Clue one! This animal is a gazelle with a surprisingly long neck, so people call it the giraffe-necked antelope!
Clue two! To reach the tastiest leaves, it balances on its hind legs like a dancing ballerina!
Clue three! It lives in dry African scrubland and hardly ever needs to drink water!
Did you guess it? Three... Two... One...
It's the GERENUK! The acrobat of the African plains! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key savanna shot, 50mm lens, the dark silhouette of a slender antelope with a long neck reaching for leaves, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide savanna shot, 35mm lens, the dark silhouette of a giraffe-necked gazelle standing tall among acacia trees, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a long elegant neck and a small head with large eyes, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a gerenuk balancing on its hind legs to nibble high branches, no features visible, mysterious mood, film grain",
            "Low-angle savanna shot, the dark silhouette of a gerenuk stretching upward against a golden dusk sky, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Tuatara",
        "title": "Who dat critter? 🦎👁️ (It has a real THIRD EYE on its head!) #shorts",
        "output": "CRITTER_TUATARA.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "tuatara",
        "reveal_search": "Tuatara",
        "description": "Can you guess the reptile with a third eye? 🦎\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has a THIRD eye hidden on top of its head!\n2️⃣ It is not a lizard — it is the last survivor of a reptile family from 200 MILLION years ago!\n3️⃣ It only lives on the islands of New Zealand and can live over 100 years!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, tuatara, third eye animal, ancient reptile, living fossil, new zealand reptiles, reptile facts, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the reptile with a real third eye? Three ancient clues!
Clue one! This reptile has a third eye on top of its head, complete with a lens and retina, though it stays hidden under scales!
Clue two! It is not actually a lizard — it is the last survivor of a reptile group that lived alongside the dinosaurs!
Clue three! It lives only on small islands of New Zealand and can live for over one hundred years!
Did you guess it? Three... Two... One...
It's the TUATARA! The living dinosaur of New Zealand! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key night forest shot, 50mm lens, the dark silhouette of a spiny ancient reptile perched on a mossy rock, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide island shot, 35mm lens, the dark silhouette of a crested reptile basking on a boulder in moonlight, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a scaly lizard-like head with a bright third eye spot on top, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a spiny-backed reptile crawling through fern shadows, no features visible, mysterious mood, film grain",
            "Low-angle night shot, the dark silhouette of a tuatara lifting its head under a full moon, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Aardvark",
        "title": "Who dat critter? 🐜🐘 (The pig-like digger that hunts ANTS at night!) #shorts",
        "output": "CRITTER_AARDVARK.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "aardvark",
        "reveal_search": "Aardvark",
        "description": "Can you guess the animal that starts every dictionary? 🐜\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has a pig-like snout, rabbit ears and a kangaroo tail, all in one animal!\n2️⃣ It uses a super long sticky tongue to eat ants and termites!\n3️⃣ It is a nocturnal digger from Africa, and its name means earth pig!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, aardvark, earth pig, ant eater, african animals, nocturnal animals, burrowing animals, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the animal that looks like a mash-up of three others? Three digging clues!
Clue one! This animal has the snout of a pig, the ears of a rabbit and the tail of a kangaroo, all rolled into one!
Clue two! It uses its long sticky tongue to vacuum up ants and termites by the thousands!
Clue three! It lives in Africa, digs burrows with strong claws, and its name literally means earth pig!
Did you guess it? Three... Two... One...
It's the AARDVARK! The night-time ant vacuum of Africa! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key savanna night shot, 50mm lens, the dark silhouette of a long-snouted animal digging into a termite mound, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide savanna shot, 35mm lens, the dark silhouette of a pig-like animal with rabbit ears ambling across the plains at dusk, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a long tube snout with a curling sticky tongue, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of an aardvark with powerful claws tearing open a mound, no features visible, mysterious mood, film grain",
            "Low-angle savanna shot, the dark silhouette of an aardvark on alert with ears pricked against the sunset, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Meerkat",
        "title": "Who dat critter? 🐾☀️ (It stands on GUARD DUTY like a tiny soldier!) #shorts",
        "output": "CRITTER_MEERKAT.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "meerkat",
        "reveal_search": "Meerkat",
        "description": "Can you guess the desert animal that stands at attention? 🐾\n\nGuess the mystery animal from 3 clues:\n1️⃣ It stands up on its hind legs to keep guard while its family eats!\n2️⃣ It lives in big families called mobs in the dry deserts of southern Africa!\n3️⃣ It can close its eyes to dig through sand, and the dark circles around its eyes block the glare!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, meerkat, desert animals, african animals, animals that stand up, meerkat facts, mob animals, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the tiny desert sentry? Three sandy clues!
Clue one! This animal stands up straight on its hind legs like a little soldier to watch for danger while its family eats!
Clue two! It lives in large families called mobs, where everyone takes turns being the lookout!
Clue three! The dark rings around its eyes act like built-in sunglasses, letting it stare into the bright desert sun!
Did you guess it? Three... Two... One...
It's the MEERKAT! The brave little guard of the desert! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key desert shot, 50mm lens, the dark silhouette of a small mongoose standing upright on its hind legs, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide savanna shot, 35mm lens, the dark silhouette of a meerkat perched on a rock scanning the horizon, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a small pointed face with dark eye patches and perked ears, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a row of meerkats standing at attention around their burrow, no features visible, mysterious mood, film grain",
            "Low-angle desert shot, the dark silhouette of a meerkat lookout on a termite mound against golden light, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Walrus",
        "title": "Who dat critter? 🦭🦷 (It has giant TUSKS and mustaches made of whiskers!) #shorts",
        "output": "CRITTER_WALRUS.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "walrus",
        "reveal_search": "Walrus",
        "description": "Can you guess the tusked giant of the Arctic? 🦭\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has two enormous tusks that can grow up to a metre long!\n2️⃣ Its face is covered in thousands of stiff whiskers that feel for food on the seafloor!\n3️⃣ It can weigh as much as a small car, with skin over 4 centimetres thick!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, walrus, arctic animals, animals with tusks, walrus facts, marine mammals, whiskers animal, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the heavyweight of the frozen north? Three tusky clues!
Clue one! This massive animal has two giant tusks that can grow as long as a metre!
Clue two! Its whiskers are super sensitive and act like feelers that sweep the seafloor for food!
Clue three! A big adult can weigh as much as a small car, with skin thicker than four centimetres to survive the ice!
Did you guess it? Three... Two... One...
It's the WALRUS! The tusked gentleman of the Arctic! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key arctic shot, 50mm lens, the dark silhouette of a huge tusked animal hauled out on an ice floe, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide arctic shot, 35mm lens, the dark silhouette of an enormous tusked sea mammal resting on dark ice, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a whiskered face with two long curving tusks, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a walrus slipping into dark arctic water, no features visible, mysterious mood, film grain",
            "Low-angle arctic shot, the dark silhouette of a walrus raising its tusks against a frozen twilight sky, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Puffin",
        "title": "Who dat critter? 🐧🪿 (The clown of the sea with a rainbow beak!) #shorts",
        "output": "CRITTER_PUFFIN.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "puffin",
        "reveal_search": "Puffin",
        "description": "Can you guess the seabird with a rainbow beak? 🐧\n\nGuess the mystery animal from 3 clues:\n1️⃣ Its beak is striped in bright orange, yellow and blue, like a tiny parrot!\n2️⃣ It can hold up to 60 fish in its beak at one time!\n3️⃣ It can fly AND swim, flapping underwater like it is flying through the sea!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, puffin, clown of the sea, seabirds, puffin facts, rainbow beak bird, atlantic animals, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the seabird they call the clown of the sea? Three feathery clues!
Clue one! This bird has a striking beak striped in bright orange, yellow and blue!
Clue two! Its beak has a special hinge so it can clamp onto up to sixty small fish at once!
Clue three! It is an ace at both flying and swimming, flapping its wings underwater as if flying through the sea!
Did you guess it? Three... Two... One...
It's the PUFFIN! The colorful clown of the Atlantic cliffs! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key coastal shot, 50mm lens, the dark silhouette of a stout seabird with a large rounded beak on a cliff ledge, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide coastal shot, 35mm lens, the dark silhouette of a puffin standing on a dark sea cliff, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a bird head with a deep grooved triangular beak, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a puffin with fish lined in its beak landing on rocks, no features visible, mysterious mood, film grain",
            "Low-angle coastal shot, the dark silhouette of a puffin in flight over dark water at dusk, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Macaroni Penguin",
        "title": "Who dat critter? 🐧🎩 (It has a fabulous yellow HAIRCUT on its head!) #shorts",
        "output": "CRITTER_MACARONI_PENGUIN.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "macaroni penguin",
        "reveal_search": "Macaroni penguin",
        "description": "Can you guess the penguin with a fancy hairdo? 🐧\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has bright yellow feathers sprouting from its forehead like a fancy hairdo!\n2️⃣ There are more of them than any other penguin on Earth!\n3️⃣ They hop like little kangaroos to climb steep rocky cliffs!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, macaroni penguin, penguin facts, yellow hair penguin, antarctic animals, most penguins, crested penguin, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the penguin with the flashiest hair in the Antarctic? Three feathery clues!
Clue one! This penguin wears bright yellow feathers on top of its head like a stylish crest!
Clue two! There are more of them than any other penguin species on the planet!
Clue three! To reach their nests, they hop up steep cliffs like tiny black-and-white kangaroos!
Did you guess it? Three... Two... One...
It's the MACARONI PENGUIN! The rockstar of the penguin world! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key antarctic shot, 50mm lens, the dark silhouette of a crested penguin with feathery head plumes on a rocky shore, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide antarctic shot, 35mm lens, the dark silhouette of a colony of crested penguins on dark cliffs, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a penguin head with a wild feathered crest, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a macaroni penguin hopping across rocks like a kangaroo, no features visible, mysterious mood, film grain",
            "Low-angle antarctic shot, the dark silhouette of a macaroni penguin against a twilight ice sky, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Sugar Glider",
        "title": "Who dat critter? 🐭🪂 (It can PARACHUTE through the air between trees!) #shorts",
        "output": "CRITTER_SUGAR_GLIDER.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "sugar glider",
        "reveal_search": "Sugar glider",
        "description": "Can you guess the flying marsupial? 🐭\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has flaps of skin that let it GLIDE over 50 metres between trees!\n2️⃣ It is a tiny marsupial from Australia that carries its babies in a pouch!\n3️⃣ It loves sweet things — which is why it is named after sugar!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, sugar glider, flying marsupial, australian animals, gliding animals, pouch animals, sugar glider facts, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the tiny parachuting marsupial? Three glide-tastic clues!
Clue one! This tiny animal has stretchy skin flaps that let it glide more than fifty metres between trees!
Clue two! It comes from Australia and is a marsupial, so its babies grow in a cozy pouch!
Clue three! It has a real sweet tooth and loves nectar and fruit — that is why it is called a sugar glider!
Did you guess it? Three... Two... One...
It's the SUGAR GLIDER! The cutest little parachutist in the forest! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key forest night shot, 50mm lens, the dark silhouette of a tiny animal with stretched skin gliding between two trees, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide forest shot, 35mm lens, the dark silhouette of a small glider leaping off a branch into the night air, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a small face with huge glossy eyes and tiny rounded ears, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a sugar glider parachuting down toward a dark forest floor, no features visible, mysterious mood, film grain",
            "Low-angle forest shot, the dark silhouette of a sugar glider soaring across a moonlit gap, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Colugo",
        "title": "Who dat critter? 🦌🛸 (It's called a flying lemur but it's NOT a lemur!) #shorts",
        "output": "CRITTER_COLUGO.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "colugo",
        "reveal_search": "Colugo",
        "description": "Can you guess the gliding mystery mammal? 🦌\n\nGuess the mystery animal from 3 clues:\n1️⃣ People call it a flying lemur, but it is NOT a lemur!\n2️⃣ Its skin connects its neck, legs and tail, letting it glide over 100 metres!\n3️⃣ It hangs upside down in trees like a bat and eats leaves and flowers!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, colugo, flying lemur, gliding mammal, southeast asia animals, canopy animals, gliding animal, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the animal nicknamed the flying lemur? Three gliding clues!
Clue one! Despite its nickname, this animal is not a lemur at all — it belongs to its own special family!
Clue two! A sheet of skin stretches from its neck to its tail, letting it glide more than one hundred metres between trees!
Clue three! It spends its days hanging upside down like a bat, nibbling leaves and flowers!
Did you guess it? Three... Two... One...
It's the COLUGO! The champion glider of the rainforest canopy! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key rainforest shot, 50mm lens, the dark silhouette of a gliding mammal with a full skin cloak stretched between limbs, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide canopy shot, 35mm lens, the dark silhouette of a colugo gliding high above the dark forest, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a round face with big eyes hanging upside down, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a colugo clinging flat to a tree trunk like a living blanket, no features visible, mysterious mood, film grain",
            "Low-angle rainforest shot, the dark silhouette of a colugo sailing across a moonlit gap, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Golden Lion Tamarin",
        "title": "Who dat critter? 🦧👑 (A tiny monkey with a LION'S MANE of golden fur!) #shorts",
        "output": "CRITTER_GOLDEN_TAMARIN.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "golden lion tamarin",
        "reveal_search": "Golden lion tamarin",
        "description": "Can you guess the tiny monkey with a lion's mane? 🦧\n\nGuess the mystery animal from 3 clues:\n1️⃣ It is a tiny monkey with a dramatic mane of golden orange fur!\n2️⃣ It lives high in the rainforest trees of Brazil and weighs less than a can of soda!\n3️⃣ It uses high-pitched chirps to tell its family where the food is!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, golden lion tamarin, tamarin monkey, rainforest monkeys, brazil animals, golden mane monkey, monkey facts, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the monkey that looks like a tiny lion? Three golden clues!
Clue one! This little monkey wears a flowing mane of golden orange fur, just like a lion!
Clue two! It lives in the treetops of Brazil's rainforest and weighs less than a can of soda!
Clue three! Families chirp to each other in high-pitched calls to share where the tastiest fruit is hiding!
Did you guess it? Three... Two... One...
It's the GOLDEN LION TAMARIN! The king of the rainforest canopy! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key rainforest shot, 50mm lens, the dark silhouette of a tiny monkey with a fluffy mane leaping between branches, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide canopy shot, 35mm lens, the dark silhouette of a small maned monkey perched on a mossy branch, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a tiny monkey face framed by a great fluffy mane, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a golden tamarin family scrambling through the treetops, no features visible, mysterious mood, film grain",
            "Low-angle rainforest shot, the dark silhouette of a golden lion tamarin against a warm sunset canopy, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Emperor Tamarin",
        "title": "Who dat critter? 🐒👨🦳 (It has a giant white MUSTACHE like a wise king!) #shorts",
        "output": "CRITTER_EMPEROR_TAMARIN.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "emperor tamarin",
        "reveal_search": "Emperor tamarin",
        "description": "Can you guess the monkey with the grand mustache? 🐒\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has a long white mustache that droops past its shoulders!\n2️⃣ It was named after an emperor who also had a famous mustache!\n3️⃣ It lives in the Amazon rainforest and loves to leap between branches!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, emperor tamarin, mustache monkey, amazon rainforest animals, tamarin monkey, white mustache monkey, monkey facts, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the monkey with the majestic mustache? Three royal clues!
Clue one! This small monkey has a long white mustache that droops down past its chin and shoulders!
Clue two! It is named after an emperor famous for his enormous mustache!
Clue three! It lives in the Amazon rainforest and leaps expertly from branch to branch high in the canopy!
Did you guess it? Three... Two... One...
It's the EMPEROR TAMARIN! The most dashing monkey in the jungle! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key rainforest shot, 50mm lens, the dark silhouette of a small monkey with a long drooping mustache perched on a vine, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide canopy shot, 35mm lens, the dark silhouette of a mustached monkey swinging through the dark forest, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a monkey face with a magnificent long white mustache, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of an emperor tamarin leaping between branches in the canopy, no features visible, mysterious mood, film grain",
            "Low-angle rainforest shot, the dark silhouette of an emperor tamarin staring out from the treetops, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
    {
        "topic": "Serval",
        "title": "Who dat critter? 🐆🦘 (The cat with HUGE ears that jumps like a kangaroo!) #shorts",
        "output": "CRITTER_SERVAL.mp4",
        "voice": "en-GB-RyanNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "reveal_word": "serval",
        "reveal_search": "Serval",
        "description": "Can you guess the big-eared jumping cat? 🐆\n\nGuess the mystery animal from 3 clues:\n1️⃣ It has the LARGEST ears of any cat, built to hear prey moving underground!\n2️⃣ It can leap 3 metres straight up to catch birds mid-air!\n3️⃣ It lives in the grasslands of Africa and is an expert mouser!\n\nDrop your guess before 3...2...1! 👇\n\n🐾 Subscribe for more fun animal guessing games!",
        "tags": "who dat critter, serval, big ear cat, african wildcat, jumping cat, savanna animals, wild cat facts, serval cat, fun animal facts, animal quiz for kids, viral shorts",
        "script": """Can you guess the wild cat with the giant ears? Three leaping clues!
Clue one! This cat has the largest ears of any cat species, perfectly tuned to hear tiny prey moving underground!
Clue two! It can spring three metres straight into the air to snatch birds in mid-flight!
Clue three! It prowls the tall grasslands of Africa and is one of the best mousers on the planet!
Did you guess it? Three... Two... One...
It's the SERVAL! The kangaroo of the cat family! Subscribe for more awesome animal guessing games!""",
        "prompts": [
            "Low-key savanna shot, 50mm lens, the dark silhouette of a spotted cat with enormous ears pausing in tall grass, a glowing question mark, no features visible, mysterious, cinematic haze, film grain",
            "Wide savanna shot, 35mm lens, the dark silhouette of a long-legged spotted cat walking through golden grass at dusk, no features visible, mysterious mood, film grain",
            "Close-up shot, the dark silhouette of a cat head with huge rounded ears and bright eyes, pure silhouette, dramatic rim light, mysterious mood, film grain",
            "Wide shot, the dark silhouette of a serval leaping straight up to catch prey, no features visible, mysterious mood, film grain",
            "Low-angle savanna shot, the dark silhouette of a serval springing high against the setting sun, rim light, silhouette only, mysterious mood, film grain",
        ],
    },
]

# ──────────────────────────────────────────────────────────────
# RichRules — high-RPM money psychology shorts
# ──────────────────────────────────────────────────────────────
MONEY_VIDEOS = [
    {
        "topic": "Why Lottery Winners Go Broke",
        "title": "Lottery Winners Go BROKE in 5 Years 💸😱 (70% Do!) #shorts",
        "output": "MONEY_LOTTERY_WINNERS.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 70,
        "highlight_color": (255, 215, 0, 255),
        "caption_position": "center",
        "script": """Think winning the lottery makes you rich? Think again. Nearly seventy percent of lottery winners end up broke within five years. Yes, you heard that right. When millions hit your bank account, the spending starts. Sports cars, mansions, bad investments. Old friends and even family come crawling out of the woodwork with their hands out. And most winners never learned how to manage that kind of money, so it vanishes faster than it arrived. The real lesson? Getting rich quick is a trap. Getting rich slow is the actual win. Save this video, and follow for the money rules they never taught you in school!""",
        "prompts": [
            "Hyper-saturated brainrot collage of a massive golden lottery ball bursting into confetti while dollar bills rain down, then the golden ball crumbles into dust, dark background with glowing neon text reading 70 PERCENT BROKE, chaotic dopamine overload, glitch artifacts, 8k vertical",
            "A shocked confused person silhouette buried under a pile of money while greedy hands reach in from all sides grabbing bills, cartoon brainrot style, flashing neon red warning signs, glitch artifacts, money energy, 8k vertical",
            "A luxury mansion being sucked into a giant vacuum cleaner while sports cars fall into a black hole, dollar bills flying everywhere, brainrot meme energy, neon pink and gold lighting, chaos, 8k vertical",
            "A golden coin balance scale where one side holds a tiny stack of coins labeled SLOW WIN and the other holds a giant crumbling tower of lottery tickets labeled RICH QUICK, glowing arrows and labels, clean infographic with brainrot glow, 8k vertical",
            "A confident character standing tall on a solid pyramid of coins stacking upward while a defeated character slides off a crumbling tower of lottery tickets, victory pose, golden hour glow, brainrot meme style, 8k vertical",
        ],
    },
]

# ──────────────────────────────────────────────────────────────
# Folks — software tips / fixes / bug alerts (first short!)
# ──────────────────────────────────────────────────────────────
FOLKS_VIDEOS = [
    {
        "topic": "Clipboard Fix",
        "title": "Ctrl+C Stopped Working? 10-Second Fix 💻⚡ #shorts",
        "output": "FOLKS_CLIPBOARD_FIX.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "clipboard_fix",
        "description": "Ctrl+C just stopped working? Here's the 10-second fix! ⚡\n\nIn this quick fix:\n0:00 The problem — copy & paste dead\n0:03 The 10-second fix\n0:04 Step 1: Press Ctrl+Shift+Esc to open Task Manager\n0:06 Step 2: Find 'Windows Explorer'\n0:08 Step 3: Right-click → Restart\n0:12 Done! Copy & paste works again\n\n💡 Save this video — it WILL happen again!\n🔔 Follow for more PC fixes like this!",
        "tags": "copy paste not working, ctrl c not working, clipboard fix, windows explorer restart, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, keyboard shortcuts, windows problems fixed, save this video",
        "script": """Did your copy paste just stop working?
You press Ctrl C. Nothing. Ctrl V. Still nothing.
So annoying right? Here is the ten second fix.
Press Ctrl Shift Esc to open Task Manager.
Find Windows Explorer. Right click it. Click Restart.
Your screen flickers for one second. And just like that, copy and paste is back.
Save this video. Trust me, this will happen again.
Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: copy and paste stopped working, grey clipboard icon crossed out with a red slash on a dark blue gradient background, red headline text, cinematic tech mood",
            "dark UI graphic: top-down computer keyboard with the CTRL and C keycaps highlighted in glowing cyan, cyan headline 'PRESS CTRL + C', dark tech mood, clean readable key labels",
            "dark UI graphic: top-down computer keyboard with the CTRL and V keycaps highlighted in red, headline 'CTRL + V ... NOTHING', dimmed keyboard, dark tech mood, clean readable key labels",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with CTRL, SHIFT and ESC keys highlighted in cyan, a small Task Manager window popping in the corner, dark tech mood, clean readable key labels",
            "dark UI graphic: Windows Task Manager window listing running processes with the Windows Explorer row highlighted in cyan, headline 'FIND WINDOWS EXPLORER', dark tech mood, readable UI text",
            "dark UI graphic: Windows Task Manager window showing Windows Explorer with a right-click context menu, the Restart menu item highlighted in red, headline 'RIGHT CLICK → RESTART', dark tech mood",
            "dark UI graphic: dark computer screen with jagged white static scanline bands and grey flicker bars, headline 'SCREEN FLICKERS FOR 1 SECOND', glitchy tech mood",
            "dark UI graphic: clipboard icon with a glowing green checkmark, headline 'COPY & PASTE IS BACK', green light rays, dark blue gradient background, success mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Windows Update Stuck",
        "title": "Windows Update Stuck at 0%? 10-Second Fix 💾⏳ #shorts",
        "output": "FOLKS_UPDATE_STUCK.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "update_stuck",
        "description": "Windows Update stuck at 0%? Here's the 10-second fix! 💾\n\nIn this quick fix:\n0:00 The problem — update frozen at 0%\n0:03 The 10-second fix\n0:04 Step 1: Press Ctrl+Shift+Esc to open Task Manager\n0:06 Step 2: Find 'Windows Update'\n0:08 Step 3: Right-click → End Task\n0:10 Step 4: Restart the update\n0:12 Done! Downloading again\n\n💡 Save this video — it WILL get stuck again!\n🔔 Follow for more PC fixes like this!",
        "tags": "windows update stuck, windows update 0 percent, update stuck fix, windows update not working, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, windows update fix, task manager tips, save this video",
        "script": """Did your Windows Update just get stuck at zero percent?
You wait and wait, and it never moves.
So annoying right? Here is the ten second fix.
Press Ctrl Shift Esc to open Task Manager.
Find Windows Update in the list. Right click it.
Click End Task. Just like that, it's stopped.
Now restart the update. Boom. Downloading again.
Save this video. It will get stuck again.
Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: Windows update progress bar stuck at 0% on a dark blue gradient background, red alert badge, headline 'UPDATE STUCK AT 0%?', clock icon, cinematic tech mood, readable UI text",
            "dark UI graphic: progress bar frozen at 0% with a grey spinning hourglass, headline 'IT NEVER MOVES', dim dark background, cinematic tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with CTRL, SHIFT and ESC keys highlighted in cyan, a small Task Manager window popping in the corner, dark tech mood, clean readable key labels",
            "dark UI graphic: Windows Task Manager window listing running processes with the Windows Update row highlighted in cyan, headline 'FIND WINDOWS UPDATE', dark tech mood, readable UI text",
            "dark UI graphic: Windows Task Manager showing Windows Update with a right-click context menu, the End Task menu item highlighted in red, headline 'RIGHT CLICK → END TASK', dark tech mood",
            "dark UI graphic: Windows Update row in Task Manager with a red stop badge and green checkmark, headline 'END TASK DONE', dark blue gradient background, success tech mood",
            "dark UI graphic: Settings window with Update & Security highlighted and a cyan progress bar at 35%, headline 'RESTART THE UPDATE', dark tech mood, readable UI text",
            "dark UI graphic: Windows update screen showing a green progress bar at 68% with glowing arrows, headline 'BOOM. DOWNLOADING AGAIN', success light rays, tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Disk Full Fix",
        "title": "Disk Always Full? Free Gigabytes Instantly 💾🚀 #shorts",
        "output": "FOLKS_DISK_FULL.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "disk_full",
        "description": "Disk always full? Games won't install? Here's the 10-second fix! 💾\n\nIn this quick fix:\n0:00 The problem — disk 95% full\n0:03 The 10-second fix\n0:04 Step 1: Press Win + R\n0:06 Step 2: Type %temp% and press Enter\n0:08 Step 3: Press Ctrl + A to select everything\n0:10 Step 4: Press Delete (skip files in use)\n0:12 Done! Gigabytes freed instantly\n\n💡 Save this video — it WILL fill up again!\n🔔 Follow for more PC fixes like this!",
        "tags": "disk full, not enough storage, free up disk space, pc slow, delete temp files, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, free storage, clean up pc, save this video",
        "script": """Is your disk always full? Games won't even install?
You delete stuff, and it's full again the same day.
So annoying right? Here is the ten second fix.
Press Win and R at the same time. The Run box pops up.
Type percent temp percent and press Enter.
This is the junk folder. Temporary files nobody needs.
Press Ctrl A to select everything inside.
Press Delete. Files in use, just skip them.
Instantly free gigabytes of space.
Save this video. It fills up again.
Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: hard drive icon nearly full with a red 95% storage meter on a dark blue gradient background, red alert badge, headline 'DISK ALWAYS FULL?', cinematic tech mood",
            "dark UI graphic: storage meter stuck at 97% red with an X on an install button, headline 'GAMES WON'T INSTALL', dim dark background, cinematic tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with the WINDOWS and R keycaps highlighted in cyan, a small Run dialog popping in the corner, headline 'PRESS WIN + R', dark tech mood, clean readable key labels",
            "dark UI graphic: a Windows Run dialog with %temp% typed into the open field in cyan, headline 'TYPE %temp% → ENTER', dark blue gradient background, readable UI text",
            "dark UI graphic: file explorer window full of junk temp files with a red folder icon, headline 'THE JUNK FOLDER', dark tech mood, readable UI text",
            "dark UI graphic: file explorer with all junk files selected and highlighted in glowing cyan, headline 'CTRL + A → SELECT ALL', dark tech mood, readable UI text",
            "dark UI graphic: trash can icon with files falling in and a red DELETE button highlighted, headline 'PRESS DELETE', dark blue gradient, success tech mood",
            "dark UI graphic: hard drive storage meter now at 35% green with gigabytes freed sparkles, headline 'GIGABYTES FREED INSTANTLY', success light rays, tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Slow Startup Fix",
        "title": "PC Boots Super Slow? 10-Second Fix 🚀⚡ #shorts",
        "output": "FOLKS_SLOW_STARTUP.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "slow_startup",
        "description": "PC boots super slow? Here's the 10-second fix! 🚀\n\nIn this quick fix:\n0:00 The problem — slow boot\n0:03 The 10-second fix\n0:04 Step 1: Press Ctrl+Shift+Esc\n0:06 Step 2: Open the Startup tab\n0:08 Step 3: Right-click the junk apps\n0:10 Step 4: Click Disable\n0:12 Done! Faster boot\n\n💡 Save this video — junk apps multiply!\n🔔 Follow for more PC fixes like this!",
        "tags": "pc boots slow, slow startup fix, startup apps, disable startup programs, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, task manager startup, speed up pc, save this video",
        "script": """Does your PC take forever to boot?
You wait and wait at the loading screen.
So annoying right? Here is the ten second fix.
Press Ctrl Shift Esc to open Task Manager.
Click the Startup tab. You'll see everything that auto starts.
Find the junk, like OneDrive and Spotify.
Right click it. Click Disable.
Boom. Faster boot. Power on to desktop in seconds.
Save this video. Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: glowing red hourglass icon on a dark blue gradient background with a loading spinner stuck, headline 'PC BOOTS SUPER SLOW?', cinematic tech mood",
            "dark UI graphic: a dark panel listing many apps all launching at once with racing arrows, headline 'EVERYTHING AUTO-STARTS', dim dark background, cinematic tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with CTRL, SHIFT and ESC keys highlighted in cyan, a small Task Manager window popping in the corner, dark tech mood, clean readable key labels",
            "dark UI graphic: Task Manager window with the Startup tab highlighted, listing OneDrive, Spotify, Steam, Teams and Edge apps, headline 'CLICK THE STARTUP TAB', dark tech mood, readable UI text",
            "dark UI graphic: Task Manager Startup tab with the OneDrive row highlighted in cyan, headline 'DISABLE THE JUNK', dark tech mood, readable UI text",
            "dark UI graphic: Task Manager showing OneDrive with a right-click context menu, the Disable menu item highlighted in red, headline 'RIGHT CLICK → DISABLE', dark tech mood",
            "dark UI graphic: glowing green rocket icon blasting upward on a dark blue gradient, headline 'BOOM. FASTER BOOT', success light rays, tech mood",
            "dark UI graphic: green panel with a power-on to desktop speed meter maxed out, headline 'WAY FASTER BOOT', success tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Bluetooth Disappeared Fix",
        "title": "Bluetooth Disappeared? 10-Second Fix 🎧🔵 #shorts",
        "output": "FOLKS_BLUETOOTH_GONE.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "bluetooth_gone",
        "description": "Bluetooth just disappeared from Settings? Here's the 10-second fix! 🎧\n\nIn this quick fix:\n0:00 The problem — Bluetooth gone\n0:03 The 10-second fix\n0:04 Step 1: Press Win + X\n0:06 Step 2: Open Device Manager\n0:08 Step 3: Right-click Bluetooth → Disable\n0:10 Step 4: Wait 2s, Enable again\n0:12 Done! Bluetooth is back\n\n💡 Save this video — it WILL vanish again!\n🔔 Follow for more PC fixes like this!",
        "tags": "bluetooth not working, bluetooth disappeared, bluetooth missing, bluetooth fix, device manager tips, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, bluetooth reset, save this video",
        "script": """Did your Bluetooth just disappear?
It's gone from your settings.
You can't connect headphones or your mouse.
So annoying right? Here is the ten second fix.
Press Win and X. Click Device Manager.
Find Bluetooth. Right click it. Click Disable device.
Wait two seconds. Then right click again and enable it.
Boom. Bluetooth is back. It just works now.
Save this video. Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: red bluetooth icon crossed out with a red slash on a dark blue gradient background, headline 'BLUETOOTH JUST DISAPPEARED?', cinematic tech mood",
            "dark UI graphic: dark panel with headphones and a mouse icons each crossed out in red, headline 'CAN'T CONNECT ANYTHING', dim dark background, tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with the WINDOWS and X keycaps highlighted in cyan, dark tech mood, clean readable key labels",
            "dark UI graphic: Device Manager window listing Audio, Bluetooth, Cameras, Keyboards and Mice with the Bluetooth row highlighted in cyan, headline 'OPEN DEVICE MANAGER', dark tech mood, readable UI text",
            "dark UI graphic: Device Manager showing Bluetooth with a right-click context menu, the Disable device item highlighted in red, headline 'RIGHT CLICK BLUETOOTH', dark tech mood",
            "dark UI graphic: dark panel with a small timer showing 2 seconds, headline 'WAIT 2 SECONDS', dim dark background, tech mood",
            "dark UI graphic: glowing green bluetooth icon on a dark blue gradient, headline 'BOOM. BLUETOOTH IS BACK', success light rays, tech mood",
            "dark UI graphic: green panel with a connected headphone icon, headline 'CONNECT AGAIN', success tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "No Sound Fix",
        "title": "No Sound on PC? 10-Second Fix 🔇🔊 #shorts",
        "output": "FOLKS_NO_SOUND.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "no_sound",
        "description": "No sound on your PC? Here's the 10-second fix! 🔊\n\nIn this quick fix:\n0:00 The problem — no sound\n0:03 The 10-second fix\n0:04 Step 1: Press Win + R\n0:06 Step 2: Type services.msc\n0:08 Step 3: Find Windows Audio\n0:10 Step 4: Right-click → Restart\n0:12 Done! Sound is back\n\n💡 Save this video — it WILL happen again!\n🔔 Follow for more PC fixes like this!",
        "tags": "no sound windows, sound not working, audio fix, windows audio service, speaker not working, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, fix sound, save this video",
        "script": """Is your sound suddenly gone?
The volume is all the way up. But nothing plays.
So annoying right? Here is the ten second fix.
Press Win and R. Type services dot msc. Press Enter.
Find Windows Audio. Right click it. Click Restart.
Wait five seconds. Boom. Sound is back. Music on.
Save this video. Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: red speaker icon with a red slash on a dark blue gradient background, headline 'NO SOUND?', cinematic tech mood",
            "dark UI graphic: dark panel with a video player showing silent waves, headline 'STILL NOTHING', dim dark background, tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with the WINDOWS and R keycaps highlighted in cyan, a small Run dialog popping in the corner, dark tech mood, clean readable key labels",
            "dark UI graphic: a Windows Run dialog with services.msc typed into the open field in cyan, headline 'TYPE services.msc', dark blue gradient background, readable UI text",
            "dark UI graphic: Services window listing Windows Audio, Firewall, Print Spooler and Update with the Windows Audio row highlighted in cyan, headline 'FIND WINDOWS AUDIO', dark tech mood, readable UI text",
            "dark UI graphic: Services window showing Windows Audio with a right-click context menu, the Restart item highlighted in red, headline 'RIGHT CLICK → RESTART', dark tech mood",
            "dark UI graphic: dark panel with a small timer showing 5 seconds, headline 'WAIT 5 SECONDS', dim dark background, tech mood",
            "dark UI graphic: glowing green speaker icon with sound waves on a dark blue gradient, headline 'SOUND IS BACK', success light rays, tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Slow Internet Fix",
        "title": "Internet Super Slow? 10-Second Fix 🌐⚡ #shorts",
        "output": "FOLKS_SLOW_INTERNET.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "slow_internet",
        "description": "Internet super slow? Here's the 10-second fix! 🌐\n\nIn this quick fix:\n0:00 The problem — slow internet\n0:03 The 10-second fix\n0:04 Step 1: Press Win + R\n0:06 Step 2: Open CMD as admin\n0:08 Step 3: Type ipconfig /flushdns\n0:10 Step 4: Press Enter\n0:12 Done! DNS cache cleared\n\n💡 Save this video — it WILL slow down again!\n🔔 Follow for more PC fixes like this!",
        "tags": "slow internet fix, internet speed boost, flush dns, ipconfig flushdns, dns cache, faster internet, pc tips, computer fix, tech shorts, windows tips, pc troubleshooting, speed up internet, save this video",
        "script": """Is your internet super slow?
Pages keep spinning forever. Nothing loads.
So annoying right? Here is the ten second fix.
Press Win and R. Type CMD. Press Enter. Run it as admin.
Type ipconfig slash flushdns. Press Enter.
It clears the DNS cache. Boom. Internet feels faster.
Websites load fast again. Still slow? Restart your router.
Save this video. Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: red globe icon crossed out with a red slash on a dark blue gradient background, headline 'INTERNET SUPER SLOW?', cinematic tech mood",
            "dark UI graphic: dark panel with a browser tab showing an endless loading spinner, headline 'NOTHING LOADS', dim dark background, tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with the WINDOWS and R keycaps highlighted in cyan, a small Run dialog popping in the corner, dark tech mood, clean readable key labels",
            "dark UI graphic: a Windows Run dialog with cmd typed into the open field in cyan, headline 'OPEN COMMAND PROMPT', dark blue gradient background, readable UI text",
            "dark UI graphic: black command prompt window with the cyan command 'ipconfig /flushdns' typed in and the success message 'Successfully flushed the DNS Resolver Cache', headline 'RUN AS ADMIN', dark tech mood",
            "dark UI graphic: glowing green globe icon on a dark blue gradient, headline 'DNS CACHE CLEARED', success light rays, tech mood",
            "dark UI graphic: green panel with a rocket meter showing fast loading, headline 'INSTANT BOOST', success tech mood",
            "dark UI graphic: dim panel with a router icon and a restart arrow, headline 'STILL SLOW?', dim dark background, tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "App Not Responding Fix",
        "title": "App Not Responding? 10-Second Fix 💀🖥️ #shorts",
        "output": "FOLKS_APP_NOT_RESPONDING.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "app_not_responding",
        "description": "App completely frozen? Here's the 10-second fix! 💀\n\nIn this quick fix:\n0:00 The problem — app not responding\n0:03 The 10-second fix\n0:04 Step 1: Press Ctrl+Shift+Esc\n0:06 Step 2: Find the frozen app\n0:08 Step 3: Right-click → End Task\n0:10 Done! App closed\n\n💡 Save this video — it WILL freeze again!\n🔔 Follow for more PC fixes like this!",
        "tags": "app not responding, program frozen, force close app, task manager end task, pc freeze fix, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, not responding fix, save this video",
        "script": """Is an app completely frozen?
It says not responding. You can't even close it.
So annoying right? Here is the ten second fix.
Press Ctrl Shift Esc to open Task Manager.
Find the frozen app. Right click it. Click End Task.
Boom. Closed. Freeze gone. Nothing else is affected.
Save this video. Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: red alert triangle icon on a dark blue gradient background, headline 'APP NOT RESPONDING?', cinematic tech mood",
            "dark UI graphic: dark panel with a frozen window and a red X button doing nothing, headline 'CAN'T EVEN CLOSE IT', dim dark background, tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with CTRL, SHIFT and ESC keys highlighted in cyan, a small Task Manager window popping in the corner, dark tech mood, clean readable key labels",
            "dark UI graphic: Task Manager window listing Chrome (Not responding), Spotify, Edge, Steam and Teams with the Chrome row highlighted in red, headline 'FIND THE FROZEN APP', dark tech mood, readable UI text",
            "dark UI graphic: Task Manager showing Chrome (Not responding) with a right-click context menu, the End Task item highlighted in red, headline 'RIGHT CLICK → END TASK', dark tech mood",
            "dark UI graphic: glowing green stop-square icon on a dark blue gradient, headline 'BOOM. CLOSED', success light rays, tech mood",
            "dark UI graphic: green panel with a fresh clean window icon, headline 'YOU'RE BACK', success tech mood",
            "dark UI graphic: dim panel with a broken snowflake icon crossed out, headline 'FREEZE GONE', dim dark background, tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Wrong Default App Fix",
        "title": "Files Open in the Wrong App? Fix Forever 📄⚙️ #shorts",
        "output": "FOLKS_WRONG_DEFAULT_APP.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "wrong_default_app",
        "description": "Files keep opening in the wrong app? Here's how to fix it forever! 📄\n\nIn this quick fix:\n0:00 The problem — wrong default app\n0:03 The fix\n0:04 Step 1: Right-click the file → Open with\n0:06 Step 2: Choose another app\n0:08 Step 3: Tick 'Always use this app'\n0:10 Step 4: Click OK\n0:12 Done! Fixed forever\n\n💡 Save this video — new apps steal defaults!\n🔔 Follow for more PC fixes like this!",
        "tags": "wrong default app, change default app, open with windows, pdf opens in browser, default program, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, fix default app, save this video",
        "script": """Do your files open in the wrong app?
PDFs open in the browser. So annoying right?
Here is the ten second fix.
Right click the file. Hover over Open with.
Choose another app. Tick Always use this app. Click OK.
Boom. Fixed forever. It never opens wrong again.
New apps steal defaults though. Re-check after installs.
Save this video. Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: red file icon crossed out with a red slash on a dark blue gradient background, headline 'FILES OPEN IN THE WRONG APP?', cinematic tech mood",
            "dark UI graphic: dark panel with a PDF icon opening into a browser window, headline 'SO ANNOYING', dim dark background, tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: a dark right-click context menu with Open, Open with, Share and Delete items, the Open with item highlighted in red, headline 'RIGHT CLICK THE FILE', dark tech mood",
            "dark UI graphic: cyan panel with a grid of app icons to pick from, headline 'CHOOSE ANOTHER APP', dark tech mood, readable UI text",
            "dark UI graphic: green panel with a checkbox ticked next to 'Always use this app' and an OK button highlighted, headline 'ALWAYS USE THIS APP', dark tech mood",
            "dark UI graphic: glowing green file icon with a checkmark on a dark blue gradient, headline 'FIXED FOREVER', success light rays, tech mood",
            "dark UI graphic: green panel with a lock icon over an app icon, headline 'DONE!', success tech mood",
            "dark UI graphic: dim panel with a new install badge and a theft warning, headline 'NEW APPS STEAL DEFAULTS', dim dark background, tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Battery Drain Fix",
        "title": "Battery Drains Too Fast? 10-Second Fix 🔋⚡ #shorts",
        "output": "FOLKS_BATTERY_DRAIN.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "battery_drain",
        "description": "Battery drains way too fast? Here's the 10-second fix! 🔋\n\nIn this quick fix:\n0:00 The problem — fast battery drain\n0:03 The 10-second fix\n0:04 Step 1: Press Win + I\n0:06 Step 2: System → Power & battery\n0:08 Step 3: Turn on Battery Saver\n0:10 Done! Lasts way longer\n\n💡 Tip: lower your brightness too!\n🔔 Follow for more PC fixes like this!",
        "tags": "battery draining fast, laptop battery fix, battery saver windows, battery life, power settings, laptop tips, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, save this video",
        "script": """Does your battery drain way too fast?
Full in the morning. Dead at lunch.
So annoying right? Here is the ten second fix.
Press Win and I. Open Settings. Go to System.
Then Power and battery. Turn on Battery Saver. One toggle.
Boom. Lasts way longer. Big difference.
Tip. Lower your brightness too. Saves even more.
Save this video. Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: red battery icon almost empty on a dark blue gradient background, headline 'BATTERY DRAINS FAST?', cinematic tech mood",
            "dark UI graphic: dark panel with a battery meter dropping fast with warning rays, headline 'RUNS OUT TOO QUICKLY', dim dark background, tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with the WINDOWS and I keycaps highlighted in cyan, dark tech mood, clean readable key labels",
            "dark UI graphic: cyan panel with a Settings navigation path System then Power and battery, headline 'SYSTEM → POWER & BATTERY', dark tech mood, readable UI text",
            "dark UI graphic: green panel with a single toggle switch turned on labeled Battery Saver, headline 'TURN ON BATTERY SAVER', dark tech mood",
            "dark UI graphic: glowing green full battery icon on a dark blue gradient, headline 'LASTS WAY LONGER', success light rays, tech mood",
            "dark UI graphic: green panel with a trophy icon, headline 'EASY WIN', success tech mood",
            "dark UI graphic: dim panel with a brightness slider icon, headline 'TIP: LOWER BRIGHTNESS TOO', dim dark background, tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Mic Not Working Fix",
        "title": "Mic Not Working? 10-Second Fix 🎙️🔧 #shorts",
        "output": "FOLKS_MIC_NOT_WORKING.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "mic_not_working",
        "description": "Mic not working? Nobody can hear you? Here's the 10-second fix! 🎙️\n\nIn this quick fix:\n0:00 The problem — mic not working\n0:03 The 10-second fix\n0:04 Step 1: Press Win + I\n0:06 Step 2: Privacy → Microphone\n0:08 Step 3: Toggle off & on\n0:10 Step 4: Test your mic\n0:12 Done! Works again\n\n💡 Privacy updates do this sometimes!\n🔔 Follow for more PC fixes like this!",
        "tags": "mic not working, microphone not working, mic fix, microphone privacy settings, mic access, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, fix microphone, save this video",
        "script": """Is your microphone not working?
Nobody can hear you on calls.
So annoying right? Here is the ten second fix.
Press Win and I. Open Settings. Go to Privacy.
Then Microphone. Toggle microphone access off. Then back on.
Test your mic. Boom. It works. You can be heard now.
Privacy updates do this sometimes. Re-check after updates.
Save this video. Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: red microphone icon with a red slash on a dark blue gradient background, headline 'MIC NOT WORKING?', cinematic tech mood",
            "dark UI graphic: dark panel with a phone call icon showing a crossed-out mic, headline 'CALLS ARE BROKEN', dim dark background, tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with the WINDOWS and I keycaps highlighted in cyan, dark tech mood, clean readable key labels",
            "dark UI graphic: Settings Privacy window listing microphone access ON, apps allowed ON and desktop apps allowed with the microphone access row highlighted in cyan, headline 'PRIVACY → MICROPHONE', dark tech mood, readable UI text",
            "dark UI graphic: cyan panel with a toggle switch swinging off and back on, headline 'TOGGLE IT OFF & ON', dark tech mood",
            "dark UI graphic: glowing green microphone icon with sound waves on a dark blue gradient, headline 'TEST YOUR MIC', success light rays, tech mood",
            "dark UI graphic: green panel with a speech bubble icon, headline 'WORKS AGAIN', success tech mood",
            "dark UI graphic: dim panel with a shield and update badge, headline 'PRIVACY UPDATES DO THIS', dim dark background, tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Printer Not Printing Fix",
        "title": "Printer Not Printing? 10-Second Fix 🖨️⚡ #shorts",
        "output": "FOLKS_PRINTER_NOT_PRINTING.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "printer_not_printing",
        "description": "Printer not printing? Here's the 10-second fix! 🖨️\n\nIn this quick fix:\n0:00 The problem — printer not printing\n0:03 The 10-second fix\n0:04 Step 1: Press Win + I\n0:06 Step 2: Open Printers & scanners\n0:08 Step 3: Open print queue\n0:10 Step 4: Cancel all documents\n0:12 Done! Prints again\n\n💡 Save this video — printers love to jam!\n🔔 Follow for more PC fixes like this!",
        "tags": "printer not printing, printer queue stuck, print queue fix, printer not working, cancel print queue, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, fix printer, save this video",
        "script": """Is your printer not printing?
You hit print. Nothing comes out. Classic printer.
So annoying right? Here is the ten second fix.
Press Win and I. Open Printers and scanners.
Find your printer. Click Open print queue.
You'll see the stuck jobs. Click Cancel all.
Now print again. Boom. It prints.
Printers love to jam. Save this for next time.
Save this video. Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: red printer icon with a red slash on a dark blue gradient background, headline 'PRINTER NOT PRINTING?', cinematic tech mood",
            "dark UI graphic: dark panel with a printer showing a stuck paper jam, headline 'NOTHING COMES OUT', dim dark background, tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with the WINDOWS and I keycaps highlighted in cyan, dark tech mood, clean readable key labels",
            "dark UI graphic: cyan panel with a printers list and the target printer highlighted, headline 'PRINTERS & SCANNERS', dark tech mood, readable UI text",
            "dark UI graphic: cyan panel with a print queue window showing pending documents, headline 'OPEN PRINT QUEUE', dark tech mood, readable UI text",
            "dark UI graphic: red panel with a cancel button highlighted and documents crossed out, headline 'CANCEL ALL DOCUMENTS', dark tech mood",
            "dark UI graphic: glowing green printer icon with a paper sheet on a dark blue gradient, headline 'PRINT AGAIN', success light rays, tech mood",
            "dark UI graphic: dim panel with a jammed gear icon and a warning, headline 'PRINTERS LOVE TO JAM', dim dark background, tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Desktop Icons Missing Fix",
        "title": "Desktop Icons Missing? 10-Second Fix 🖥️👀 #shorts",
        "output": "FOLKS_DESKTOP_ICONS_MISSING.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "desktop_icons_missing",
        "description": "All your desktop icons just disappeared? Here's the 10-second fix! 🖥️\n\nIn this quick fix:\n0:00 The problem — icons missing\n0:02 Don't panic — files are safe\n0:04 Step 1: Right-click the desktop\n0:06 Step 2: Hover over View\n0:08 Step 3: Click Show desktop icons\n0:10 Done! Icons are back\n\n💡 Save this video — it happens more than you think!\n🔔 Follow for more PC fixes like this!",
        "tags": "desktop icons missing, desktop icons disappeared, show desktop icons, icons gone, desktop blank, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, restore desktop icons, save this video",
        "script": """Did all your desktop icons just disappear?
The desktop looks empty. Don't panic. Your files are safe.
Here is the ten second fix.
Right click the desktop. Hover over View.
Click Show desktop icons.
Boom. All your icons are back. Done.
It happens more than you think. Quick fix every time.
Save this video. Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: red monitor icon with an empty desktop on a dark blue gradient background, headline 'DESKTOP ICONS MISSING?', cinematic tech mood",
            "dark UI graphic: dark panel with a reassuring shield icon over file icons, headline 'DON'T PANIC', dim dark background, tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: a dark right-click context menu with View, Sort by, Refresh and New items, the View item highlighted in red, headline 'RIGHT CLICK THE DESKTOP', dark tech mood",
            "dark UI graphic: a dark context submenu with Large, Medium, Small icons and Show desktop icons, the Show desktop icons item highlighted in green, headline 'HOVER OVER VIEW', dark tech mood",
            "dark UI graphic: green panel with a checked checkbox next to Show desktop icons, headline 'SHOW DESKTOP ICONS', dark tech mood",
            "dark UI graphic: glowing green monitor icon full of icons on a dark blue gradient, headline 'ALL YOUR ICONS ARE BACK', success light rays, tech mood",
            "dark UI graphic: green panel with a checkmark, headline 'DONE', success tech mood",
            "dark UI graphic: dim panel with a recurring warning icon, headline 'HAPPENS MORE THAN YOU THINK', dim dark background, tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Can't Delete File Fix",
        "title": "Can't Delete a File? 10-Second Fix 🗑️⚡ #shorts",
        "output": "FOLKS_CANT_DELETE_FILE.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "cant_delete_file",
        "description": "Can't delete a file? Here's the 10-second fix! 🗑️\n\nIn this quick fix:\n0:00 The problem — file in use\n0:03 The 10-second fix\n0:04 Step 1: Press Ctrl+Shift+Esc\n0:06 Step 2: Find the app using the file\n0:08 Step 3: Right-click → End Task\n0:10 Step 4: Delete the file\n0:12 Done! Gone\n\n💡 Save this video — stubborn files return!\n🔔 Follow for more PC fixes like this!",
        "tags": "cant delete file, file in use, file locked, delete file windows, force delete file, task manager end task, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, save this video",
        "script": """Can't delete a file?
Windows says it's open in another program. Delete keeps failing.
So annoying right? Here is the ten second fix.
Press Ctrl Shift Esc to open Task Manager.
Find the app using the file. Right click it. Click End Task.
Now delete the file. Boom. Gone.
Stubborn files will return though. Same fix next time.
Save this video. Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: red file icon with a red slash on a dark blue gradient background, headline 'CAN'T DELETE A FILE?', cinematic tech mood",
            "dark UI graphic: dark panel with a file icon locked behind a red warning box, headline 'WINDOWS SAYS NO', dim dark background, tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with CTRL, SHIFT and ESC keys highlighted in cyan, a small Task Manager window popping in the corner, dark tech mood, clean readable key labels",
            "dark UI graphic: Task Manager window listing Chrome, Spotify, Edge, Steam and Teams with the Chrome row highlighted in cyan, headline 'FIND THE APP USING IT', dark tech mood, readable UI text",
            "dark UI graphic: Task Manager showing Chrome with a right-click context menu, the End Task item highlighted in red, headline 'RIGHT CLICK → END TASK', dark tech mood",
            "dark UI graphic: cyan panel with a file icon and a delete key highlighted, headline 'NOW DELETE IT', dark tech mood",
            "dark UI graphic: glowing green trash icon on a dark blue gradient, headline 'BOOM. GONE', success light rays, tech mood",
            "dark UI graphic: dim panel with a stubborn file icon peeking back, headline 'STUBBORN FILES RETURN', dim dark background, tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Search Broken Fix",
        "title": "Windows Search Broken? 10-Second Fix 🔍⚡ #shorts",
        "output": "FOLKS_SEARCH_BROKEN.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "search_broken",
        "description": "Windows Search broken? Here's the 10-second fix! 🔍\n\nIn this quick fix:\n0:00 The problem — search broken\n0:03 The 10-second fix\n0:04 Step 1: Press Ctrl+Shift+Esc\n0:06 Step 2: Find Windows Search\n0:08 Step 3: Right-click → End Task\n0:10 Done! It restarts itself\n\n💡 Save this video — search breaks a lot!\n🔔 Follow for more PC fixes like this!",
        "tags": "windows search broken, start menu search not working, search not working, windows search fix, task manager end task, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, fix search, save this video",
        "script": """Is Windows Search broken?
You type. Nothing shows up. It just spins.
So annoying right? Here is the ten second fix.
Press Ctrl Shift Esc to open Task Manager.
Find Windows Search. Right click it. Click End Task.
It restarts itself. Boom. Search works again.
Search breaks a lot. Same fix next time.
Save this video. Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: red magnifying glass icon crossed out with a red slash on a dark blue gradient background, headline 'WINDOWS SEARCH BROKEN?', cinematic tech mood",
            "dark UI graphic: dark panel with a search bar showing an endless spinner, headline 'IT JUST SPINS', dim dark background, tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with CTRL, SHIFT and ESC keys highlighted in cyan, a small Task Manager window popping in the corner, dark tech mood, clean readable key labels",
            "dark UI graphic: Task Manager window listing Windows Search, OneDrive, Spotify, Steam and Edge with the Windows Search row highlighted in cyan, headline 'FIND WINDOWS SEARCH', dark tech mood, readable UI text",
            "dark UI graphic: Task Manager showing Windows Search with a right-click context menu, the End Task item highlighted in red, headline 'RIGHT CLICK → END TASK', dark tech mood",
            "dark UI graphic: cyan panel with a restart loop arrow icon, headline 'IT RESTARTS ITSELF', dark tech mood",
            "dark UI graphic: glowing green magnifying glass icon on a dark blue gradient, headline 'SEARCH WORKS AGAIN', success light rays, tech mood",
            "dark UI graphic: dim panel with a repeat warning icon, headline 'SEARCH BREAKS A LOT', dim dark background, tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Text Too Small Fix",
        "title": "Text Too Small? Make It Big Instantly 👀📝 #shorts",
        "output": "FOLKS_TEXT_TOO_SMALL.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "text_too_small",
        "description": "Text too small? Here's how to make it big instantly! 👀\n\nIn this quick fix:\n0:00 The problem — tiny text\n0:03 Quick zoom (browser)\n0:04 Hold Ctrl + scroll up\n0:06 Whole system: Display scale\n0:08 Step 1: Press Win + I → Display\n0:10 Step 2: Drag the scale up (125%–150%)\n0:12 Done! Bigger text\n\n💡 Every new screen needs this!\n🔔 Follow for more PC fixes like this!",
        "tags": "text too small, increase text size, windows display scale, browser zoom, screen text size, display settings, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, make text bigger, save this video",
        "script": """Is the text too small?
You're squinting at your screen. Everything is tiny.
So annoying right? Here is the ten second fix.
Hold Ctrl and scroll up. It zooms in the browser. Works on any page.
For the whole system, go to Display. Press Win and I. Then Display.
Drag the scale up. Try one twenty five. Or one fifty percent.
Bigger text. Much easier to read.
Every new screen needs this. Save this video.
Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: red Aa text icon on a dark blue gradient background, headline 'TEXT TOO SMALL?', cinematic tech mood",
            "dark UI graphic: dark panel with a squinting eye icon over tiny text, headline 'HARD TO READ', dim dark background, tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with the CTRL key highlighted in cyan and a scroll-up arrow, headline 'HOLD CTRL + SCROLL UP', dark tech mood, clean readable key labels",
            "dark UI graphic: cyan panel with a browser zoom meter increasing, headline 'ZOOMS IN THE BROWSER', dark tech mood",
            "dark UI graphic: cyan panel with a Display settings icon and navigation path, headline 'WHOLE SYSTEM: DISPLAY', dark tech mood, readable UI text",
            "dark UI graphic: green panel with a scale slider dragging up past 125%, headline 'DRAG THE SCALE UP', dark tech mood",
            "dark UI graphic: glowing green big Aa text icon on a dark blue gradient, headline 'BIGGER TEXT', success light rays, tech mood",
            "dark UI graphic: dim panel with a monitor icon and a repeat note, headline 'EVERY NEW SCREEN NEEDS THIS', dim dark background, tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Emoji Keyboard Shortcut",
        "title": "Secret Emoji Keyboard? Win + . 😂✨ #shorts",
        "output": "FOLKS_EMOJI_KEYBOARD.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "emoji_keyboard",
        "description": "Want a secret emoji keyboard? It's built into Windows! 😂\n\nIn this quick tip:\n0:00 The secret — built-in emoji keyboard\n0:02 No downloads needed\n0:04 Step 1: Press Win + . (period)\n0:06 Step 2: Emoji panel pops up\n0:08 Step 3: Browse or search\n0:10 Done! Emojis in any app\n\n💡 You'll use this daily — try it right now!\n🔔 Follow for more PC tips like this!",
        "tags": "emoji keyboard, emoji shortcut, win key period, windows emoji, type emojis windows, hidden emoji panel, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc shortcuts, save this video",
        "script": """Want a secret emoji keyboard?
It's built right into Windows. No downloads needed. No apps. No install.
Here is the ten second fix.
Press Win and the period key.
An emoji panel pops up instantly. Browse the whole library.
You can search too. Type laugh.
Emojis everywhere. In any app.
You'll use this daily. Try it right now.
Same trick everywhere. Save this video.
Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: glowing orange smiley face icon on a dark blue gradient background, headline 'SECRET EMOJI KEYBOARD?', cinematic tech mood",
            "dark UI graphic: dark panel with a no-download badge over app icons, headline 'NO DOWNLOADS NEEDED', dim dark background, tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with the WINDOWS key and period key highlighted in cyan, dark tech mood, clean readable key labels",
            "dark UI graphic: cyan panel with an emoji panel popping up with a grid of emoji faces, headline 'EMOJI PANEL POPS UP', dark tech mood",
            "dark UI graphic: cyan panel with a search box inside the emoji panel, headline 'SEARCH EMOJIS TOO', dark tech mood",
            "dark UI graphic: glowing green smiley icon with sparkles on a dark blue gradient, headline 'EMOJIS EVERYWHERE', success light rays, tech mood",
            "dark UI graphic: green panel with a daily calendar icon, headline 'YOU'LL USE THIS DAILY', success tech mood",
            "dark UI graphic: dim panel with a keyboard shortcut badge WIN + ., headline 'SHORTCUT: WIN + .', dim dark background, tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Screen Record Shortcut",
        "title": "Record Screen WITHOUT Software? 🎥🖥️ #shorts",
        "output": "FOLKS_SCREEN_RECORD.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "screen_record",
        "description": "Want to record your screen without any software? It's hidden in Windows! 🎥\n\nIn this quick tip:\n0:00 The secret — built-in recorder\n0:02 No downloads, no watermark\n0:04 Step 1: Press Win + Alt + R\n0:06 Step 2: Recording starts\n0:08 Step 3: Click stop when done\n0:10 Step 4: Saved to Videos folder\n0:12 Done! Zero cost\n\n💡 Great for clips and bugs!\n🔔 Follow for more PC tips like this!",
        "tags": "screen record windows, record screen without software, xbox game bar record, screen recording shortcut, win alt r, no watermark recorder, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc shortcuts, save this video",
        "script": """Want to record your screen without any software?
Windows has it hidden. No downloads. No watermark. Completely free.
Here is the ten second fix.
Press Win Alt and R. Recording starts now.
A small bar appears. Click stop when you're done.
Your clip saves itself. Straight to your Videos folder.
Done. Zero cost. Great for clips and bugs.
Save this video. Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: glowing orange camera icon on a dark blue gradient background, headline 'RECORD WITHOUT SOFTWARE?', cinematic tech mood",
            "dark UI graphic: dark panel with a no-download no-watermark badge over a monitor, headline 'NO DOWNLOADS. NO WATERMARK.', dim dark background, tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with the WINDOWS, ALT and R keycaps highlighted in cyan, dark tech mood, clean readable key labels",
            "dark UI graphic: red panel with a red recording dot and a small capture bar, headline 'RECORDING STARTS NOW', dark tech mood",
            "dark UI graphic: cyan panel with a stop square button highlighted, headline 'CLICK STOP WHEN DONE', dark tech mood",
            "dark UI graphic: green panel with a film clip sliding into a Videos folder, headline 'SAVED TO VIDEOS FOLDER', dark tech mood",
            "dark UI graphic: glowing green camera icon with a zero-cost badge on a dark blue gradient, headline 'DONE. ZERO COST', success light rays, tech mood",
            "dark UI graphic: dim panel with a clapperboard and bug icon, headline 'GREAT FOR CLIPS & BUGS', dim dark background, tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Blue Screen Fix",
        "title": "Blue Screen? Fix It With ONE Command 🛡️💙 #shorts",
        "output": "FOLKS_BLUE_SCREEN.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "blue_screen",
        "description": "Blue screen? Don't panic — here's the fix with ONE command! 🛡️\n\nIn this quick fix:\n0:00 The problem — blue screen\n0:02 Don't panic — files are safe\n0:04 Step 1: Press Win + R\n0:06 Step 2: Open CMD as admin\n0:08 Step 3: Type sfc /scannow\n0:10 Step 4: Let it scan\n0:12 Done! Fixed\n\n💡 Worth doing after any crash!\n🔔 Follow for more PC fixes like this!",
        "tags": "blue screen of death, bsod fix, sfc scannow, repair windows files, system file checker, stop crashing, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, save this video",
        "script": """Did you just get the Blue Screen?
Don't panic. Your files are usually fine.
Here is the fix. Press Win and R. Type CMD. Press Enter.
Run it as admin. Type SFC slash scannow. Press Enter.
It checks your system files. Let it scan. It repairs broken files.
Boom. Fixed. Fewer crashes now.
Worth doing after a crash. Save this video.
Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: blue monitor icon with a sad face and the blue screen look on a dark background, headline 'BLUE SCREEN?', cinematic tech mood",
            "dark UI graphic: dark panel with a reassuring shield over file icons, headline 'YOUR FILES ARE FINE', dim dark background, tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with the WINDOWS and R keycaps highlighted in cyan, a small Run dialog popping in the corner, dark tech mood, clean readable key labels",
            "dark UI graphic: a Windows Run dialog with cmd typed into the open field in cyan, headline 'RUN AS ADMIN', dark blue gradient background, readable UI text",
            "dark UI graphic: black command prompt window with the cyan command 'sfc /scannow' typed in and the message 'Scanning... repairs broken Windows files', dark tech mood",
            "dark UI graphic: cyan progress bar at 60% labeled 'Verifying 60%' on a dark background, headline 'LET IT SCAN', dark tech mood",
            "dark UI graphic: glowing green shield icon with a checkmark on a dark blue gradient, headline 'BOOM. FIXED', success light rays, tech mood",
            "dark UI graphic: dim panel with a crash-after note and a restart icon, headline 'WORTH DOING AFTER A CRASH', dim dark background, tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Cursor Disappeared Fix",
        "title": "Cursor Disappeared? 10-Second Fix 🖱️👀 #shorts",
        "output": "FOLKS_CURSOR_DISAPPEARED.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": "cursor_disappeared",
        "description": "Cursor just disappeared? Here's the 10-second fix! 🖱️\n\nIn this quick fix:\n0:00 The problem — cursor gone\n0:03 The 10-second fix\n0:04 Step 1: Press Win + R\n0:06 Step 2: Type main.cpl\n0:08 Step 3: Open Pointer Options\n0:10 Step 4: Tick 'Show location when I press CTRL'\n0:12 Done! Press Ctrl to find it\n\n💡 Save this video — cursors love to hide!\n🔔 Follow for more PC fixes like this!",
        "tags": "cursor disappeared, mouse pointer gone, cursor not showing, find mouse pointer, show pointer location, mouse fix, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, save this video",
        "script": """Did your cursor just disappear?
You move the mouse. Nothing shows up.
So annoying right? Here is the ten second fix.
Press Win and R. Type main dot cpl. Press Enter.
Go to Pointer Options. Tick Show location when I press Ctrl.
Press Ctrl now. Boom. Found it.
Cursors love to hide. Now you can always find it.
Save this video. Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: red mouse icon crossed out with a red slash on a dark blue gradient background, headline 'CURSOR DISAPPEARED?', cinematic tech mood",
            "dark UI graphic: dark panel with a moving mouse and no pointer visible, headline 'MOVE THE MOUSE... NOTHING', dim dark background, tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with the WINDOWS and R keycaps highlighted in cyan, a small Run dialog popping in the corner, dark tech mood, clean readable key labels",
            "dark UI graphic: a Windows Run dialog with main.cpl typed into the open field in cyan, dark blue gradient background, readable UI text",
            "dark UI graphic: cyan panel with a Mouse Properties window and the Pointer Options tab highlighted, headline 'POINTER OPTIONS', dark tech mood, readable UI text",
            "dark UI graphic: green panel with a checked checkbox next to 'Show location when I press CTRL', headline 'SHOW LOCATION ON CTRL', dark tech mood",
            "dark UI graphic: glowing green mouse icon with a pulsing radar ring on a dark blue gradient, headline 'PRESS CTRL NOW', success light rays, tech mood",
            "dark UI graphic: dim panel with a hide-and-seek icon over a cursor, headline 'CURSORS LOVE TO HIDE', dim dark background, tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Wi-Fi Won't Connect Fix",
        "title": "Wi-Fi Won't Connect? 10-Second Fix 📶⚡ #shorts",
        "output": "FOLKS_WIFI_NOT_CONNECTING.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "description": "Wi-Fi won't connect on your PC? Here's the 10-second fix! 📶\n\nIn this quick fix:\n0:00 The problem — Wi-Fi stuck\n0:03 The 10-second fix\n0:04 Step 1: Press Win + I\n0:06 Step 2: Go to Network & Internet\n0:08 Step 3: Click Advanced network settings\n0:10 Step 4: Click Network reset → Reset now\n0:14 Done! Wi-Fi works again\n\n💡 Save this video — it WILL drop again!\n🔔 Follow for more PC fixes like this!",
        "tags": "wifi not connecting, wifi stuck, network reset, wifi fix, internet not working, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, wifi problems fixed, save this video",
        "script": """Did your Wi-Fi just stop connecting?
You click the network icon and nothing happens.
So annoying right? Here is the ten second fix.
Press Win and I together to open Settings.
Go to Network and Internet.
Click Advanced network settings.
Click Network reset. Then click Reset now.
Your PC restarts the network. Just like that, Wi-Fi is back.
Save this video. It will drop again.
Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: Wi-Fi icon with a red X and a yellow warning triangle on a dark blue gradient background, headline 'WI-FI WON'T CONNECT?', red alert badge, cinematic tech mood, readable UI text",
            "dark UI graphic: computer showing the Wi-Fi list with no available networks, a spinning grey circle, headline 'NOTHING HAPPENS', dim dark background, cinematic tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with the WINDOWS and I keycaps highlighted in cyan, a small Settings window popping in the corner, headline 'PRESS WIN + I', dark tech mood, clean readable key labels",
            "dark UI graphic: Windows Settings sidebar with the Network and Internet item highlighted in cyan, headline 'GO TO NETWORK & INTERNET', dark tech mood, readable UI text",
            "dark UI graphic: Settings window with Advanced network settings row highlighted in cyan, headline 'ADVANCED NETWORK SETTINGS', dark blue gradient background, readable UI text",
            "dark UI graphic: Settings page showing a Network reset panel with a red RESET NOW button highlighted, headline 'NETWORK RESET → RESET NOW', dark tech mood",
            "dark UI graphic: Wi-Fi icon with spinning refresh arrows and a pulsing green dot, headline 'PC RESTARTS THE NETWORK', dark blue gradient background, tech mood",
            "dark UI graphic: Wi-Fi icon with full green signal bars and a glowing checkmark, headline 'WI-FI IS BACK', green light rays, success tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Taskbar Frozen Fix",
        "title": "Taskbar Frozen or Not Clicking? 10-Second Fix 🧊⚡ #shorts",
        "output": "FOLKS_TASKBAR_FROZEN.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "description": "Taskbar frozen and nothing clicks? Here's the 10-second fix! 🧊\n\nIn this quick fix:\n0:00 The problem — taskbar dead\n0:03 The 10-second fix\n0:04 Step 1: Press Ctrl+Shift+Esc\n0:06 Step 2: Find 'Windows Explorer'\n0:08 Step 3: Right-click → Restart\n0:12 Done! Taskbar clicks again\n\n💡 Save this video — it WILL freeze again!\n🔔 Follow for more PC fixes like this!",
        "tags": "taskbar frozen, taskbar not clicking, start menu not working, windows explorer restart, taskbar fix, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, taskbar problems fixed, save this video",
        "script": """Is your taskbar frozen? Nothing clicks?
Start menu dead. Icons dead. The whole bar is stuck.
So annoying right? Here is the ten second fix.
Press Ctrl Shift Esc to open Task Manager.
Find Windows Explorer. Right click it. Click Restart.
Your taskbar disappears for one second. Then it pops right back.
Just like that, everything clicks again.
Save this video. It will freeze again.
Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: taskbar at the bottom of the screen with a big frozen snowflake icon and a red alert badge on a dark blue gradient background, headline 'TASKBAR FROZEN?', cinematic tech mood, readable UI text",
            "dark UI graphic: desktop with a greyed out taskbar and a dead start menu, a big grey X cursor clicking nothing, headline 'NOTHING CLICKS', dim dark background, cinematic tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with CTRL, SHIFT and ESC keys highlighted in cyan, a small Task Manager window popping in the corner, dark tech mood, clean readable key labels",
            "dark UI graphic: Windows Task Manager window listing running processes with the Windows Explorer row highlighted in cyan, headline 'FIND WINDOWS EXPLORER', dark tech mood, readable UI text",
            "dark UI graphic: Windows Task Manager showing Windows Explorer with a right-click context menu, the Restart menu item highlighted in red, headline 'RIGHT CLICK → RESTART', dark tech mood",
            "dark UI graphic: Windows Explorer row in Task Manager with a green restart arrow spinning, headline 'RESTARTING EXPLORER...', dark blue gradient background, tech mood",
            "dark UI graphic: taskbar fading out and then popping back with a small green glow, headline 'POPS RIGHT BACK', dark blue gradient background, tech mood",
            "dark UI graphic: taskbar with a glowing green checkmark floating above it, headline 'EVERYTHING CLICKS AGAIN', green light rays, success tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Mouse Double-Click Fix",
        "title": "Mouse Double-Clicking by Itself? 10-Second Fix 🖱️⚡ #shorts",
        "output": "FOLKS_MOUSE_DOUBLE_CLICK.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "description": "Mouse double-clicking when you only click once? Here's the 10-second fix! 🖱️\n\nIn this quick fix:\n0:00 The problem — files open by themselves\n0:03 The 10-second fix\n0:04 Step 1: Open Control Panel\n0:06 Step 2: Click Mouse\n0:08 Step 3: Open the Buttons tab\n0:10 Step 4: Turn the speed down slightly\n0:14 Done! No more double clicks\n\n💡 Save this video — it WILL act up again!\n🔔 Follow for more PC fixes like this!",
        "tags": "mouse double clicking, mouse opens files by itself, double click fix, mouse settings, mouse speed, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, mouse problems fixed, save this video",
        "script": """Is your mouse double-clicking by itself?
You click once, and files open twice. Everything misbehaves.
So annoying right? Here is the ten second fix.
Open the Control Panel.
Click Mouse to open mouse settings.
Go to the Buttons tab.
Drag the double click speed down a little.
Just like that, no more phantom double clicks.
Save this video. It will act up again.
Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: computer mouse icon with two ghost fingers clicking it twice and a red alert badge on a dark blue gradient background, headline 'MOUSE DOUBLE-CLICKING?', cinematic tech mood, readable UI text",
            "dark UI graphic: file explorer where two folders fly open at once, multiple window squares, headline 'FILES OPEN BY THEMSELVES', dim dark background, cinematic tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: Control Panel window with the Mouse icon highlighted in cyan, headline 'CLICK MOUSE', dark tech mood, readable UI text",
            "dark UI graphic: mouse properties window with the Buttons tab highlighted in cyan, headline 'OPEN THE BUTTONS TAB', dark tech mood, readable UI text",
            "dark UI graphic: mouse settings dialog with a red warning on the double-click test box, headline 'STILL ACTING WEIRD?', dim dark background, cinematic tech mood",
            "dark UI graphic: mouse settings showing a slider labeled DOUBLE CLICK SPEED being dragged down in red, headline 'TURN THE SPEED DOWN', dark tech mood, readable UI text",
            "dark UI graphic: small mouse test box where one click stays single, a green checkmark over the mouse icon, headline 'TEST IT', dark blue gradient background, tech mood",
            "dark UI graphic: computer mouse with a green checkmark and no ghost clicks, headline 'NO MORE DOUBLE CLICKS', green light rays, dark blue gradient background, success tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "External Drive Not Showing Fix",
        "title": "USB Drive Not Showing Up? 10-Second Fix 💾🔌 #shorts",
        "output": "FOLKS_DRIVE_NOT_SHOWING.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "description": "USB or external drive not showing in File Explorer? Here's the 10-second fix! 💾\n\nIn this quick fix:\n0:00 The problem — drive missing\n0:03 The 10-second fix\n0:04 Step 1: Right-click Start → Disk Management\n0:06 Step 2: Find the grey drive\n0:08 Step 3: Right-click → Change Drive Letter\n0:10 Step 4: Assign a new letter\n0:14 Done! Drive appears instantly\n\n💡 Save this video — it WILL hide again!\n🔔 Follow for more PC fixes like this!",
        "tags": "usb drive not showing, external drive not showing, change drive letter, disk management, usb fix, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, drive problems fixed, save this video",
        "script": """Did your USB drive just disappear?
You plug it in, and nothing shows in File Explorer.
So annoying right? Here is the ten second fix.
Right click the Start button. Click Disk Management.
Find your drive with a grey icon and no letter.
Right click it. Click Change Drive Letter and Paths.
Click Add, and pick a new letter.
Just like that, your drive appears instantly.
Save this video. It will hide again.
Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: USB flash drive icon with a red question mark and a grey empty file explorer window on a dark blue gradient background, headline 'DRIVE NOT SHOWING?', red alert badge, cinematic tech mood, readable UI text",
            "dark UI graphic: file explorer with only one drive listed and a blinking empty space where a second drive should be, headline 'NOTHING IN EXPLORER', dim dark background, cinematic tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: start menu right-click context menu with Disk Management highlighted in cyan, headline 'RIGHT CLICK START → DISK MANAGEMENT', dark tech mood, readable UI text",
            "dark UI graphic: Disk Management window with a grey drive partition with no drive letter highlighted in cyan, headline 'FIND THE GREY DRIVE', dark tech mood, readable UI text",
            "dark UI graphic: right-click context menu over the grey drive with Change Drive Letter and Paths highlighted in red, headline 'CHANGE DRIVE LETTER', dark tech mood",
            "dark UI graphic: dialog box showing the drive letter field with a grey X and an ADD button, headline 'CLICK ADD', dark blue gradient background, readable UI text",
            "dark UI graphic: small dialog with a drive letter dropdown and an ADD button highlighted, headline 'ASSIGN A NEW LETTER', dark blue gradient background, readable UI text",
            "dark UI graphic: file explorer now showing the USB drive with a glowing green checkmark, headline 'DRIVE APPEARS INSTANTLY', green light rays, success tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "PC Won't Shut Down Fix",
        "title": "PC Won't Shut Down or Restart? 10-Second Fix 🚫⚡ #shorts",
        "output": "FOLKS_WONT_SHUT_DOWN.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "description": "PC stuck and won't shut down? Here's the 10-second fix! 🚫\n\nIn this quick fix:\n0:00 The problem — screen stuck\n0:03 The 10-second fix\n0:04 Step 1: Hold the power button for 10 seconds\n0:06 Step 2: Let it turn fully off\n0:08 Step 3: Wait 10 seconds\n0:10 Step 4: Turn it back on\n0:14 Done! PC boots clean\n\n⚠️ Only when the PC is totally frozen!\n🔔 Follow for more PC fixes like this!",
        "tags": "pc won't shut down, pc stuck, computer frozen, hold power button, pc not restarting, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, computer problems fixed, save this video",
        "script": """Is your PC stuck and won't shut down?
You click start, click shut down, and nothing happens.
So annoying right? Here is the ten second fix.
Hold the power button for ten seconds.
Let the PC turn fully off.
Wait ten seconds.
Then press the power button to turn it back on.
Just like that, your PC boots clean.
Only do this when it's totally frozen.
Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: power button icon with a red X and a frozen spinning wheel on a dark blue gradient background, headline 'PC WON'T SHUT DOWN?', red alert badge, cinematic tech mood, readable UI text",
            "dark UI graphic: start menu with the shutdown button crossed out and a grey frozen screen behind, headline 'CLICK ... AND NOTHING', dim dark background, cinematic tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: glowing power button being held down with a circular 10 second countdown ring, headline 'HOLD POWER FOR 10 SECONDS', dark tech mood, readable UI text",
            "dark UI graphic: dark screen with a grey power icon going to black, headline 'LET IT TURN FULLY OFF', dark blue gradient background, tech mood",
            "dark UI graphic: a big grey clock icon with 10 marked on it, headline 'WAIT 10 SECONDS', dark tech mood, readable UI text",
            "dark UI graphic: power button with green lightning and a booting screen with loading dots, headline 'TURN IT BACK ON', dark blue gradient background, tech mood",
            "dark UI graphic: desktop with a glowing green checkmark over a clean screen, headline 'PC BOOTS CLEAN', green light rays, success tech mood",
            "dark UI graphic: orange warning triangle icon with text 'ONLY IF TOTALLY FROZEN', headline '⚠️ ONLY WHEN FROZEN', dark red gradient background, warning tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Keyboard Typing Wrong Fix",
        "title": "Keyboard Typing Wrong Characters? 10-Second Fix ⌨️⚡ #shorts",
        "output": "FOLKS_KEYBOARD_TYPING_WRONG.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "description": "Keyboard typing symbols instead of letters? Here's the 10-second fix! ⌨️\n\nIn this quick fix:\n0:00 The problem — weird characters\n0:03 The 10-second fix\n0:04 Step 1: Press the Windows key\n0:06 Step 2: Type 'On-Screen Keyboard'\n0:08 Step 3: Open it\n0:10 Step 4: Press Ctrl and check\n0:14 Done! Keys work again\n\n💡 Usually it's a stuck Ctrl or Alt key!\n🔔 Follow for more PC fixes like this!",
        "tags": "keyboard typing wrong characters, keyboard typing symbols, on screen keyboard, ctrl stuck, keyboard fix, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, keyboard problems fixed, save this video",
        "script": """Is your keyboard typing wrong characters?
You press a letter and get a symbol. Or numbers and nothing.
So annoying right? Here is the ten second fix.
Press the Windows key. Type on screen keyboard.
Open the On-Screen Keyboard.
Look for the Ctrl or Alt keys that look pressed down.
Click them to release. Just like that, keys work again.
It's usually a stuck Ctrl or Alt key.
Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: computer keyboard with letters turning into symbols and a red alert badge on a dark blue gradient background, headline 'KEYBOARD TYPING WRONG?', cinematic tech mood, readable UI text",
            "dark UI graphic: text editor showing weird symbols instead of letters, a big red question mark, headline 'SYMBOLS INSTEAD OF LETTERS', dim dark background, cinematic tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with the WINDOWS key highlighted in cyan and a search bar typing 'ON-SCREEN KEYBOARD', headline 'PRESS WIN → TYPE IT', dark tech mood, clean readable key labels",
            "dark UI graphic: On-Screen Keyboard app window popping up with its keys glowing, headline 'OPEN ON-SCREEN KEYBOARD', dark tech mood, readable UI text",
            "dark UI graphic: On-Screen Keyboard and a normal keyboard side by side with matching keys highlighted, headline 'COMPARE THE TWO', dark blue gradient background, tech mood",
            "dark UI graphic: On-Screen Keyboard with the CTRL and ALT keys highlighted in red and pressed down, headline 'FIND STUCK CTRL OR ALT', dark tech mood, readable key labels",
            "dark UI graphic: On-Screen Keyboard with CTRL and ALT keys glowing green and released, headline 'CLICK TO RELEASE', dark blue gradient background, tech mood",
            "dark UI graphic: text editor now typing letters correctly with a glowing green checkmark, headline 'KEYS WORK AGAIN', green light rays, success tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Notifications Not Working Fix",
        "title": "No Desktop Notifications? 10-Second Fix 🔔⚡ #shorts",
        "output": "FOLKS_NOTIFICATIONS_NOT_WORKING.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "description": "No notifications popping up on your PC? Here's the 10-second fix! 🔔\n\nIn this quick fix:\n0:00 The problem — silent notifications\n0:03 The 10-second fix\n0:04 Step 1: Press Win + I\n0:06 Step 2: Go to System → Notifications\n0:08 Step 3: Turn ON notifications\n0:10 Step 4: Check Focus assist\n0:14 Done! Notifications back\n\n💡 Save this video — it WILL get silenced again!\n🔔 Follow for more PC fixes like this!",
        "tags": "notifications not working, no desktop notifications, focus assist, notification settings, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, notifications fix, save this video",
        "script": """Are your notifications not popping up?
No pings. No banners. Total silence on your PC.
So annoying right? Here is the ten second fix.
Press Win and I together to open Settings.
Go to System, then Notifications.
Make sure notifications are turned ON.
Now check Focus assist. Make sure it's OFF.
Just like that, notifications are back.
Save this video. It will get silenced again.
Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: bell icon with a red X and a dark quiet moon icon on a dark blue gradient background, headline 'NO NOTIFICATIONS?', red alert badge, cinematic tech mood, readable UI text",
            "dark UI graphic: notification banner icon with a grey slash across it, a totally clean notification corner, headline 'TOTAL SILENCE', dim dark background, cinematic tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with the WINDOWS and I keycaps highlighted in cyan, a small Settings window popping in the corner, headline 'PRESS WIN + I', dark tech mood, clean readable key labels",
            "dark UI graphic: Windows Settings sidebar with the System and Notifications items highlighted in cyan, headline 'SYSTEM → NOTIFICATIONS', dark tech mood, readable UI text",
            "dark UI graphic: Settings toggle for notifications switched ON and glowing green, headline 'TURN NOTIFICATIONS ON', dark blue gradient background, readable UI text",
            "dark UI graphic: notification test banner popping at the bottom with a green checkmark, headline 'TEST IT', dark blue gradient background, tech mood",
            "dark UI graphic: Focus assist settings panel with the OFF option highlighted in red, headline 'CHECK FOCUS ASSIST', dark tech mood, readable UI text",
            "dark UI graphic: bell icon ringing with a glowing green checkmark and banner notifications popping, headline 'NOTIFICATIONS ARE BACK', green light rays, success tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "Screen Too Dark Fix",
        "title": "Screen Too Dark or Bright? 10-Second Fix 🔆⚡ #shorts",
        "output": "FOLKS_SCREEN_TOO_DARK.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "description": "Screen too dark even at max brightness? Here's the 10-second fix! 🔆\n\nIn this quick fix:\n0:00 The problem — dim screen\n0:03 The 10-second fix\n0:04 Step 1: Press Win + I\n0:06 Step 2: Go to System → Display\n0:08 Step 3: Turn OFF 'Help improve battery'\n0:10 Step 4: Crank brightness to 100%\n0:14 Done! Screen bright again\n\n💡 Save this video — it WILL dim again!\n🔔 Follow for more PC fixes like this!",
        "tags": "screen too dark, screen dim, brightness not working, adaptive brightness, display settings, pc tips, computer fix, tech shorts, windows tips, windows 11 tips, windows 10 tips, pc troubleshooting, brightness fix, save this video",
        "script": """Is your screen too dark, even at max brightness?
You crank it up and it stays dim.
So annoying right? Here is the ten second fix.
Press Win and I together to open Settings.
Go to System, then Display.
Turn off help improve battery, that's adaptive brightness.
Now drag the brightness to one hundred percent.
Just like that, your screen is bright again.
Save this video. It will dim again.
Follow for more PC fixes like this!""",
        "prompts": [
            "dark UI graphic: monitor icon with a grey dark screen and a red alert badge on a dark blue gradient background, headline 'SCREEN TOO DARK?', cinematic tech mood, readable UI text",
            "dark UI graphic: brightness slider stuck at max but the monitor staying grey and dim, headline 'STILL DIMMED', dim dark background, cinematic tech mood",
            "dark UI graphic: glowing yellow lightning bolt in a rounded panel with a big 10s badge, headline 'THE 10-SECOND FIX', dark blue gradient background, energetic tech mood",
            "dark UI graphic: top-down keyboard with the WINDOWS and I keycaps highlighted in cyan, a small Settings window popping in the corner, headline 'PRESS WIN + I', dark tech mood, clean readable key labels",
            "dark UI graphic: Windows Settings sidebar with the System and Display items highlighted in cyan, headline 'SYSTEM → DISPLAY', dark tech mood, readable UI text",
            "dark UI graphic: Settings panel with a toggle labeled 'Help improve battery' switched OFF in red, headline 'TURN OFF ADAPTIVE BRIGHTNESS', dark tech mood, readable UI text",
            "dark UI graphic: monitor showing a grey dim screen next to a slider labeled ADAPTIVE BRIGHTNESS with an OFF badge, headline 'THAT WAS THE CULPRIT', dim dark background, cinematic tech mood",
            "dark UI graphic: brightness slider dragged to 100% glowing cyan, headline 'CRANK TO 100%', dark blue gradient background, readable UI text",
            "dark UI graphic: monitor with a bright glowing screen and light rays bursting out, headline 'SCREEN IS BRIGHT AGAIN', green light rays, success tech mood",
            "dark UI graphic: orange bookmark ribbon icon with a follow bell and a FOLLOW button, headline 'SAVE THIS FOR LATER', dark blue gradient background, tech mood",
        ],
    },
    {
        "topic": "RAM Full Fix",
        "title": "PC Freezing? Your RAM is Full — 10-Second Fix 🧠⚡ #shorts",
        "output": "FOLKS_RAM_FULL.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "PC keeps freezing? Your RAM is full — here's the 10-second fix! 🧠\n\nIn this quick fix:\n0:00 The problem — PC freezing constantly\n0:03 The 10-second fix\n0:04 Step 1: Press Ctrl+Shift+Esc\n0:06 Step 2: Click Memory tab\n0:08 Step 3: Sort by RAM usage\n0:10 Step 4: End the biggest waster\n0:12 Done! PC smooth again\n\n💡 Save this — RAM fills up every time!\n🔔 Follow for more PC fixes!",
        "tags": "PC freezing fix, RAM full fix, memory fix windows, task manager RAM, PC running slow, windows 10 fix, windows 11 fix, computer fix, tech tips, PC tips, folks, 10 second fix",
        "script": """Is your PC freezing and stuttering for no reason? Your RAM is probably full. Here is the ten-second fix.
Step one. Press Control Shift Escape to open Task Manager.
Step two. Click the Performance tab then click Memory.
Step three. Go back to Processes and click the Memory column to sort by highest usage.
Step four. Right-click the biggest RAM waster you do not need and hit End Task.
Done! Your PC stops freezing immediately. Save this video because your RAM will fill up again. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode Windows Task Manager screenshot showing Memory tab at 97 percent usage with red warning indicator, clean minimal UI, blue accent color, 1080x960 vertical crop",
            "Dark mode Windows Task Manager Processes tab with Memory column sorted descending, top process highlighted in red showing 4GB usage, clean UI, blue accent",
            "Dark mode Windows screen showing PC performance graph with memory flatlined at maximum, freeze warning overlay, clean minimal design, blue cyan accent",
            "Dark mode Task Manager showing memory usage dropping from 97 percent to 45 percent after ending process, green checkmark overlay, clean UI",
            "Clean dark Windows desktop with performance widget showing memory now at 45 percent, smooth animation indicator, blue accent, subscribe reminder overlay",
        ],
    },
    {
        "topic": "Startup Password Skip",
        "title": "Remove Windows Login Password in 10 Seconds 🔓⚡ #shorts",
        "output": "FOLKS_PASSWORD_SKIP.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Tired of typing your password every time? Remove it in 10 seconds! 🔓\n\nIn this quick fix:\n0:00 The problem — password screen every boot\n0:03 The 10-second fix\n0:04 Step 1: Press Win + R\n0:06 Step 2: Type netplwiz\n0:08 Step 3: Uncheck 'Users must enter password'\n0:10 Step 4: Enter your password to confirm\n0:12 Done! Auto-login enabled\n\n💡 Only do this on a personal PC!\n🔔 Follow for more PC fixes!",
        "tags": "remove windows password, auto login windows, skip login screen, netplwiz, windows 10 password fix, windows 11 tip, PC tips, folks, 10 second fix, computer tips",
        "script": """Tired of typing your Windows password every single time you start your PC? Here is how to remove it in ten seconds.
Step one. Press Windows key and R at the same time to open Run.
Step two. Type netplwiz and press Enter.
Step three. Uncheck the box that says Users must enter a user name and password.
Step four. Enter your current password to confirm and click OK.
Done! Windows will now log in automatically every time. Only do this on your personal PC at home. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode Windows Run dialog box open with netplwiz typed inside, clean minimal UI, blue accent color, dark background, 1080x960 vertical",
            "Dark mode User Accounts dialog showing checkbox unchecked for password requirement, cursor highlighting the checkbox, clean UI, blue accent",
            "Dark mode Windows login screen with a big red X crossing it out, arrow pointing to a green checkmark auto-login screen, clean minimal design",
            "Dark mode confirmation dialog with password field being filled in, green confirm button highlighted, clean UI, blue cyan accent",
            "Clean dark Windows desktop booting directly without login screen, speed lines animation, green checkmark overlay, subscribe reminder",
        ],
    },
    {
        "topic": "High CPU Fix",
        "title": "CPU at 100%? Here's Why and How to Fix It ⚙️🔥 #shorts",
        "output": "FOLKS_HIGH_CPU.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "CPU stuck at 100%? Here's the instant fix! ⚙️\n\nIn this quick fix:\n0:00 The problem — CPU 100% always\n0:03 The 10-second fix\n0:04 Step 1: Ctrl+Shift+Esc → Task Manager\n0:06 Step 2: Sort by CPU usage\n0:08 Step 3: Find the culprit process\n0:10 Step 4: End Task or disable on startup\n0:12 Done! CPU back to normal\n\n💡 Save this — it WILL happen again!\n🔔 Follow for more PC fixes!",
        "tags": "CPU 100 percent fix, high CPU usage windows, task manager CPU, PC running hot, slow PC fix, windows 10 fix, windows 11 fix, computer fix, tech tips, folks, 10 second fix",
        "script": """Is your CPU stuck at one hundred percent making your whole PC slow and burning hot? Here is the ten-second fix.
Step one. Press Control Shift Escape to open Task Manager.
Step two. Click the CPU column header to sort processes by highest CPU usage.
Step three. Look for the biggest CPU waster. Common culprits are Windows Update, antivirus scans, or browser extensions.
Step four. If it is not essential right-click it and hit End Task. If it keeps coming back right-click it and open its file location to investigate.
Done! CPU drops immediately. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode Windows Task Manager showing CPU usage graph flatlined at 100 percent with red warning, heat wave effect overlay, clean minimal UI, orange red accent, 1080x960",
            "Dark mode Task Manager Processes sorted by CPU descending, top process highlighted in red at 98 percent CPU, cursor on End Task button, clean UI",
            "Dark mode PC performance panel showing CPU temperature gauge at critical level with flame icon, clean minimal design, red orange accent",
            "Dark mode Task Manager showing CPU dropping from 100 percent to 12 percent after ending process, green arrow pointing down, clean UI",
            "Clean dark Windows desktop CPU widget showing normal 8 percent usage, cool blue color, green checkmark overlay, subscribe reminder",
        ],
    },
    {
        "topic": "Files Disappeared Fix",
        "title": "Files Disappeared from Desktop? Get Them Back in 5 Seconds 🗂️⚡ #shorts",
        "output": "FOLKS_FILES_DISAPPEARED.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Desktop files all gone? Get them back instantly! 🗂️\n\nIn this quick fix:\n0:00 The problem — desktop is empty\n0:03 The 5-second fix\n0:04 Step 1: Right-click empty desktop\n0:06 Step 2: Click View\n0:08 Step 3: Click Show desktop icons\n0:10 Done! All files reappear instantly\n\n💡 This happens after Windows updates!\n🔔 Follow for more PC fixes!",
        "tags": "desktop icons disappeared, files gone from desktop, show desktop icons, windows fix, desktop empty fix, windows 10 fix, windows 11 fix, PC tips, folks, quick fix",
        "script": """Did all your desktop files and icons suddenly disappear? Do not panic. They are still there. Here is the five-second fix.
Step one. Right-click anywhere on the empty desktop.
Step two. Hover over View in the menu that appears.
Step three. In the submenu look for Show desktop icons and click it to make sure it has a checkmark.
Done! Every single file and icon reappears instantly. Windows sometimes turns this off after updates. Save this video. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode completely empty Windows desktop with subtle wallpaper, confused question mark overlay, clean minimal design, blue accent, 1080x960 vertical",
            "Dark mode Windows right-click context menu open on desktop showing View submenu highlighted, clean UI, blue accent cursor pointing to it",
            "Dark mode View submenu showing Show desktop icons option with cursor clicking it, checkmark appearing, clean minimal UI",
            "Dark mode Windows desktop showing all icons and files suddenly reappearing with a pop animation effect, green checkmark overlay",
            "Clean dark Windows desktop full of icons restored, celebration effect, subscribe reminder overlay, blue cyan accent",
        ],
    },
    {
        "topic": "PC Overheating Fix",
        "title": "PC Overheating and Shutting Down? Fix It in 10 Seconds 🌡️❄️ #shorts",
        "output": "FOLKS_OVERHEATING.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "PC randomly shutting down from heat? Here's the fix! 🌡️\n\nIn this quick fix:\n0:00 The problem — random shutdowns from heat\n0:03 The 10-second fix\n0:04 Step 1: Search 'Power Plan' in Start\n0:06 Step 2: Open Change plan settings\n0:08 Step 3: Change advanced power settings\n0:10 Step 4: Set Processor max to 80%\n0:12 Done! No more overheating shutdowns\n\n💡 Save this — summer makes it worse!\n🔔 Follow for more PC fixes!",
        "tags": "PC overheating fix, PC shutting down heat, processor power limit, windows power plan, thermal throttle fix, laptop overheating, PC tips, folks, 10 second fix, computer tips",
        "script": """Is your PC randomly shutting down because it is overheating? Here is the ten-second software fix.
Step one. Click the Start menu and search for Power Plan and open Choose a power plan.
Step two. Click Change plan settings next to your current plan.
Step three. Click Change advanced power settings.
Step four. Find Processor power management, then Maximum processor state, and change it from one hundred percent to eighty percent.
Done! Your CPU runs cooler and stops causing those random shutdowns. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode Windows laptop with heat waves rising from keyboard, temperature gauge showing critical red zone, flame warning overlay, clean design, red accent, 1080x960",
            "Dark mode Windows Control Panel Power Options screen open, cursor navigating to Change plan settings, clean minimal UI, blue accent",
            "Dark mode Advanced Power Settings dialog showing Processor Power Management tree expanded, Maximum processor state highlighted at 100 percent",
            "Dark mode same dialog showing Maximum processor state being changed to 80 percent, green checkmark appearing, clean UI",
            "Clean dark Windows desktop with CPU temperature widget showing cool 55 degrees celsius, blue cool color, green checkmark, subscribe reminder",
        ],
    },
    {
        "topic": "Night Light Enable",
        "title": "Stop Ruining Your Eyes at Night — Enable This NOW 🌙👁️ #shorts",
        "output": "FOLKS_NIGHT_LIGHT.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Protect your eyes from blue light at night — enable this feature! 🌙\n\nIn this quick tip:\n0:00 The problem — blue light destroying your sleep\n0:03 The 10-second fix\n0:04 Step 1: Win + I to open Settings\n0:06 Step 2: System → Display\n0:08 Step 3: Turn on Night Light\n0:10 Step 4: Schedule it for sunset to sunrise\n0:12 Done! Eyes protected automatically\n\n💡 This also helps you sleep faster!\n🔔 Follow for more PC tips!",
        "tags": "night light windows, blue light filter windows, protect eyes PC, windows display settings, sleep better PC tip, windows 10 tip, windows 11 tip, PC tips, folks, eye care",
        "script": """Still using your PC at full blue light brightness at night? You are destroying your sleep and your eyes. Here is the ten-second fix.
Step one. Press Windows key and I to open Settings.
Step two. Go to System then Display.
Step three. Find Night Light and toggle it on.
Step four. Click Night Light settings and schedule it to turn on automatically at sunset and off at sunrise every single day.
Done! Your screen shifts to warm colours at night, reducing blue light, helping your eyes, and making you fall asleep faster. Follow for more PC tips!""",
        "prompts": [
            "Dark mode Windows display at night showing harsh bright blue-white screen with tired eyes emoji overlay and warning icon, clean design, 1080x960",
            "Dark mode Windows Settings open showing System Display page, Night Light toggle highlighted with cursor pointing to it, blue accent UI",
            "Dark mode Night Light settings showing schedule configuration with sunset to sunrise time range being set, clean minimal UI",
            "Side by side comparison of harsh blue screen vs warm amber night light screen, clear improvement arrow between them, clean design",
            "Dark mode Windows desktop with warm amber night light enabled, moon icon in taskbar, eye health green checkmark, subscribe reminder",
        ],
    },
    {
        "topic": "Recycle Bin Recovery",
        "title": "Deleted Something Important? Recover It in 5 Seconds 🗑️✅ #shorts",
        "output": "FOLKS_RECYCLE_RECOVERY.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Accidentally deleted something important? Get it back instantly! 🗑️\n\nIn this quick tip:\n0:00 The problem — important file deleted\n0:03 The 5-second fix\n0:04 Step 1: Open Recycle Bin\n0:06 Step 2: Find your file\n0:08 Step 3: Right-click → Restore\n0:10 Done! File is back where it was\n\n💡 Bonus: Ctrl+Z immediately undoes deletion!\n🔔 Follow for more PC tips!",
        "tags": "recover deleted file windows, recycle bin restore, undo delete windows, recover lost files, windows file recovery, PC tips, folks, 5 second fix, computer tips",
        "script": """Did you accidentally delete an important file? Do not panic. Here is how to get it back in five seconds.
Step one. Open the Recycle Bin on your desktop by double-clicking it.
Step two. Find the file you deleted. You can sort by Date Deleted to find it quickly.
Step three. Right-click the file and click Restore. It goes straight back to where it was.
Done! Bonus tip: If you JUST deleted it, immediately press Control Z to undo the deletion without even opening the Recycle Bin. Follow for more PC tips!""",
        "prompts": [
            "Dark mode Windows desktop showing Recycle Bin icon with a distressed overlay and important document inside it, red warning, clean design, 1080x960",
            "Dark mode Recycle Bin window open showing deleted files sorted by date, cursor hovering over recently deleted file, clean minimal UI",
            "Dark mode right-click context menu on deleted file showing Restore option highlighted with cursor, clean UI, blue accent",
            "Dark mode Windows Explorer showing restored file back in its original folder location, green checkmark animation overlay",
            "Clean dark Windows desktop with file successfully restored, Ctrl+Z shortcut tip overlay, subscribe reminder, blue cyan accent",
        ],
    },
    {
        "topic": "Font Size Shortcut",
        "title": "Make Text BIGGER Everywhere Instantly — No Settings Needed 🔤⚡ #shorts",
        "output": "FOLKS_FONT_SHORTCUT.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Make text bigger on ANY website or app instantly! 🔤\n\nIn this quick tip:\n0:00 The problem — tiny text everywhere\n0:03 The trick\n0:04 Ctrl + Plus to zoom in\n0:06 Ctrl + Minus to zoom out\n0:08 Ctrl + 0 to reset to normal\n0:10 Works on Chrome, Edge, Word, Excel...\n0:12 Done! Perfect text size anywhere\n\n💡 Also works on most apps!\n🔔 Follow for more PC tips!",
        "tags": "make text bigger windows, zoom in browser, ctrl plus zoom, font size shortcut, browser zoom, PC shortcuts, windows tips, folks, text size fix, computer shortcuts",
        "script": """Struggling with tiny text on websites or in apps? Here is the universal shortcut that works everywhere.
Press Control and the Plus key to zoom in and make everything bigger.
Press Control and the Minus key to zoom out and make everything smaller.
Press Control and Zero to instantly reset back to the default normal size.
This works in Chrome, Edge, Firefox, Word, Excel, Notepad and most Windows apps. No need to dig through settings every time. Just three keys. Save this. Follow for more PC tips!""",
        "prompts": [
            "Dark mode browser window showing tiny unreadable text on a webpage, frustrated emoji overlay, clean design, blue accent, 1080x960 vertical",
            "Dark mode keyboard close-up showing Ctrl and Plus keys highlighted with glowing effect, zoom in animation arrow, clean minimal design",
            "Dark mode browser window showing text zooming in larger and more readable, zoom percentage counter showing 150 percent, clean UI",
            "Dark mode showing Ctrl Minus and Ctrl Zero shortcuts side by side with zoom out and reset animations, clean minimal UI",
            "Dark mode browser with perfectly sized readable text, three shortcuts shown as cheat sheet overlay, subscribe reminder, blue cyan accent",
        ],
    },
    {
        "topic": "Startup Too Many Programs",
        "title": "Why Your PC is Slow After Login — Fix in 10 Seconds 🚀💤 #shorts",
        "output": "FOLKS_STARTUP_BLOAT.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "PC slow right after you log in? Here's why and how to fix it! 🚀\n\nIn this quick fix:\n0:00 The problem — PC slow after login\n0:03 The 10-second fix\n0:04 Step 1: Ctrl+Shift+Esc → Task Manager\n0:06 Step 2: Click Startup Apps tab\n0:08 Step 3: See High impact programs\n0:10 Step 4: Right-click → Disable the bloat\n0:12 Done! 2x faster login\n\n💡 Every app you install adds itself here!\n🔔 Follow for more PC fixes!",
        "tags": "PC slow after login, startup programs windows, disable startup apps, task manager startup, slow boot fix, windows 10 fix, windows 11 fix, PC tips, folks, 10 second fix",
        "script": """Is your PC incredibly slow for the first five minutes after you log in? Here is why and the ten-second fix.
Every app you install secretly adds itself to your startup list. So when you log in twenty things all load at once, choking your PC.
Step one. Press Control Shift Escape and open Task Manager.
Step two. Click the Startup Apps tab.
Step three. Look for anything marked High impact that you do not need immediately at startup.
Step four. Right-click them one by one and hit Disable.
Done! Your login is now dramatically faster. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode Windows Task Manager showing Startup Apps tab with 15 enabled apps listed, many marked High impact in red, clean minimal UI, 1080x960",
            "Dark mode startup list with multiple High Impact apps highlighted, cursor hovering over one, right-click menu appearing with Disable option",
            "Dark mode showing startup app count dropping from 15 enabled to 4 enabled, speed improvement visualization, green arrows, clean UI",
            "Dark mode Windows login screen with a speed comparison showing slow 3 minutes vs fast 30 seconds boot with the fix applied",
            "Clean dark Windows desktop loading fast, rocket launch animation overlay, subscribe reminder, blue cyan accent, green checkmark",
        ],
    },
    {
        "topic": "Screenshot Shortcut",
        "title": "The 3 Best Windows Screenshot Shortcuts You Need to Know 📸⚡ #shorts",
        "output": "FOLKS_SCREENSHOT.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Stop using the wrong screenshot method! Here are the 3 best shortcuts 📸\n\nIn this quick tip:\n0:00 Shortcut 1: Win+Shift+S — select any area\n0:04 Shortcut 2: PrtScn — full screen to clipboard\n0:07 Shortcut 3: Win+PrtScn — saves automatically\n0:10 Bonus: Snipping Tool for annotations\n0:12 Done! Never struggle with screenshots again\n\n💡 Win+Shift+S is the best one!\n🔔 Follow for more PC tips!",
        "tags": "windows screenshot shortcut, win shift s, snipping tool, prtscn shortcut, how to screenshot windows, PC shortcuts, windows tips, folks, screenshot tip, computer shortcuts",
        "script": """Stop pressing Print Screen and getting confused. Here are the three best Windows screenshot shortcuts you need to know right now.
Number one. Windows Shift S. This opens a crosshair so you can select exactly the area you want. It copies to your clipboard automatically.
Number two. Print Screen alone. This captures the full screen and copies it to clipboard. Paste it straight into Word, Paint or anywhere.
Number three. Windows Print Screen. This captures the full screen AND automatically saves it as a file in your Screenshots folder. No pasting needed.
Bonus tip. Search for Snipping Tool in the Start menu for full annotation and delay features. Save this. Follow for more PC tips!""",
        "prompts": [
            "Dark mode Windows desktop showing screenshot crosshair selection overlay in action, Win+Shift+S keyboard shortcut displayed prominently, clean design, blue accent, 1080x960",
            "Dark mode showing three screenshot shortcuts side by side as a clean cheat sheet card — Win+Shift+S, PrtScn, Win+PrtScn — with icons",
            "Dark mode Windows clipboard notification showing screenshot captured successfully, preview thumbnail, clean minimal UI, blue accent",
            "Dark mode File Explorer showing Screenshots folder with automatically saved PNG files appearing, clean UI, green checkmark",
            "Clean dark Windows screen with all three shortcuts shown as keyboard visual, save this tip overlay, subscribe reminder, blue cyan accent",
        ],
    },
    {
        "topic": "Sticky Keys Fix",
        "title": "Stop Sticky Keys Popups in 10 Seconds 🎹⚡ #shorts",
        "output": "FOLKS_STICKY_KEYS.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Sticky Keys popups driving you crazy? Turn them off! 🎹\n\nIn this quick fix:\n0:00 The problem — popups and beeping\n0:03 The 10-second fix\n0:04 Step 1: Press Shift 5 times\n0:06 Step 2: Click 'No' to leave it off\n0:08 Step 3: Click the link to settings\n0:10 Step 4: Uncheck all three shortcuts\n0:12 Done! No more popups\n\n💡 Turn off all three: Sticky, Filter, Toggle!\n🔔 Follow for more PC fixes!",
        "tags": "sticky keys fix, turn off sticky keys, shift pressed 5 times, windows keyboard fix, filter keys off, windows 10 fix, windows 11 fix, PC tips, folks, quick fix",
        "script": """Is your keyboard suddenly beeping and popping up a Sticky Keys box when you press Shift? Here is how to kill it forever in ten seconds.
Step one. Press the Shift key five times fast to trigger the Sticky Keys dialog.
Step two. Click No to say you do not want it on.
Step three. Then click the link that says click here to disable the keyboard shortcut.
Step four. Uncheck every single box so Sticky Keys, Filter Keys and Toggle Keys never turn on again.
Done! No more beeping, no more popups. Save this video. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode Windows showing Sticky Keys popup dialog asking to turn on Sticky Keys, cursor hovering over No button, clean minimal UI, blue accent, 1080x960 vertical",
            "Dark mode Windows settings Keyboard page with Sticky Keys toggle OFF, green checkmark, clean UI, blue cyan accent",
            "Dark mode Windows showing keyboard shortcut dialog with all three boxes unchecked, red X over beeping keyboard icon, clean minimal design",
            "Dark mode Windows desktop typing normally with no popups, keyboard glowing calm green, clean UI, subscribe reminder overlay",
        ],
    },
    {
        "topic": "Windows Key Not Working",
        "title": "Windows Key Dead? 10-Second Fix 🪟⚡ #shorts",
        "output": "FOLKS_WINDOWS_KEY.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Press the Windows key and nothing happens? Fix it! 🪟\n\nIn this quick fix:\n0:00 The problem — Windows key does nothing\n0:03 The 10-second fix\n0:04 Step 1: Press Fn + Windows key\n0:06 Step 2: Check for F-Lock on your keyboard\n0:08 Step 3: Restart Windows Explorer\n0:10 Step 4: Reboot the PC\n0:12 Done! Start menu opens again\n\n💡 Fn + Win toggles it on many laptops!\n🔔 Follow for more PC fixes!",
        "tags": "windows key not working, start menu not opening fix, fn lock windows key, keyboard fix, windows explorer restart, windows 10 fix, windows 11 fix, PC tips, folks",
        "script": """Does pressing the Windows key do absolutely nothing? The Start menu is dead. Here is the ten-second fix.
Step one. On many laptops the Windows key is disabled by the Fn lock. Press Fn together with the Windows key to re-enable it.
Step two. Look for an F-Lock key and toggle it on if your keyboard has one.
Step three. Still dead? Press Control Shift Escape, find Windows Explorer in the list, right-click it and click Restart.
Step four. If it still fails, simply reboot your PC.
Done! Your Start menu is back. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode Windows keyboard with Windows logo key glowing red X, question mark overlay, clean minimal UI, blue accent, 1080x960 vertical",
            "Dark mode laptop keyboard with Fn key and Windows key highlighted with connecting arrow, clean UI, blue cyan accent",
            "Dark mode Task Manager with Windows Explorer selected and Restart button highlighted, clean minimal design, blue accent",
            "Dark mode Windows desktop with Start menu popping open successfully, green checkmark, subscribe reminder overlay",
        ],
    },
    {
        "topic": "Num Lock Fix",
        "title": "Numbers Typing as Symbols? NumLock Fix 🔢⚡ #shorts",
        "output": "FOLKS_NUMLOCK_FIX.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Typing numbers and getting symbols? NumLock is off! 🔢\n\nIn this quick fix:\n0:00 The problem — symbols instead of numbers\n0:03 The 5-second fix\n0:04 Step 1: Find the NumLock key\n0:06 Step 2: Press it once\n0:08 Step 3: Light on = numbers work\n0:10 Pro tip: Set NumLock on at startup in BIOS\n0:12 Done! Numbers type correctly\n\n💡 The light must be ON!\n🔔 Follow for more PC fixes!",
        "tags": "num lock fix, numbers typing symbols, num lock off, keyboard number keys wrong, laptop num lock, windows fix, PC tips, folks, quick fix",
        "script": """Are you typing numbers but getting symbols like exclamation points and at signs instead? Your NumLock is off. Here is the fix.
Step one. Find the NumLock key on your keyboard, usually above the number pad or in the top row on a laptop.
Step two. Press it once and watch the little indicator light.
Step three. When the light is on your numbers type correctly again.
Pro tip. To keep NumLock on at startup, enter your BIOS and set NumLock state to On. Save this. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode keyboard closeup with NumLock key glowing red off state, symbols overlay on number keys, clean minimal UI, blue accent, 1080x960",
            "Dark mode keyboard with NumLock key glowing green on state, numbers 0-9 highlighted cleanly, blue cyan accent",
            "Dark mode laptop showing NumLock indicator light location highlighted with arrow, clean UI, blue accent",
            "Dark mode BIOS screen with NumLock state set to On highlighted, green checkmark, clean minimal design, subscribe reminder",
        ],
    },
    {
        "topic": "Right Click Menu Slow",
        "title": "Right-Click Menu TOO Slow? Windows 11 Fix 🖱️⚡ #shorts",
        "output": "FOLKS_RIGHT_CLICK_SLOW.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Right-click menu takes forever to open? Fix it! 🖱️\n\nIn this quick fix:\n0:00 The problem — slow right-click menu\n0:03 The 10-second fix\n0:04 Step 1: Click 'Show more options'\n0:06 Step 2: Use Shift + right-click for full menu\n0:08 Step 3: Disable Shell Extensions\n0:10 Step 4: Remove broken context items\n0:12 Done! Instant menu\n\n💡 Shift + right-click is the fastest!\n🔔 Follow for more PC fixes!",
        "tags": "right click slow fix, context menu slow windows 11, show more options, shift right click, shell extensions, windows 11 fix, PC tips, folks, quick fix",
        "script": """Is your right-click menu in Windows 11 taking forever to appear? Here is the ten-second fix.
Step one. The quickest workaround — press Shift and right-click at the same time to jump straight to the full classic menu.
Step two. Or right-click and choose Show more options at the bottom.
Step three. For a permanent fix, open Task Manager and click on Startup apps to disable junk.
Step four. Use a tool like ShellExView to remove broken shell extensions that slow the menu down.
Done! Right-clicking is instant again. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode Windows 11 right-click menu with loading spinner and hourglass, frustrated cursor, clean minimal UI, blue accent, 1080x960",
            "Dark mode Windows 11 showing Show more options entry highlighted in context menu, clean UI, blue cyan accent",
            "Dark mode keyboard visual with Shift and right-click highlighted together, lightning fast arrow, blue accent",
            "Dark mode Task Manager Startup tab with junk apps disabled with green checkmark, clean minimal design, subscribe reminder",
        ],
    },
    {
        "topic": "Alt Tab Not Working",
        "title": "Alt+Tab Broken? 10-Second Fix 🔄⚡ #shorts",
        "output": "FOLKS_ALT_TAB.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Alt+Tab not switching windows? Here's the fix! 🔄\n\nIn this quick fix:\n0:00 The problem — Alt+Tab does nothing\n0:03 The 10-second fix\n0:04 Step 1: Restart Windows Explorer\n0:06 Step 2: Update your GPU drivers\n0:08 Step 3: Check keyboard shortcuts settings\n0:10 Step 4: Turn off overlay apps\n0:12 Done! Alt+Tab works again\n\n💡 Restart Explorer first — fixes 80%!\n🔔 Follow for more PC fixes!",
        "tags": "alt tab not working, alt tab fix, window switcher broken, restart windows explorer, gpu driver update, windows 10 fix, windows 11 fix, PC tips, folks",
        "script": """Is Alt Tab suddenly doing nothing and you cannot switch windows? Here is the ten-second fix.
Step one. Press Control Shift Escape to open Task Manager, find Windows Explorer, right-click and hit Restart.
Step two. If that does not fix it, update your graphics card drivers from the manufacturer's website.
Step three. Check in Settings that Alt Tab behavior has not been changed to only show the current desktop.
Step four. Close overlay apps like game launchers that sometimes block Alt Tab.
Done! Switching windows works again. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode keyboard with Alt and Tab keys glowing red X, window switcher broken overlay, clean minimal UI, blue accent, 1080x960",
            "Dark mode Task Manager with Windows Explorer selected and Restart highlighted, clean UI, blue cyan accent",
            "Dark mode multiple app windows stacked with arrow switching between them working, green checkmark, blue accent",
            "Dark mode Windows settings Multitasking page with Alt Tab options shown, clean minimal design, subscribe reminder",
        ],
    },
    {
        "topic": "Screen Zoomed In",
        "title": "Screen STUCK Zoomed In? 10-Second Fix 🔍⚡ #shorts",
        "output": "FOLKS_SCREEN_ZOOM.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Everything on screen is huge? Reset zoom now! 🔍\n\nIn this quick fix:\n0:00 The problem — screen stuck zoomed in\n0:03 The 10-second fix\n0:04 Step 1: Press Ctrl + 0 to reset zoom\n0:06 Step 2: Press Ctrl + - to zoom out\n0:08 Step 3: Hold Ctrl and scroll to adjust\n0:10 Step 4: Press Win + Esc to exit Magnifier\n0:12 Done! Screen back to normal\n\n💡 Ctrl + 0 = reset to 100%!\n🔔 Follow for more PC fixes!",
        "tags": "screen zoomed in fix, reset browser zoom, ctrl 0 zoom, magnifier off, windows zoom stuck, PC tips, folks, quick fix, windows 11 fix",
        "script": """Is your whole screen suddenly zoomed in and gigantic? Here is the ten-second fix.
Step one. Press Control and zero together to reset your browser zoom back to one hundred percent.
Step two. If the whole Windows screen is enlarged, hold Control and press minus to zoom back out.
Step three. You can also hold Control and scroll with your mouse wheel to fine tune the zoom level.
Step four. If a big magnifier box is following your cursor, press the Windows key plus Escape to turn off the Magnifier tool.
Done! Everything is back to normal size. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode Windows desktop with huge oversized icons and zoomed in text, confused cursor, clean minimal UI, blue accent, 1080x960",
            "Dark mode keyboard visual with Ctrl and zero keys highlighted together, reset arrow icon, clean UI, blue cyan accent",
            "Dark mode browser showing zoom percentage resetting from 150 percent to 100 percent, green checkmark, blue accent",
            "Dark mode Windows desktop back to normal size with perfect icons, subscribe reminder overlay",
        ],
    },
    {
        "topic": "USB Drive Not Recognized",
        "title": "USB Drive Not Showing? 10-Second Fix 💾⚡ #shorts",
        "output": "FOLKS_USB_NOT_SHOWING.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Plugged in a USB and nothing shows up? Fix it! 💾\n\nIn this quick fix:\n0:00 The problem — USB drive not showing\n0:03 The 10-second fix\n0:04 Step 1: Try a different USB port\n0:06 Step 2: Check Disk Management\n0:08 Step 3: Assign a drive letter\n0:10 Step 4: Update USB drivers\n0:12 Done! Drive appears\n\n💡 Disk Management finds hidden drives!\n🔔 Follow for more PC fixes!",
        "tags": "usb drive not showing, usb not recognized fix, assign drive letter, disk management usb, usb driver update, windows 10 fix, windows 11 fix, PC tips, folks",
        "script": """Is your USB drive plugged in but not showing up in File Explorer? Here is the ten-second fix.
Step one. Try plugging it into a different USB port, ideally directly into the back of your PC.
Step two. Right-click the Start button and open Disk Management to see if the drive appears there.
Step three. If it shows up without a drive letter, right-click the partition, choose Change Drive Letter and assign one.
Step four. If nothing appears at all, open Device Manager, find your USB controllers, and update or reinstall their drivers.
Done! Your USB drive shows up again. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode Windows File Explorer with no USB drive visible, confused user overlay, USB stick icon, clean minimal UI, blue accent, 1080x960",
            "Dark mode Disk Management window with unrecognized USB drive highlighted, clean UI, blue cyan accent",
            "Dark mode Change Drive Letter dialog with a new letter being assigned, green checkmark, blue accent",
            "Dark mode File Explorer now showing USB drive with files visible, subscribe reminder overlay",
        ],
    },
    {
        "topic": "PC Wakes Up By Itself",
        "title": "PC Wakes Up By Itself? Fix It Now 💤⚡ #shorts",
        "output": "FOLKS_PC_WAKES_UP.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "PC keeps waking up on its own? Here's the fix! 💤\n\nIn this quick fix:\n0:00 The problem — PC wakes up alone\n0:03 The 10-second fix\n0:04 Step 1: Open Command Prompt as admin\n0:06 Step 2: Type powercfg /lastwake\n0:08 Step 3: It shows the culprit device\n0:10 Step 4: Disable wake for that device\n0:12 Done! PC stays asleep\n\n💡 Usually a mouse or network card!\n🔔 Follow for more PC fixes!",
        "tags": "pc wakes up by itself, computer wakes on own fix, powercfg lastwake, disable wake device, sleep mode fix, windows 10 fix, windows 11 fix, PC tips, folks",
        "script": """Does your PC keep waking up from sleep by itself in the middle of the night? Here is the ten-second fix.
Step one. Right-click the Start button and open Terminal or Command Prompt as Administrator.
Step two. Type powercfg space /lastwake and press Enter.
Step three. Windows will list the exact device that woke your PC — usually a mouse or network card.
Step four. Open Device Manager, right-click that device, go to Power Management and uncheck Allow this device to wake the computer.
Done! Your PC stays asleep. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode PC monitor turning on by itself at night with clock showing 3 AM, confused emoji overlay, clean minimal UI, blue accent, 1080x960",
            "Dark mode Command Prompt window showing powercfg /lastwake output with device name highlighted, blue cyan accent",
            "Dark mode Device Manager with mouse device Power Management tab open and wake checkbox unchecked, clean UI",
            "Dark mode PC sleeping peacefully with moon icon and green checkmark, subscribe reminder overlay",
        ],
    },
    {
        "topic": "Corrupted System Files",
        "title": "Fix Corrupted Windows Files in 60 Seconds 🔧⚡ #shorts",
        "output": "FOLKS_SFC_SCAN.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Weird errors and crashes? Corrupted files! 🔧\n\nIn this quick fix:\n0:00 The problem — random errors & crashes\n0:03 The 60-second fix\n0:04 Step 1: Open Command Prompt as admin\n0:06 Step 2: Type sfc /scannow\n0:08 Step 3: Let it scan and repair\n0:10 Step 4: Then run DISM /Online /Cleanup-Image\n0:12 Done! System files fixed\n\n💡 Run both commands for best results!\n🔔 Follow for more PC fixes!",
        "tags": "sfc scannow, corrupted system files fix, dism cleanup image, repair windows files, command prompt fix, windows 10 fix, windows 11 fix, PC tips, folks",
        "script": """Is Windows throwing random errors and crashing for no reason? You may have corrupted system files. Here is how to fix them.
Step one. Right-click the Start button and open Terminal as Administrator.
Step two. Type sfc space forward slash scannow and press Enter. This scans and repairs protected system files.
Step three. When it finishes, run this second command: DISM space forward slash Online space forward slash Cleanup-Image space forward slash RestoreHealth.
Step four. Let it finish, then reboot your PC.
Done! Corrupted Windows files are repaired. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode Windows with warning popups and red error badges, corrupted file icons, clean minimal UI, blue accent, 1080x960",
            "Dark mode Command Prompt running sfc /scannow with progress bar scanning gears, blue cyan accent",
            "Dark mode Command Prompt running DISM RestoreHealth with progress percentage, clean UI, blue accent",
            "Dark mode healthy Windows desktop with green shield checkmark, subscribe reminder overlay",
        ],
    },
    {
        "topic": "Downloads Going to OneDrive",
        "title": "Downloads Going to OneDrive? Fix It 📥⚡ #shorts",
        "output": "FOLKS_ONEDRIVE_DOWNLOADS.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Files saving to OneDrive instead of your PC? Fix it! 📥\n\nIn this quick fix:\n0:00 The problem — downloads go to OneDrive\n0:03 The 10-second fix\n0:04 Step 1: Open File Explorer\n0:06 Step 2: Right-click Downloads folder\n0:08 Step 3: Click Properties → Location\n0:10 Step 4: Move it to This PC\n0:12 Done! Files stay local\n\n💡 Keeps your cloud storage from filling up!\n🔔 Follow for more PC fixes!",
        "tags": "downloads going to onedrive fix, move downloads folder, change download location, onedrive storage full, file explorer fix, windows 10 fix, windows 11 fix, PC tips, folks",
        "script": """Are your downloads mysteriously saving to OneDrive instead of your hard drive? Here is the ten-second fix.
Step one. Open File Explorer and find the Downloads folder on the left side.
Step two. Right-click Downloads and choose Properties.
Step three. Click the Location tab, then click Move and pick a folder on your main drive, like C colon backslash Downloads.
Step four. Click Apply, then choose Yes to move your existing files.
Done! Your downloads stay on your PC, not the cloud. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode File Explorer with downloads icon linked to OneDrive cloud, red arrow pointing away, clean minimal UI, blue accent, 1080x960",
            "Dark mode Downloads folder Properties window with Location tab highlighted, clean UI, blue cyan accent",
            "Dark mode Move Folder dialog selecting local This PC Downloads path, green checkmark, blue accent",
            "Dark mode File Explorer showing Downloads folder with local hard drive icon, subscribe reminder overlay",
        ],
    },
    {
        "topic": "Dark Mode Not Working",
        "title": "Dark Mode Not Applying? Force It On 🌙⚡ #shorts",
        "output": "FOLKS_DARK_MODE.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Dark mode won't stick? Here's the fix! 🌙\n\nIn this quick fix:\n0:00 The problem — dark mode won't apply\n0:03 The 10-second fix\n0:04 Step 1: Open Settings → Personalization\n0:06 Step 2: Click Colors\n0:08 Step 3: Set both modes to Dark\n0:10 Step 4: Restart the app\n0:12 Done! Everything goes dark\n\n💡 Set BOTH Windows and app mode!\n🔔 Follow for more PC fixes!",
        "tags": "dark mode not working, force dark mode windows, personalization colors, dark theme fix, windows 10 fix, windows 11 fix, PC tips, folks, quick fix",
        "script": """Is dark mode not applying to all your apps? Here is the ten-second fix.
Step one. Open Settings and go to Personalization.
Step two. Click on Colors on the left side.
Step three. Under Choose your mode, set both the Windows mode and the app mode to Dark.
Step four. Some stubborn apps need a restart — close and reopen them to pick up the dark theme.
Done! Everything is dark and easy on the eyes. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode Windows Personalization Colors settings with both mode dropdowns set to Dark highlighted, clean minimal UI, blue accent, 1080x960",
            "Split screen showing white mode versus dark mode with arrow pointing to dark side, blue cyan accent",
            "Dark mode File Explorer and apps all dark themed with moon icon, green checkmark, clean UI",
            "Dark mode cozy desktop fully dark with subscribe reminder overlay",
        ],
    },
    {
        "topic": "PDF Opens in Browser",
        "title": "PDF Opens in Browser? Change It 📄⚡ #shorts",
        "output": "FOLKS_PDF_DEFAULT.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "PDFs always open in your browser? Fix it! 📄\n\nIn this quick fix:\n0:00 The problem — PDFs open in Chrome/Edge\n0:03 The 10-second fix\n0:04 Step 1: Right-click a PDF file\n0:06 Step 2: Click Open with → Choose another app\n0:08 Step 3: Pick your PDF reader\n0:10 Step 4: Check 'Always' to keep it\n0:12 Done! PDFs open properly\n\n💡 Pick Adobe Reader or Sumatra PDF!\n🔔 Follow for more PC fixes!",
        "tags": "pdf opens in browser fix, change pdf default app, open with always, adobe reader default, pdf reader fix, windows 10 fix, windows 11 fix, PC tips, folks",
        "script": """Are your PDF files always opening in the browser instead of a proper reader? Here is the ten-second fix.
Step one. Right-click any PDF file on your PC.
Step two. Hover over Open with and click Choose another app.
Step three. Pick your favorite PDF reader like Adobe Reader, Foxit, or Sumatra PDF.
Step four. Click the box that says Always use this app to open PDF files, then hit OK.
Done! PDFs now open in a real reader, not your browser. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode PDF file icon with browser globe overlay and red X, frustrated cursor, clean minimal UI, blue accent, 1080x960",
            "Dark mode Open with dialog with Always checkbox highlighted and Adobe Reader selected, blue cyan accent",
            "Dark mode PDF reader app open with document cleanly displayed, green checkmark, blue accent",
            "Dark mode desktop with PDF thumbnails showing reader app icons, subscribe reminder overlay",
        ],
    },
    {
        "topic": "Cursor Hard to Find",
        "title": "Mouse Cursor Hard to Find? Make It BIGGER 🖱️⚡ #shorts",
        "output": "FOLKS_BIG_CURSOR.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Losing your mouse cursor? Make it huge! 🖱️\n\nIn this quick fix:\n0:00 The problem — cursor impossible to find\n0:03 The 10-second fix\n0:04 Step 1: Open Settings → Accessibility\n0:06 Step 2: Click Mouse pointer and touch\n0:08 Step 3: Drag the size slider up\n0:10 Step 4: Pick a high-contrast color\n0:12 Done! Cursor easy to spot\n\n💡 Turn on the pointer finder too!\n🔔 Follow for more PC fixes!",
        "tags": "cursor hard to find, make mouse cursor bigger, mouse pointer size, accessibility pointer, high contrast cursor, windows 10 fix, windows 11 fix, PC tips, folks",
        "script": """Are you constantly losing your mouse cursor on a big or bright screen? Here is the ten-second fix.
Step one. Open Settings and go to Accessibility.
Step two. Click on Mouse pointer and touch.
Step three. Drag the cursor size slider to the right to make it bigger.
Step four. Pick a bright high-contrast color so it pops on any background. You can also turn on the pointer finder so pressing Control makes a ring around it.
Done! You will never lose your cursor again. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode huge bright desktop with tiny invisible cursor, magnifying glass searching, clean minimal UI, blue accent, 1080x960",
            "Dark mode Windows Accessibility Mouse pointer settings with size slider dragged large, blue cyan accent",
            "Dark mode desktop with large bright yellow high-contrast cursor clearly visible, green checkmark, blue accent",
            "Dark mode Windows with pointer finder ring pulsing around cursor, subscribe reminder overlay",
        ],
    },
    {
        "topic": "Taskbar Not Hiding",
        "title": "Taskbar Won't Hide? Auto-Hide Fix 📉⚡ #shorts",
        "output": "FOLKS_TASKBAR_HIDE.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Taskbar keeps showing in fullscreen? Fix it! 📉\n\nIn this quick fix:\n0:00 The problem — taskbar won't hide\n0:03 The 10-second fix\n0:04 Step 1: Right-click taskbar → Settings\n0:06 Step 2: Toggle on Auto-hide\n0:08 Step 3: Move your mouse down to reveal\n0:10 Step 4: Disable taskbar overlays in apps\n0:12 Done! Fullscreen is truly full\n\n💡 Great for games and videos!\n🔔 Follow for more PC fixes!",
        "tags": "taskbar not hiding fix, auto hide taskbar, fullscreen taskbar fix, taskbar settings, windows 11 fix, PC tips, folks, quick fix",
        "script": """Is your taskbar staying visible in fullscreen games and videos? Here is the ten-second fix.
Step one. Right-click an empty spot on the taskbar and choose Taskbar settings.
Step two. Turn on Automatically hide the taskbar.
Step three. The taskbar now slides away and reappears only when you move your mouse to the bottom edge.
Step four. If an app still forces it open, look for a fullscreen or overlay setting inside that app and turn it off.
Done! Your screen is truly fullscreen. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode Windows fullscreen video with taskbar stubbornly visible at bottom, red X overlay, clean minimal UI, blue accent, 1080x960",
            "Dark mode Taskbar settings with Auto-hide toggle switched ON highlighted, blue cyan accent",
            "Dark mode desktop with taskbar sliding down and away, smooth motion arrow, blue accent",
            "Dark mode clean fullscreen desktop with no taskbar visible, green checkmark, subscribe reminder",
        ],
    },
    {
        "topic": "Lock Screen Photo Not Changing",
        "title": "Lock Screen Won't Change Photo? Fix It 🔐⚡ #shorts",
        "output": "FOLKS_LOCK_SCREEN.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Lock screen stuck on the same photo? Fix it! 🔐\n\nIn this quick fix:\n0:00 The problem — lock screen won't change\n0:03 The 10-second fix\n0:04 Step 1: Open Settings → Personalization\n0:06 Step 2: Click Lock screen\n0:08 Step 3: Switch from Slideshow to Picture\n0:10 Step 4: Browse to your photo\n0:12 Done! New lock screen!\n\n💡 Slideshow can ignore your picks!\n🔔 Follow for more PC fixes!",
        "tags": "lock screen photo not changing, lock screen fix, personalize lock screen, change lock screen picture, windows 10 fix, windows 11 fix, PC tips, folks",
        "script": """Is your lock screen stuck on the same photo no matter what you pick? Here is the ten-second fix.
Step one. Open Settings and go to Personalization.
Step two. Click Lock screen on the left.
Step three. If it is set to Slideshow, switch it to Picture — a slideshow can override your selected image.
Step four. Click Browse and choose the photo you want to use.
Done! Your lock screen finally shows the picture you picked. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode Windows lock screen with old generic photo, refresh icon circled in red, clean minimal UI, blue accent, 1080x960",
            "Dark mode Personalization Lock screen settings with Picture selected and Browse highlighted, blue cyan accent",
            "Dark mode file picker selecting a beautiful photo, green checkmark, blue accent",
            "Dark mode lock screen now showing the chosen photo, subscribe reminder overlay",
        ],
    },
    {
        "topic": "Sound Too Quiet",
        "title": "Sound MAXED but Still Quiet? Fix It 🔊⚡ #shorts",
        "output": "FOLKS_SOUND_QUIET.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Volume at 100% but still quiet? Fix it! 🔊\n\nIn this quick fix:\n0:00 The problem — max volume still too quiet\n0:03 The 10-second fix\n0:04 Step 1: Right-click speaker icon\n0:06 Step 2: Open Sound settings\n0:08 Step 3: Go to Speaker properties\n0:10 Step 4: Turn on Loudness Equalization\n0:12 Done! Sound is noticeably louder\n\n💡 Use the Enhancements tab!\n🔔 Follow for more PC fixes!",
        "tags": "sound too quiet fix, volume max but quiet, loudness equalization, speaker enhancements, boost windows volume, windows 10 fix, windows 11 fix, PC tips, folks",
        "script": """Is your volume at one hundred percent but still too quiet? Here is the ten-second fix.
Step one. Right-click the speaker icon in the taskbar and choose Sound settings.
Step two. Click on your output device, then click Device properties.
Step three. Scroll down and click Additional device properties, then open the Enhancements tab.
Step four. Check Loudness Equalization and click Apply. This boosts quiet audio dramatically.
Done! Your sound is noticeably louder. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode Windows speaker icon at 100 percent volume but tiny quiet sound waves, clean minimal UI, blue accent, 1080x960",
            "Dark mode Windows Sound settings with speaker device selected, blue cyan accent",
            "Dark mode Speaker Properties Enhancements tab with Loudness Equalization checked, loud sound waves, blue accent",
            "Dark mode Windows with big green sound waves and volume icon at full power, subscribe reminder",
        ],
    },
    {
        "topic": "Clock Wrong Time",
        "title": "PC Clock Always Wrong? Fix It in 10 Seconds 🕐⚡ #shorts",
        "output": "FOLKS_CLOCK_WRONG.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Your clock keeps resetting to the wrong time? Fix it! 🕐\n\nIn this quick fix:\n0:00 The problem — clock always wrong\n0:03 The 10-second fix\n0:04 Step 1: Right-click clock → Adjust date/time\n0:06 Step 2: Turn on Set time automatically\n0:08 Step 3: Toggle sync now\n0:10 Step 4: Check the timezone is right\n0:12 Done! Clock stays correct\n\n💡 If it keeps resetting, it's the CMOS battery!\n🔔 Follow for more PC fixes!",
        "tags": "clock wrong time fix, pc time resetting, set time automatically, timezone fix, cmos battery, windows 10 fix, windows 11 fix, PC tips, folks",
        "script": """Is your PC clock always showing the wrong time no matter how often you fix it? Here is how to fix it.
Step one. Right-click the clock in the taskbar and choose Adjust date and time.
Step two. Make sure Set time automatically is turned on.
Step three. Click Sync now to force Windows to grab the correct time from the internet.
Step four. Check your timezone is correct too. If the clock keeps resetting after shutdown, the CMOS battery on your motherboard is dying and should be replaced.
Done! Your clock stays accurate. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode Windows clock in taskbar showing completely wrong time, red X overlay, clean minimal UI, blue accent, 1080x960",
            "Dark mode Windows Date and Time settings with Set time automatically ON and Sync now highlighted, blue cyan accent",
            "Dark mode world map showing correct timezone selection, green checkmark, blue accent",
            "Dark mode taskbar clock showing correct time with wifi sync icon, subscribe reminder overlay",
        ],
    },
    {
        "topic": "Windows Update Fails",
        "title": "Windows Update Stuck or Failing? Fix It 🔄⚡ #shorts",
        "output": "FOLKS_UPDATE_FAIL.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Windows Update keeps failing? Here's the fix! 🔄\n\nIn this quick fix:\n0:00 The problem — updates stuck or failing\n0:03 The 60-second fix\n0:04 Step 1: Run the Update troubleshooter\n0:06 Step 2: Restart the Windows Update service\n0:08 Step 3: Clear the update cache\n0:10 Step 4: Try the update again\n0:12 Done! Updates install cleanly\n\n💡 Clearing the cache fixes most errors!\n🔔 Follow for more PC fixes!",
        "tags": "windows update stuck fix, update failing fix, windows update troubleshooter, clear update cache, update service restart, windows 10 fix, windows 11 fix, PC tips, folks",
        "script": """Is Windows Update stuck or throwing errors every time? Here is how to fix it.
Step one. Open Settings, go to System, then Troubleshoot, and run the Windows Update troubleshooter.
Step two. Press Windows key R, type services.msc, find Windows Update, right-click it and click Restart.
Step three. Still failing? Clear the update cache by deleting the contents of C colon backslash Windows backslash SoftwareDistribution.
Step four. Go back to Windows Update and click Check for updates again.
Done! Updates install cleanly. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode Windows Update settings with red error badge and spinning stuck loader, clean minimal UI, blue accent, 1080x960",
            "Dark mode Windows Troubleshoot settings with Windows Update troubleshooter selected, blue cyan accent",
            "Dark mode Services window with Windows Update service highlighted and Restart button, clean UI, blue accent",
            "Dark mode Windows Update installing successfully with green checkmark, subscribe reminder overlay",
        ],
    },
    {
        "topic": "Laptop Battery Not Charging",
        "title": "Laptop Plugged In but NOT Charging? Fix 🔋⚡ #shorts",
        "output": "FOLKS_BATTERY_NOT_CHARGING.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Laptop plugged in but battery won't charge? Fix it! 🔋\n\nIn this quick fix:\n0:00 The problem — plugged in, not charging\n0:03 The 10-second fix\n0:04 Step 1: Check the charger and cable\n0:06 Step 2: Try another outlet\n0:08 Step 3: Restart with charger plugged in\n0:10 Step 4: Run battery diagnostics\n0:12 Done! Charging again\n\n💡 Battery drivers can get stuck!\n🔔 Follow for more PC fixes!",
        "tags": "laptop not charging fix, plugged in not charging, battery driver reset, battery diagnostics, ac adapter fix, windows 10 fix, windows 11 fix, PC tips, folks",
        "script": """Is your laptop plugged in but the battery is not charging? Here is the ten-second fix.
Step one. Check the charger, cable and port — a loose connection is the most common cause. Try a different outlet too.
Step two. Shut down the laptop, unplug it, hold the power button for fifteen seconds, then plug it back in and start it up.
Step three. Still not charging? Open Device Manager, expand Batteries, right-click each battery entry and choose Uninstall, then restart. Windows reinstalls them.
Step four. Run a battery diagnostic in the BIOS or manufacturer's app to check battery health.
Done! Your battery charges again. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode laptop with power cable plugged in but battery icon showing red not charging status, clean minimal UI, blue accent, 1080x960",
            "Dark mode charging cable closeup with loose connector highlighted, warning icon, blue cyan accent",
            "Dark mode Device Manager Batteries section with entries selected for uninstall, clean UI, blue accent",
            "Dark mode laptop battery icon now filling green with lightning bolt charging, subscribe reminder overlay",
        ],
    },
    {
        "topic": "Second Monitor Not Detected",
        "title": "Second Monitor Not Detecting? Fix It 🖥️⚡ #shorts",
        "output": "FOLKS_SECOND_MONITOR.mp4",
        "voice": "en-US-AndrewNeural",
        "gameplay": SUBWAY_SURFERS,
        "font_size": 60,
        "highlight_color": (0, 200, 255, 255),
        "caption_position": "center",
        "ui_variant": None,
        "description": "Second monitor showing 'no signal'? Fix it! 🖥️\n\nIn this quick fix:\n0:00 The problem — second monitor not detected\n0:03 The 10-second fix\n0:04 Step 1: Press Win + P\n0:06 Step 2: Choose Extend\n0:08 Step 3: Try another cable or port\n0:10 Step 4: Update display drivers\n0:12 Done! Both monitors work\n\n💡 Win + P toggles display modes!\n🔔 Follow for more PC fixes!",
        "tags": "second monitor not detected fix, dual monitor not working, win p extend, no signal monitor, display driver update, windows 10 fix, windows 11 fix, PC tips, folks",
        "script": """Is your second monitor showing no signal or not being detected? Here is the ten-second fix.
Step one. Press the Windows key and P together to open the projection menu.
Step two. Click Extend so Windows knows you want to use both screens.
Step three. If the monitor still shows no signal, try a different cable or port — HDMI, DisplayPort or USB-C.
Step four. Update your graphics drivers from the manufacturer's site to fix detection issues.
Done! Both monitors are working. Follow for more quick PC fixes!""",
        "prompts": [
            "Dark mode dual monitor setup with second monitor showing no signal red X, clean minimal UI, blue accent, 1080x960",
            "Dark mode Windows Win+P projection menu with Extend option highlighted, blue cyan accent",
            "Dark mode monitor port closeup with HDMI cable being connected, clean UI, blue accent",
            "Dark mode dual monitors both showing wallpaper perfectly, green checkmark, subscribe reminder overlay",
        ],
    },
]

# ──────────────────────────────────────────────────────────────
# All channels mapped
# ──────────────────────────────────────────────────────────────
CHANNELS = {
    "sigma": {
        "name": "SigmaChoices",
        "handle": "@SigmaChoices",
        "niche": "Brainrot Would You Rather",
        "videos": SIGMA_CHOICES_VIDEOS,
        "output_dir": os.path.join("output", "sigma"),
    },
    "versus": {
        "name": "BrainrotVersus",
        "handle": "@BrainrotVersus",
        "niche": "Meme Character Battles",
        "videos": BRAINROT_VERSUS_VIDEOS,
        "output_dir": os.path.join("output", "versus"),
    },
    "attention": {
        "name": "AttentionCooked",
        "handle": "@AttentionCooked",
        "niche": "Interactive Retention Tests",
        "videos": ATTENTION_COOKED_VIDEOS,
        "output_dir": os.path.join("output", "attention"),
    },
    "critter": {
        "name": "WhoDatCritter",
        "handle": "@WhoDatCritter",
        "niche": "Kids Guessing Game (Brainrot/Sludge)",
        "videos": CRITTER_VIDEOS,
        "output_dir": os.path.join("output", "critter"),
    },
    "money": {
        "name": "RichRules",
        "handle": "@RichRules",
        "niche": "Money Rules & Psychology Shorts",
        "videos": MONEY_VIDEOS,
        "output_dir": os.path.join("output", "money"),
    },
    "folks": {
        "name": "Folks",
        "handle": "@folks",
        "niche": "Software Tips, Fixes & Bug Alerts",
        "videos": FOLKS_VIDEOS,
        "output_dir": os.path.join("output", "folks"),
    },
}


def is_video_uploaded(channel_name: str, topic: str) -> bool:
    """Check if a video topic is already marked as Uploaded in the database."""
    try:
        db_path = os.path.join("data", "youtube_journal.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("""
            SELECT status FROM videos v
            JOIN channels c ON v.channel_id = c.id
            WHERE c.name = ? AND v.topic = ?
        """, (channel_name, topic))
        row = c.fetchone()
        conn.close()
        if row and row[0] == "Uploaded":
            return True
    except sqlite3.Error as e:
        print(f"⚠️  DB check failed for {channel_name}/{topic}: {e}")
    return False


def generate_video(channel_key: str, video_def: dict, dry_run: bool = False,
                   experiment_id: int | None = None, overrides: dict | None = None):
    """Generate a single video and log it to the journal."""
    ch = CHANNELS[channel_key]
    output_dir = ch.get("output_dir", ".")
    os.makedirs(output_dir, exist_ok=True)
    output = os.path.join(output_dir, video_def["output"])
    topic = video_def["topic"]

    # NEVER re-generate videos that are already uploaded to YouTube!
    if is_video_uploaded(ch["name"], topic):
        print(f"⏭️  SKIP (already uploaded to YouTube): {ch['name']} - {topic}")
        return output

    if overrides:
        output = os.path.join(output_dir, video_def["output"].replace(".mp4", f"_{overrides.get('_tag', 'x')}.mp4"))

    if os.path.exists(output):
        print(f"⏭️  SKIP (already exists on disk): {output}")
        return output

    if dry_run:
        print(f"📝 WOULD GENERATE: {output} ({video_def['topic']}) for {ch['name']}")
        return None

    print(f"\n{'='*60}")
    print(f"🎬 Generating: {video_def['topic']} → {output}")
    print(f"📺 Channel: {ch['name']}")
    if experiment_id:
        print(f"🧪 Experiment: {experiment_id}")
    if overrides:
        print(f"🔬 Overrides: {overrides}")
    print(f"{'='*60}\n")

    t0 = time.time()

    ui_variant = video_def.get("ui_variant")
    if ui_variant:
        from app.video import ui_graphics

        ui_dir = os.path.join("data", os.path.splitext(os.path.basename(output))[0].lower())
        ui_graphics.render_scenes(ui_dir, ui_variant)

    def _ov(key, default):
        """Resolve a parameter: overrides first, then video_def, then default."""
        if overrides and key in overrides:
            return overrides[key]
        return video_def.get(key, default)

    generate(
        script=video_def["script"],
        image_prompts=overrides.get("_prompts", video_def["prompts"]) if overrides else video_def["prompts"],
        output_path=output,
        voice=_ov("voice", "en-US-AndrewNeural"),
        gameplay_path=overrides.get("gameplay") if overrides and "gameplay" in overrides else video_def.get("gameplay"),
        font_size=_ov("font_size", 60),
        highlight_color=_ov("highlight_color", (255, 215, 0, 255)),
        caption_position=_ov("caption_position", "center"),
        entity=video_def["topic"],
        channel=ch["name"],
        experiment_id=experiment_id,
        reveal_word=video_def.get("reveal_word"),
        reveal_search=video_def.get("reveal_search"),
        reveal_image=video_def.get("reveal_image"),
        record=True,  # always register in curiosity graph
    )

    elapsed = time.time() - t0
    print(f"✅ Rendered in {elapsed:.0f}s: {output}")

    # Log to journal and cross-reference into curiosity graph
    journal_id = log_video(
        ch["name"],
        video_def["topic"],
        video_def["title"],
        "Rendered",
        notes=f"Batch generated. Voice: {video_def.get('voice', 'default')}. Time: {elapsed:.0f}s.",
    )
    if journal_id:
        link_to_curiosity(os.path.basename(output), journal_id)

    return output


def _apply_treatment(video_def: dict, design: dict, level: str) -> tuple:
    """Map an experiment design onto a video definition.

    Returns (overrides_dict, supported).  ``supported`` is False when the
    treatment variable needs a script-level change that v0 can't automate —
    in that case generation is tagged with the experiment id but unchanged.
    """
    var = design.get("treatment_var")
    is_control = level == "control"
    tag = "ctl" if is_control else "trt"
    overrides: dict = {"_tag": tag}

    if var == "voice":
        if is_control:
            overrides["voice"] = video_def.get("voice", "en-US-AndrewNeural")
        else:
            # Treatment: use a distinct voice from the control default
            default = video_def.get("voice", "en-US-AndrewNeural")
            alternatives = ["en-US-ChristopherNeural", "en-GB-RyanNeural", "en-US-AndrewNeural"]
            overrides["voice"] = next((v for v in alternatives if v != default), alternatives[0])
        return overrides, True
    if var == "caption_position":
        overrides["caption_position"] = "top" if not is_control else video_def.get("caption_position", "center")
        return overrides, True
    if var == "split_screen":
        if is_control:
            overrides["gameplay"] = video_def.get("gameplay")
        else:
            overrides["gameplay"] = None  # full-screen treatment
        return overrides, True
    if var == "font_size":
        overrides["font_size"] = (video_def.get("font_size", 60) + 12 if not is_control
                                  else video_def.get("font_size", 60))
        return overrides, True
    if var == "scene_count":
        prompts = video_def["prompts"]
        n = len(prompts)
        target = max(3, n - 1) if not is_control else n
        return {"_tag": tag, "_prompts": prompts[:target]}, True
    if var == "caption_hue":
        overrides["highlight_color"] = ((0, 200, 255, 255) if not is_control
                                        else video_def.get("highlight_color", (255, 215, 0, 255)))
        return overrides, True

    # Script-level variables (reveal/hook/pacing) — tag only in v0
    return overrides, False


def _load_design(design_id: int) -> dict:
    import sqlite3
    from curiosity.schema import DEFAULT_DB_PATH, loads
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM experiments WHERE id = ?", (design_id,)
    ).fetchone()
    conn.close()
    if not row:
        raise SystemExit(f"❌ Experiment design {design_id} not found in {DEFAULT_DB_PATH}")
    return dict(row)


def main():
    parser = argparse.ArgumentParser(description="Batch YouTube Shorts generator")
    parser.add_argument("--channel", "-c", choices=list(CHANNELS.keys()), help="Generate only one channel")
    parser.add_argument("--list", "-l", action="store_true", help="Just list what would be generated")
    parser.add_argument("--experiment", "-e", type=int, default=None,
                        help="Tag all generated videos with this experiment id")
    parser.add_argument("--from-design", "-d", type=int, default=None,
                        help="Run a one-variable experiment design (control + treatment variants)")
    args = parser.parse_args()

    # Initialize journal
    init_db()

    # Ensure channels exist
    for ch in CHANNELS.values():
        add_channel(ch["name"], ch["handle"], ch["niche"])

    # Determine which channels to process
    if args.channel:
        targets = {args.channel: CHANNELS[args.channel]}
    else:
        targets = CHANNELS

    design = None
    if args.from_design:
        design = _load_design(args.from_design)
        print(f"\n🧪 Running experiment design #{args.from_design}:")
        print(f"   Hypothesis: {design['hypothesis']}")
        print(f"   Treatment variable: {design['treatment_var']} "
              f"(levels: control / treatment)\n")

    total = 0
    for ch in targets.values():
        for vdef in ch["videos"]:
            if design:
                total += 2  # control + treatment
            else:
                total += 1
    done = 0
    skipped = 0
    failed = 0

    for key, ch in targets.items():
        print(f"\n📺 Channel: {ch['name']} ({len(ch['videos'])} videos)")
        print("-" * 40)

        for vdef in ch["videos"]:
            variants = []
            if design:
                ctl_overrides, ctl_supported = _apply_treatment(vdef, design, "control")
                trt_overrides, trt_supported = _apply_treatment(vdef, design, "treatment")
                if not ctl_supported:
                    print(f"   ⚠️  {design['treatment_var']} needs script-level work — "
                          f"tagging experiment only, no auto-variant.")
                variants = [
                    (args.from_design, ctl_overrides, "control"),
                    (args.from_design, trt_overrides, "treatment"),
                ]
            else:
                variants = [(args.experiment, None, "single")]

            for exp_id, overrides, _label in variants:
                try:
                    result = generate_video(key, vdef, dry_run=args.list,
                                            experiment_id=exp_id, overrides=overrides)
                    if result:
                        done += 1
                    elif args.list:
                        done += 1
                    else:
                        skipped += 1
                except Exception as e:
                    failed += 1
                    print(f"❌ FAILED: {vdef['output']} — {e}")

    print(f"\n{'='*60}")
    print(f"📊 BATCH COMPLETE: {done} done, {skipped} skipped, {failed} failed (of {total} total)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
