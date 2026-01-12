#!/usr/bin/env python3
"""
Pydantic Models for AI Debate Arena
"I'm learnding!" - Ralph Wiggum

Supports N debaters with custom positions on any topic.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum


class DebaterPosition(BaseModel):
    """A debater's position on the topic"""
    name: str = Field(..., description="Name of the position (e.g., 'Atheist', 'Pro', 'Skeptic')")
    stance: str = Field(..., description="Brief description of their stance on the topic")
    key_beliefs: List[str] = Field(default_factory=list, description="Core beliefs driving this position")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Theist",
                "stance": "Believes in the existence of God based on faith and reason",
                "key_beliefs": ["Divine revelation", "Cosmological argument", "Moral foundation"]
            }
        }


class Debater(BaseModel):
    """Configuration for a debate participant"""
    id: str = Field(..., description="Unique identifier for this debater")
    name: str = Field(..., description="Display name (e.g., 'Dr. Sarah Chen')")
    position: DebaterPosition = Field(..., description="Their position on the debate topic")
    personality: str = Field(
        default="analytical and articulate",
        description="Personality traits affecting debate style"
    )
    argument_style: str = Field(
        default="uses evidence and logical reasoning",
        description="How they construct arguments"
    )
    voice_id: int = Field(default=0, ge=0, le=3, description="Liquid Audio voice ID (0-3)")
    avatar_emoji: str = Field(default="🎓", description="Emoji avatar for UI")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "debater_theist",
                "name": "Rev. Michael Torres",
                "position": {
                    "name": "Theist",
                    "stance": "Argues for God's existence through faith and reason",
                    "key_beliefs": ["Divine revelation", "Fine-tuning argument"]
                },
                "personality": "warm but intellectually rigorous",
                "argument_style": "combines philosophical arguments with personal testimony",
                "voice_id": 0,
                "avatar_emoji": "⛪"
            }
        }


class DebateConfig(BaseModel):
    """Configuration for a multi-party debate"""
    topic: str = Field(..., description="The main debate topic/question")
    description: Optional[str] = Field(None, description="Additional context for the topic")
    debaters: List[Debater] = Field(..., min_length=2, max_length=6, description="2-6 debate participants")
    max_rounds: int = Field(default=3, ge=1, le=10, description="Number of full rounds")
    turn_time_seconds: int = Field(default=60, ge=15, le=180, description="Time per turn")
    allow_rebuttals: bool = Field(default=True, description="Allow direct rebuttals between speakers")
    moderator_strictness: Literal["relaxed", "moderate", "strict"] = Field(
        default="moderate",
        description="How strictly moderator enforces topic focus"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Does God exist?",
                "description": "A philosophical debate on the existence of a divine being",
                "debaters": [
                    {"id": "atheist", "name": "Dr. Alex Reed", "position": {"name": "Atheist", "stance": "No evidence for God"}},
                    {"id": "agnostic", "name": "Prof. Jordan Liu", "position": {"name": "Agnostic", "stance": "Cannot know either way"}},
                    {"id": "theist", "name": "Rev. Michael Torres", "position": {"name": "Theist", "stance": "God exists"}}
                ],
                "max_rounds": 3,
                "moderator_strictness": "moderate"
            }
        }


class DebateArgument(BaseModel):
    """Structured output from a debater's turn"""
    main_claim: str = Field(..., description="The primary argument or claim being made")
    supporting_points: List[str] = Field(
        default_factory=list,
        max_length=3,
        description="Evidence or reasoning supporting the claim"
    )
    rebuttal_to: Optional[str] = Field(
        None,
        description="If responding to another debater, their name"
    )
    rhetorical_strategy: str = Field(
        default="logical",
        description="The persuasion approach (logical, emotional, ethical, etc.)"
    )
    confidence_level: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="How confident in this argument (affects tone)"
    )

    def to_speech_text(self) -> str:
        """Convert to natural speech text"""
        text = self.main_claim
        if self.supporting_points:
            text += " " + " ".join(self.supporting_points[:2])
        return text


