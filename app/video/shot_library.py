"""Cinematic Shot Library & Visual Intent Engine.

Transforms raw visual ideas into cinematic shot specifications based on 
cinematography principles (framing, camera angle, focal depth, lighting, and narrative intent).
"""

from typing import Dict, Any

# Reusable Cinematic Shot Archetypes
SHOT_ARCHETYPES = {
    "HOOK_SILHOUETTE": {
        "camera": "Low Dutch angle, 35mm wide lens",
        "framing": "Subject in shadow/silhouette filling 50% frame, clear negative space top-center",
        "lighting": "Backlit volumetric rim lighting, dramatic high-contrast golden atmosphere",
        "depth": "Deep depth of field, sharp foreground monstera/jungle foliage bokeh",
        "intent": "Create instant mystery and tension. Eye drawn to central glowing shadow within 0.2 seconds."
    },
    "EXTREME_MACRO": {
        "camera": "100mm macro prime lens, ultra-shallow depth of field f/1.8",
        "framing": "Extreme close-up of tactile detail (eyes, fur droplets, claw mechanism) occupying 80% frame",
        "lighting": "Soft directional studio lighting, glowing bioluminescence or sunlight sparkles",
        "depth": "Extremely shallow, silky smooth background blur (bokeh)",
        "intent": "Fascinate viewer with unexpected micro-textures and intricate living details."
    },
    "OVERHEAD_DRONE": {
        "camera": "High overhead top-down drone perspective (90 degree bird's eye view)",
        "framing": "Wide landscape establishing shot, subject centered surrounded by environmental patterns",
        "lighting": "Natural ambient daylight, soft shadows, pristine water or terrain textures",
        "depth": "Deep focus across entire frame",
        "intent": "Establish massive scale, environment context, and epic wildlife documentary feel."
    },
    "HERO_REVEAL": {
        "camera": "Low-angle heroic camera tilt looking up, 50mm portrait lens",
        "framing": "Hero animal standing proudly in center-lower third, 65% frame occupancy",
        "lighting": "Golden hour rim light tracing fur/skin edges, warm ambient backlight",
        "depth": "Medium depth of field, background environment softly blurred",
        "intent": "Deliver satisfying emotional payoff and iconic character showcase."
    },
    "COMPARISON_INFOGRAPHIC": {
        "camera": "Eye-level studio shot, clean architectural composition",
        "framing": "Side-by-side scale comparison with distinct negative space for text",
        "lighting": "High-key balanced softbox lighting, ultra-clean shadow definition",
        "depth": "Sharply rendered subjects on soft muted gradient background",
        "intent": "Instant cognitive clarity for size/power comparison without visual noise."
    },
    "HABITAT_STORY": {
        "camera": "Eye-level tracking shot, 50mm cinematic lens",
        "framing": "Subject interacting naturally with habitat, rule of thirds placement",
        "lighting": "Dappled sunlight filtering through natural canopy, atmospheric haze",
        "depth": "Natural background depth with secondary environmental elements (steam, leaves, water)",
        "intent": "Immersion in a believable living scene rather than a static portrait."
    }
}

def synthesize_cinematic_prompt(
    shot_type: str,
    subject_description: str,
    environment_details: str,
    style_guide: str = "Disney Nature documentary aesthetic, stylized 3D educational art"
) -> str:
    """Synthesizes a structured shot directive into a precise cinematic AI prompt."""
    shot = SHOT_ARCHETYPES.get(shot_type, SHOT_ARCHETYPES["HABITAT_STORY"])
    
    prompt = (
        f"Shot Type: {shot_type} ({shot['camera']}). "
        f"Subject: {subject_description}. "
        f"Composition & Framing: {shot['framing']}. "
        f"Environment & Story: {environment_details}. "
        f"Lighting & Depth: {shot['lighting']}, {shot['depth']}. "
        f"Style Directive: {style_guide}, zero clutter, high readability for vertical 9:16 format"
    )
    return prompt
