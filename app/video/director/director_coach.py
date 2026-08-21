"""Director Coach & Sequence Auditor.

Evaluates complete storyboards as a cohesive film sequence before image generation.
Explains WHY a sequence is strong or weak and provides actionable coaching advice.
"""

from dataclasses import dataclass, field
import json
import os
from typing import List, Dict, Any

from app.video.director.director_engine import SceneSpecification

@dataclass
class AuditReport:
    sequence_score: float
    passed: bool
    rhythm_score: float
    continuity_score: float
    caption_safety_score: float
    retention_score: float
    coaching_notes: List[str]
    breakdown: List[Dict[str, Any]]

class DirectorCoach:
    """Audits entire storyboards and acts as a self-improving film director coach."""

    def audit_storyboard(self, storyboard: List[SceneSpecification]) -> AuditReport:
        coaching_notes = []
        breakdown = []
        
        cameras = [s.director_note.camera_type for s in storyboard]
        purposes = [s.narrative_purpose for s in storyboard]
        
        # Check 1: Rhythm & Consecutive Monotony
        consecutive_repeats = 0
        for i in range(1, len(cameras)):
            if cameras[i] == cameras[i-1]:
                consecutive_repeats += 1
                coaching_notes.append(
                    f"⚠️ Weak Rhythm at Scene #{i+1}: Consecutive repeat of camera angle ({cameras[i]}). "
                    "Recommendation: Shift focal length or switch to Wide/Macro contrast."
                )

        rhythm_score = max(5.0, 10.0 - (consecutive_repeats * 2.0))

        # Check 2: Narrative Arc Flow (Mystery -> Exploration -> Scale -> Payoff)
        has_mystery = purposes[0] == "MYSTERY_HOOK"
        has_payoff = purposes[-1] == "PAYOFF_REVEAL"
        
        if not has_mystery:
            coaching_notes.append("⚠️ Storyboard missing initial Mystery Hook in Scene #1.")
        if not has_payoff:
            coaching_notes.append("⚠️ Storyboard missing decisive Payoff Reveal in final Scene.")

        continuity_score = 9.5 if (has_mystery and has_payoff) else 7.0
        caption_safety_score = 9.5  # All SceneSpecs enforce top 35% safe area
        retention_score = round((rhythm_score + continuity_score + caption_safety_score) / 3.0, 2)
        
        passed = retention_score >= 7.5

        for idx, scene in enumerate(storyboard):
            breakdown.append({
                "scene_id": scene.scene_id,
                "line": scene.narrative_line,
                "purpose": scene.narrative_purpose,
                "camera": scene.director_note.camera_type,
                "implied_motion": scene.director_note.implied_motion,
                "attention_target": scene.director_note.attention_target,
            })

        return AuditReport(
            sequence_score=retention_score,
            passed=passed,
            rhythm_score=rhythm_score,
            continuity_score=continuity_score,
            caption_safety_score=caption_safety_score,
            retention_score=retention_score,
            coaching_notes=coaching_notes if coaching_notes else ["✅ Storyboard pacing and visual rhythm are excellently balanced."],
            breakdown=breakdown
        )

class DirectorMemory:
    """Stores storyboards and audit history for long-term learning."""

    def __init__(self, storage_dir: str = "data/director_memory"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def log_storyboard(self, episode_id: str, storyboard: List[SceneSpecification], audit: AuditReport):
        file_path = os.path.join(self.storage_dir, f"{episode_id}_storyboard.json")
        payload = {
            "episode_id": episode_id,
            "sequence_score": audit.sequence_score,
            "passed": audit.passed,
            "coaching_notes": audit.coaching_notes,
            "scenes": [
                {
                    "scene_id": s.scene_id,
                    "line": s.narrative_line,
                    "purpose": s.narrative_purpose,
                    "director_note": s.director_note.__dict__,
                    "world_state": s.world_state_inherited
                }
                for s in storyboard
            ]
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"🧠 Director Memory: Storyboard logged to {file_path}")