class ModeratorAction(BaseModel):
    """Action taken by the moderator"""
    action_type: Literal["introduce", "transition", "redirect", "summarize", "conclude"] = Field(
        ..., description="Type of moderator intervention"
    )
    message: str = Field(..., description="What the moderator says")
    addressed_to: Optional[str] = Field(None, description="Specific debater being addressed")
    off_topic_warning: bool = Field(default=False, description="Is this a warning about going off-topic?")
    topic_reminder: Optional[str] = Field(None, description="Reminder of what the topic is")


class TopicRelevanceCheck(BaseModel):
    """Result of checking if an argument is on-topic"""
    is_relevant: bool = Field(..., description="Whether the argument is on-topic")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="0-1 score of topic relevance")
    off_topic_elements: List[str] = Field(
        default_factory=list,
        description="Parts that went off-topic"
    )
    suggested_redirect: Optional[str] = Field(
        None,
        description="How to get back on topic"
    )


class DebateTurnResult(BaseModel):
    """Complete result of a debate turn"""
    debater_id: str
    debater_name: str
    position_name: str
    argument: DebateArgument
    timestamp: float
    round_number: int
    turn_in_round: int
    audio_generated: bool = False
    relevance_check: Optional[TopicRelevanceCheck] = None


class DebateState(BaseModel):
    """Current state of the debate"""
    debate_id: str
    config: DebateConfig
    current_round: int = 0
    current_speaker_index: int = 0
    phase: Literal["not_started", "introduction", "debate", "rebuttals", "closing", "finished"] = "not_started"
    turns: List[DebateTurnResult] = Field(default_factory=list)
    is_active: bool = False
    winner: Optional[str] = None  # Could be determined by votes/scoring


# Pre-built debate templates
DEBATE_TEMPLATES = {
    "god_existence": DebateConfig(
        topic="Does God exist?",
        description="A philosophical debate examining evidence and arguments for and against the existence of a divine being.",
        debaters=[
            Debater(
                id="atheist",
                name="Dr. Alex Reed",
                position=DebaterPosition(
                    name="Atheist",
                    stance="There is no credible evidence for God's existence",
                    key_beliefs=["Scientific materialism", "Burden of proof on believers", "Natural explanations suffice"]
                ),
                personality="rational, direct, scientifically-minded",
                argument_style="relies on empirical evidence and logical analysis",
                voice_id=0,
                avatar_emoji="🔬"
            ),
            Debater(
                id="agnostic",
                name="Prof. Jordan Liu",
                position=DebaterPosition(
                    name="Agnostic",
                    stance="The existence of God is unknown and perhaps unknowable",
                    key_beliefs=["Epistemological humility", "Limits of human knowledge", "Both sides have valid points"]
                ),
                personality="thoughtful, balanced, philosophically careful",
                argument_style="explores nuances and acknowledges uncertainty",
                voice_id=1,
                avatar_emoji="🤔"
            ),
            Debater(
                id="theist",
                name="Rev. Michael Torres",
                position=DebaterPosition(
                    name="Theist",
                    stance="God exists and can be known through reason and faith",
                    key_beliefs=["Cosmological argument", "Moral foundations require God", "Personal religious experience"]
                ),
                personality="warm, intellectually engaged, faith-grounded",
                argument_style="combines philosophical arguments with appeals to meaning and purpose",
                voice_id=2,
                avatar_emoji="⛪"
            ),
        ],
        max_rounds=3,
        moderator_strictness="moderate"
    ),

    "ai_consciousness": DebateConfig(
        topic="Can artificial intelligence ever be truly conscious?",
        description="Exploring whether machines can achieve genuine consciousness or merely simulate it.",
        debaters=[
            Debater(
                id="functionalist",
                name="Dr. Maya Patel",
                position=DebaterPosition(
                    name="Functionalist",
                    stance="Consciousness is about function, not substrate - AI can be conscious",
                    key_beliefs=["Mind as software", "Substrate independence", "Turing test validity"]
                ),
                personality="optimistic, technologically progressive",
                argument_style="draws on computational theory and thought experiments",
                voice_id=0,
                avatar_emoji="🤖"
            ),
            Debater(
                id="biological_naturalist",
                name="Prof. David Chen",
                position=DebaterPosition(
                    name="Biological Naturalist",
                    stance="Consciousness requires biological processes that AI cannot replicate",
                    key_beliefs=["Chinese Room argument", "Biological necessity", "Qualia are non-computational"]
                ),
                personality="skeptical, scientifically rigorous",
                argument_style="emphasizes biological and neurological evidence",
                voice_id=1,
                avatar_emoji="🧠"
            ),
            Debater(
                id="panpsychist",
                name="Dr. Elena Vasquez",
                position=DebaterPosition(
                    name="Panpsychist",
                    stance="Consciousness is fundamental to reality - AI may have some form of experience",
                    key_beliefs=["Consciousness is ubiquitous", "Degrees of experience", "Integration theory"]
                ),
                personality="philosophical, open-minded, speculative",
                argument_style="explores metaphysical possibilities",
                voice_id=2,
                avatar_emoji="✨"
            ),
        ],
        max_rounds=3,
        moderator_strictness="moderate"
    ),

    "free_will": DebateConfig(
        topic="Do humans have free will?",
        description="Examining whether our choices are truly free or determined by prior causes.",
        debaters=[
            Debater(
                id="libertarian",
                name="Prof. Sarah Mitchell",
                position=DebaterPosition(
                    name="Libertarian Free Will",
                    stance="Humans have genuine free will that is not determined by prior causes",
                    key_beliefs=["Agent causation", "Moral responsibility requires freedom", "Consciousness enables choice"]
                ),
                personality="passionate defender of human agency",
                argument_style="appeals to moral intuitions and phenomenal experience",
                voice_id=0,
                avatar_emoji="🦅"
            ),
            Debater(
                id="determinist",
                name="Dr. Marcus Webb",
                position=DebaterPosition(
                    name="Hard Determinist",
                    stance="All events, including human choices, are determined by prior causes",
                    key_beliefs=["Causal closure", "Neuroscience shows decisions are made unconsciously", "Illusion of choice"]
                ),
                personality="unflinching, scientifically grounded",
                argument_style="cites neuroscience and physics research",
                voice_id=1,
                avatar_emoji="⚙️"
            ),
            Debater(
                id="compatibilist",
                name="Dr. Rachel Kim",
                position=DebaterPosition(
                    name="Compatibilist",
                    stance="Free will and determinism are compatible - we are free when acting on our desires",
                    key_beliefs=["Freedom as acting on reasons", "Moral responsibility preserved", "Practical free will"]
                ),
                personality="pragmatic, bridge-building",
                argument_style="reconciles opposing views through careful definitions",
                voice_id=2,
                avatar_emoji="🌉"
            ),
        ],
        max_rounds=3,
        moderator_strictness="moderate"
    ),
}


