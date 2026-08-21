"""Prompt Translator (Decoupled Renderer).

Converts decoupled Scene Specifications into model-specific image prompts 
only when rendering is requested.
"""

from app.video.director.director_engine import SceneSpecification
from app.video.director.world_state import GlobalStyleBible

class PromptTranslator:
    """Translates Scene Specifications into model-specific text prompts."""

    def __init__(self, style_bible: GlobalStyleBible):
        self.style_bible = style_bible

    def translate_to_pollinations_prompt(self, spec: SceneSpecification) -> str:
        note = spec.director_note
        world = spec.world_state_inherited
        
        prompt = (
            f"Shot Type {note.narrative_purpose} ({note.camera_type}). "
            f"Subject: {note.primary_subject} ({spec.narrative_line}). "
            f"Framing: {note.framing}. Implied Motion: {note.implied_motion}. "
            f"Environment: {world['environment']}, {world['weather']}. "
            f"Lighting & Atmosphere: {world['lighting']}. "
            f"Safe Area: {note.caption_safe_area}. "
            f"Style: {self.style_bible.style_identity}, {self.style_bible.color_philosophy}, zero clutter, 9:16 vertical"
        )
        return prompt
