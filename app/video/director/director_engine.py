"""Director Engine & Creative Producer."""

from dataclasses import dataclass, field
import json
import re
from typing import List, Dict, Any, Optional

from app.video.director.world_state import GlobalStyleBible, EpisodeWorld, SceneGraph

@dataclass
class DirectorNote:
    scene_index: int
    beat_index: int
    narrative_purpose: str
    emotion_target: str
    attention_target: str
    primary_subject: str
    secondary_subject: str
    implied_motion: str
    camera_type: str
    focal_length: str
    framing: str
    lighting: str
    caption_safe_area: str
    belief_reference: str
    expected_retention_effect: str

@dataclass
class SceneSpecification:
    scene_id: str
    narrative_line: str
    narrative_purpose: str
    emotion_target: str
    director_note: DirectorNote
    scene_graph: Dict[str, Any]
    world_state_inherited: Dict[str, Any]

class CreativeProducer:
    def evaluate_project(self, topic: str, script: str) -> Dict[str, Any]:
        has_hook = "?" in script[:100] or any(w in script[:100].lower() for w in ["guess", "can you", "what if"])
        word_count = len(script.split())
        ideal_duration = 35 <= (word_count / 2.5) <= 60
        
        score = 8.5 if (has_hook and ideal_duration) else 6.5
        approved = score >= 7.0
        
        return {
            "approved": approved,
            "producer_score": score,
            "topic": topic,
            "estimated_duration_sec": round(word_count / 2.5, 1),
            "has_strong_hook": has_hook,
            "reasoning": "Strong curiosity hook & ideal video length" if approved else "Script needs stronger initial hook"
        }

class DirectorPlanner:
    def __init__(self, style_bible: Optional[GlobalStyleBible] = None):
        self.style_bible = style_bible or GlobalStyleBible()
        self.history_shots: List[str] = []

    def dissect_into_semantic_beats(self, sentence: str) -> List[str]:
        parts = [p.strip() for p in re.split(r'[,;]|\band\b|\beven\b', sentence) if len(p.strip()) > 5]
        if len(parts) > 1 and len(sentence.split()) > 12:
            return parts[:3]
        return [sentence.strip()]

    def plan_scene_specification(
        self,
        scene_idx: int,
        beat_idx: int,
        beat_line: str,
        world: EpisodeWorld,
        total_scenes: int = 5
    ) -> SceneSpecification:
        text = beat_line.lower()
        is_reveal = ("it's the" in text or "reveal" in text or scene_idx >= total_scenes - 1)
        
        # Enforce Mystery Silhouettes for all clue scenes BEFORE the countdown reveal
        if not is_reveal:
            primary_subject_prompt = f"mysterious unidentified creature shadow silhouette (do not show clear face)"
            if scene_idx == 1:
                purpose = "MYSTERY_HOOK"
                emotion = "CURIOSITY"
                camera = "Low Dutch Angle (-15 deg), 35mm wide"
                shot_type = "SILHOUETTE_ENTRANCE"
                motion = "Thermal steam drifting left to right, subtle monstera vegetation sway"
                attention = "Central mysterious glowing shadow silhouette"
            elif any(w in text for w in ["pound", "largest", "decibel", "sun", "140"]):
                purpose = "SCALE_COMPARISON"
                emotion = "WONDER"
                camera = "Eye-level silhouette infographic layout, 50mm lens"
                shot_type = "SCALE_COMPARISON"
                motion = "Slow camera pan showing massive shadow outline vs reference object"
                attention = "Shadow outline scale height comparison"
            elif any(w in text for w in ["macro", "snout", "droplet", "claw", "bath", "lemon"]):
                purpose = "TACTILE_DISCOVERY"
                emotion = "FASCINATION"
                camera = "100mm Macro prime lens, extreme close-up detail, shallow DOF f/1.8"
                shot_type = "MACRO_DETAIL"
                motion = "Water droplet splash on unidentified creature paw/claw"
                attention = "Micro texture of mysterious claw or fur droplet in shadow"
            else:
                purpose = "HABITAT_IMMERSION"
                emotion = "MYSTERY"
                camera = "Hidden telephoto tracking lens behind leaves, 135mm lens"
                shot_type = "HIDDEN_THROUGH_LEAVES"
                motion = "Leaves gently swaying, creature partially obscured in 80% shadow"
                attention = "Unidentified creature blending into mysterious habitat shadow"
        else:
            # THE PAYOFF REVEAL SHOT
            primary_subject_prompt = world.hero_character.name
            purpose = "PAYOFF_REVEAL"
            emotion = "JOY_AWE"
            camera = "Low angle hero tilt looking upward (+10 deg), 70mm telephoto"
            shot_type = "HERO_REVEAL"
            motion = "Golden light rays illuminating full clear view of hero animal, water ripples expanding"
            attention = "Full heroic reveal of smiling animal"

        sg = SceneGraph()
        sg.add_entity(primary_subject_prompt, "CHARACTER", {"features": world.hero_character.primary_features})
        sg.add_entity("Environment", "ENVIRONMENT", {"anchor": world.environment_anchor, "lighting": world.lighting_anchor})
        if world.recurring_motifs:
            sg.add_entity(world.recurring_motifs[0], "PROP", {"type": "recurring_motif"})
            sg.add_relation(primary_subject_prompt, "INTERACTING_WITH", world.recurring_motifs[0])
        sg.add_relation(primary_subject_prompt, "LOCATED_IN", "Environment")

        note = DirectorNote(
            scene_index=scene_idx,
            beat_index=beat_idx,
            narrative_purpose=purpose,
            emotion_target=emotion,
            attention_target=attention,
            primary_subject=primary_subject_prompt,
            secondary_subject=world.recurring_motifs[0] if world.recurring_motifs else "Environment",
            implied_motion=motion,
            camera_type=camera,
            focal_length=camera.split(",")[-1].strip(),
            framing="Hero in lower 65% frame, upper 35% negative space for captions",
            lighting="Dark mystery backlight with shadow contrast" if not is_reveal else world.lighting_anchor,
            caption_safe_area="Top 35% clean atmosphere gradient",
            belief_reference=f"BELIEF_{shot_type}",
            expected_retention_effect="HIGH"
        )

        return SceneSpecification(
            scene_id=f"scene_{scene_idx}_beat_{beat_idx}",
            narrative_line=beat_line,
            narrative_purpose=purpose,
            emotion_target=emotion,
            director_note=note,
            scene_graph=sg.to_dict(),
            world_state_inherited={
                "environment": world.environment_anchor,
                "lighting": "Dark mystery backlight" if not is_reveal else world.lighting_anchor,
                "weather": world.weather_atmosphere,
                "hero_color": world.hero_character.color_palette
            }
        )
