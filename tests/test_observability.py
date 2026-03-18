#!/usr/bin/env python3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from debate_engine import DebateRole
from observability import normalize_attributes, turn_attributes


class TestObservabilityHelpers:
    def test_normalize_attributes_serializes_supported_values(self):
        attributes = normalize_attributes({
            "role": DebateRole.PRO,
            "count": 2,
            "enabled": True,
            "items": ["a", "b"],
            "meta": {"phase": "opening"},
            "skip": None,
        })

        assert attributes["role"] == "pro"
        assert attributes["count"] == 2
        assert attributes["enabled"] is True
        assert attributes["items"] == ["a", "b"]
        assert attributes["meta"] == '{"phase": "opening"}'
        assert "skip" not in attributes

    def test_turn_attributes_builds_consistent_metric_shape(self):
        attributes = turn_attributes(
            debate_id="debate_123",
            topic="Should AI replace teachers?",
            round_number=2,
            phase="debate",
            speaker_name="Dr. Maya Patel",
            position_name="Functionalist",
            has_audio=True,
            relevance_score=0.92,
            is_relevant=True,
            confidence_level=0.81,
        )

        assert attributes["debate.id"] == "debate_123"
        assert attributes["debate.topic"] == "Should AI replace teachers?"
        assert attributes["round.number"] == 2
        assert attributes["debate.phase"] == "debate"
        assert attributes["speaker.name"] == "Dr. Maya Patel"
        assert attributes["speaker.position"] == "Functionalist"
        assert attributes["audio.generated"] is True
        assert attributes["relevance.score"] == 0.92
        assert attributes["relevance.on_topic"] is True
        assert attributes["argument.confidence"] == 0.81
