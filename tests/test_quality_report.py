#!/usr/bin/env python3

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from debate_engine_v2 import MultiDebateEngine
from models import (
    DebateArgument,
    DebateTurnResult,
    TopicRelevanceCheck,
    GenerationMetadata,
    DEBATE_TEMPLATES,
)


class TestQualityReport:
    def test_quality_report_summarizes_turn_metrics(self):
        engine = MultiDebateEngine(DEBATE_TEMPLATES["ai_consciousness"].model_copy(deep=True))

        first = engine.config.debaters[0]
        second = engine.config.debaters[1]
        engine.state.turns = [
            DebateTurnResult(
                debater_id=first.id,
                debater_name=first.name,
                position_name=first.position.name,
                argument=DebateArgument(
                    main_claim="From the Functionalist perspective, AI can be conscious.",
                    supporting_points=["Function matters more than substrate."],
                    confidence_level=0.7,
                ),
                timestamp=time.time(),
                round_number=1,
                turn_in_round=0,
                audio_generated=True,
                generation_metadata=GenerationMetadata(
                    provider="groq",
                    model="llama-3.1-8b-instant",
                    used_fallback=True,
                    repeated_claim=False,
                ),
                relevance_check=TopicRelevanceCheck(
                    is_relevant=True,
                    relevance_score=0.9,
                    off_topic_elements=[],
                    suggested_redirect=None,
                ),
            ),
            DebateTurnResult(
                debater_id=second.id,
                debater_name=second.name,
                position_name=second.position.name,
                argument=DebateArgument(
                    main_claim="Biological consciousness depends on living processes.",
                    supporting_points=["Brains are not interchangeable with software."],
                    confidence_level=0.8,
                ),
                timestamp=time.time(),
                round_number=1,
                turn_in_round=1,
                audio_generated=False,
                generation_metadata=GenerationMetadata(
                    provider="groq",
                    model="llama-3.1-8b-instant",
                    used_fallback=False,
                    repeated_claim=False,
                ),
                relevance_check=TopicRelevanceCheck(
                    is_relevant=False,
                    relevance_score=0.4,
                    off_topic_elements=["Shifted into general AI policy."],
                    suggested_redirect="Return to consciousness criteria.",
                ),
            ),
            DebateTurnResult(
                debater_id=second.id,
                debater_name=second.name,
                position_name=second.position.name,
                argument=DebateArgument(
                    main_claim="Biological consciousness depends on living processes.",
                    supporting_points=["The same claim is repeated here."],
                    confidence_level=0.6,
                ),
                timestamp=time.time(),
                round_number=2,
                turn_in_round=1,
                audio_generated=False,
                generation_metadata=GenerationMetadata(
                    provider="groq",
                    model="llama-3.1-8b-instant",
                    used_fallback=False,
                    repeated_claim=True,
                ),
                relevance_check=TopicRelevanceCheck(
                    is_relevant=True,
                    relevance_score=0.6,
                    off_topic_elements=[],
                    suggested_redirect=None,
                ),
            ),
        ]

        report = engine.get_quality_report()

        assert report["summary"]["total_turns"] == 3
        assert report["summary"]["average_relevance_score"] == 0.633
        assert report["summary"]["off_topic_turns"] == 1
        assert report["summary"]["low_relevance_turns"] == 1
        assert report["summary"]["audio_success_rate"] == 0.333
        assert report["summary"]["average_confidence"] == 0.7
        assert report["summary"]["repeat_claim_ratio"] == 0.333
        assert report["summary"]["fallback_turns"] == 1

        rows = {row["debater_id"]: row for row in report["speaker_breakdown"]}
        assert rows[first.id]["turn_count"] == 1
        assert rows[first.id]["audio_success_rate"] == 1.0
        assert rows[first.id]["fallback_turns"] == 1
        assert rows[second.id]["turn_count"] == 2
        assert rows[second.id]["off_topic_turns"] == 1
        assert rows[second.id]["audio_success_rate"] == 0.0
        assert rows[second.id]["repeated_claim_turns"] == 1