def create_custom_debate(
    topic: str,
    positions: List[dict],
    max_rounds: int = 3,
    moderator_strictness: str = "moderate"
) -> DebateConfig:
    """
    Helper to create a custom debate configuration.

    Args:
        topic: The debate topic/question
        positions: List of dicts with keys: name, stance, debater_name (optional)
        max_rounds: Number of rounds
        moderator_strictness: "relaxed", "moderate", or "strict"

    Example:
        create_custom_debate(
            topic="Should we colonize Mars?",
            positions=[
                {"name": "Pro-Colonization", "stance": "Mars is humanity's future"},
                {"name": "Anti-Colonization", "stance": "We should fix Earth first"},
                {"name": "Cautious", "stance": "Only with proper preparation"}
            ]
        )
    """
    debaters = []
    voice_ids = [0, 1, 2, 3]
    avatars = ["🎓", "📚", "🔬", "💡", "🌟", "🎯"]

    for i, pos in enumerate(positions):
        debater = Debater(
            id=f"debater_{i}",
            name=pos.get("debater_name", f"Speaker {i + 1}"),
            position=DebaterPosition(
                name=pos["name"],
                stance=pos["stance"],
                key_beliefs=pos.get("key_beliefs", [])
            ),
            personality=pos.get("personality", "articulate and thoughtful"),
            argument_style=pos.get("argument_style", "balanced reasoning"),
            voice_id=voice_ids[i % len(voice_ids)],
            avatar_emoji=pos.get("avatar", avatars[i % len(avatars)])
        )
        debaters.append(debater)

    return DebateConfig(
        topic=topic,
        debaters=debaters,
        max_rounds=max_rounds,
        moderator_strictness=moderator_strictness
    )