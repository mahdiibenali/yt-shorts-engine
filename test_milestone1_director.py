import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import json
import urllib.parse
import httpx

from app.video.director.world_state import GlobalStyleBible, EpisodeWorld, CharacterSheet
from app.video.director.director_engine import CreativeProducer, DirectorPlanner
from app.video.director.director_coach import DirectorCoach, DirectorMemory
from app.video.director.prompt_translator import PromptTranslator

def render_sample_frame(prompt: str, output_path: str, width: int = 1080, height: int = 960):
    print(f"🎬 Rendering Sample Frame from Approved Spec: {output_path}...")
    models = ["flux", "turbo"]
    
    for model in models:
        try:
            encoded = urllib.parse.quote(prompt[:350])
            url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&model={model}&nologo=true"
            resp = httpx.get(url, timeout=60.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200 and len(resp.content) > 5000:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                print(f"✅ Saved frame: {output_path} ({model})")
                return output_path
        except Exception as e:
            print(f"⚠️ Model {model} failed: {e}")
            
    print(f"❌ Failed rendering: {output_path}")
    return None

if __name__ == "__main__":
    os.makedirs("milestone1_output", exist_ok=True)
    
    print("\n========================================================")
    print("🎬 MILESTONE 1: AI FILM DIRECTOR PIPELINE")
    print("========================================================\n")
    
    # Step 1: Creative Producer Gatekeeper Evaluation
    producer = CreativeProducer()
    topic = "Capybara"
    script = (
        "Can you guess which famous animal is the most relaxed creature in the entire universe? "
        "This giant fuzzy friend is so friendly that birds, monkeys, and even alligators hang out with it! "
        "It is the largest rodent on planet Earth, weighing up to 140 pounds! "
        "It loves taking warm baths with lemons floating on its head! "
        "It is the CAPYBARA! The ultimate icon of chill vibes!"
    )
    
    eval_result = producer.evaluate_project(topic, script)
    print(f"📋 Producer Decision: Approved={eval_result['approved']} (Score: {eval_result['producer_score']}/10)")
    print(f"   Reasoning: {eval_result['reasoning']}\n")
    
    # Step 2: Initialize Episode World & Scene Graph Context
    style_bible = GlobalStyleBible()
    hero_char = CharacterSheet(
        name="Capybara",
        species="Hydrochoerus hydrochaeris",
        primary_features="Chubby body, soft brown fur, calm dark eyes, relaxed expression",
        color_palette="Warm basalt brown, soft amber",
        personality_vibe="Zen master, unbothered"
    )
    
    world = EpisodeWorld(
        episode_id="ep_capybara_001",
        topic_name="Capybara",
        environment_anchor="Volcanic jungle thermal river hot spring with mossy basalt rocks",
        lighting_anchor="Golden hour backlight (4:30 PM) with soft emerald shadow fill",
        weather_atmosphere="Thermal mist rising softly, gentle floating golden pollen",
        hero_character=hero_char,
        recurring_motifs=["Yellow yuzu citrus", "Golden finch bird"]
    )
    
    # Step 3: Director Planning & Storyboard Generation (Decoupled Planning)
    planner = DirectorPlanner(style_bible=style_bible)
    script_lines = [s.strip() for s in script.split(".") if s.strip()]
    
    storyboard = []
    scene_counter = 1
    
    for line in script_lines:
        beats = planner.dissect_into_semantic_beats(line)
        for b_idx, beat in enumerate(beats):
            spec = planner.plan_scene_specification(
                scene_idx=scene_counter,
                beat_idx=b_idx,
                beat_line=beat,
                world=world
            )
            storyboard.append(spec)
        scene_counter += 1

    # Step 4: Director Coach Storyboard Audit (Before Rendering)
    coach = DirectorCoach()
    audit = coach.audit_storyboard(storyboard)
    
    print("========================================================")
    print(f"🧠 STORYBOARD AUDIT REPORT (Score: {audit.sequence_score}/10 | Passed: {audit.passed})")
    print("========================================================")
    print(f"   Rhythm Score: {audit.rhythm_score}/10 | Continuity: {audit.continuity_score}/10 | Safety: {audit.caption_safety_score}/10")
    print("   Coaching Notes:")
    for note in audit.coaching_notes:
        print(f"     • {note}")
    print("========================================================\n")
    
    # Step 5: Save Storyboard to Director Memory
    memory = DirectorMemory()
    memory.log_storyboard(world.episode_id, storyboard, audit)
    
    # Step 6: Render 2 Sample Shots using Prompt Translator (Decoupled Renderer)
    translator = PromptTranslator(style_bible=style_bible)
    
    prompt_shot1 = translator.translate_to_pollinations_prompt(storyboard[0])
    prompt_shot2 = translator.translate_to_pollinations_prompt(storyboard[1])
    
    print("\n--------------------------------------------------------")
    print(f"Shot #1 Plan: {storyboard[0].director_note.narrative_purpose} | Purpose: {storyboard[0].director_note.attention_target}")
    print(f"Translated Prompt: {prompt_shot1[:120]}...")
    render_sample_frame(prompt_shot1, "milestone1_output/shot1_mystery.png")
    
    print("\n--------------------------------------------------------")
    print(f"Shot #2 Plan: {storyboard[1].director_note.narrative_purpose} | Purpose: {storyboard[1].director_note.attention_target}")
    print(f"Translated Prompt: {prompt_shot2[:120]}...")
    render_sample_frame(prompt_shot2, "milestone1_output/shot2_habitat.png")
