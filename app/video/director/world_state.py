"""Hierarchical World State & Scene Graph System."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class GlobalStyleBible:
    channel_name: str = "WhoDatCritter"
    style_identity: str = "DisneyNature stylized animated documentary aesthetic"
    color_philosophy: str = "Rich natural organic tones, warm golden ambient sunlight, zero plastic glare"
    render_quality: str = "Unreal Engine 5 cinematic render, soft subsurface scattering, clean readable composition"
    max_visual_clutter: float = 0.2

@dataclass
class CharacterSheet:
    name: str
    species: str
    primary_features: str
    color_palette: str
    personality_vibe: str

@dataclass
class EpisodeWorld:
    episode_id: str
    topic_name: str
    environment_anchor: str
    lighting_anchor: str
    weather_atmosphere: str
    hero_character: CharacterSheet
    supporting_characters: List[str] = field(default_factory=list)
    recurring_motifs: List[str] = field(default_factory=list)

@dataclass
class SceneGraphNode:
    entity_name: str
    entity_type: str
    attributes: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SceneGraphEdge:
    subject: str
    relationship: str
    target: str

class SceneGraph:
    def __init__(self):
        self.nodes: Dict[str, SceneGraphNode] = {}
        self.edges: List[SceneGraphEdge] = []

    def add_entity(self, name: str, entity_type: str, attributes: Optional[Dict[str, Any]] = None):
        self.nodes[name] = SceneGraphNode(
            entity_name=name,
            entity_type=entity_type,
            attributes=attributes or {}
        )

    def add_relation(self, subject: str, relationship: str, target: str):
        self.edges.append(SceneGraphEdge(subject=subject, relationship=relationship, target=target))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": [
                {"name": n.entity_name, "type": n.entity_type, "attributes": n.attributes}
                for n in self.nodes.values()
            ],
            "relationships": [
                {"subject": e.subject, "relation": e.relationship, "target": e.target}
                for e in self.edges
            ]
        }
