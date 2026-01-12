#!/usr/bin/env python3
"""
Unit Tests for Debate Engine
"I'm learnding!" - Ralph Wiggum
"""

import pytest
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from debate_engine import (
    DebateEngine,
    DebateRole,
    DebatePhase,
    Agent,
    DebateTurn
)


class TestRalphWiggumDebateEngine:
    """
    Test suite for DebateEngine
    "Hi, Super Nintendo Chalmers!" - Ralph
    """

    def test_engine_initialization_unpossible(self):
        """Test that engine initializes correctly - That's unpossible!"""
        topic = "Should we eat paste in school?"
        engine = DebateEngine(topic, max_rounds=3)

        assert engine.topic == topic
        assert engine.max_rounds == 3
        assert engine.current_round == 0
        assert engine.current_phase == DebatePhase.INTRODUCTION
        assert engine.debate_id.startswith("debate_")
        assert len(engine.history) == 0
        assert engine.is_active == False

    def test_agents_are_learnding(self):
        """Test that agents are properly initialized - I'm learnding!"""
        engine = DebateEngine("Is the cat's breath smelling like cat food?")

        assert "pro" in engine.agents
        assert "con" in engine.agents
        assert "moderator" in engine.agents

        # Check PRO agent
        pro = engine.agents["pro"]
        assert pro.role == DebateRole.PRO
        assert pro.voice_id == 0
        assert pro.name == "Dr. Advocate"

        # Check CON agent
        con = engine.agents["con"]
        assert con.role == DebateRole.CON
        assert con.voice_id == 1
        assert pro.name != con.name  # Different agents

    def test_my_cats_breath_smells_like_cat_food(self):
        """Test agent data class - My cat's breath smells like cat food!"""
        agent = Agent(
            id="ralph_wiggum",
            name="Ralph",
            role=DebateRole.PRO,
            voice_id=3,
            personality="confused but enthusiastic",
            argument_style="random observations"
        )

        assert agent.id == "ralph_wiggum"
        assert agent.name == "Ralph"
        assert agent.role == DebateRole.PRO
        assert agent.personality == "confused but enthusiastic"

    def test_debate_turn_creation_i_bent_my_wookie(self):
        """Test debate turn creation - I bent my Wookie!"""
        turn = DebateTurn(
            agent_id="agent_pro",
            agent_name="Dr. Advocate",
            role=DebateRole.PRO,
            statement="The evidence clearly shows...",
            audio_data=None,
            timestamp=1234567890.0,
            phase=DebatePhase.MAIN_ARGUMENTS,
            is_rebuttal=False,
            duration=2.5
        )

        assert turn.agent_name == "Dr. Advocate"
        assert turn.statement == "The evidence clearly shows..."
        assert turn.is_rebuttal == False
        assert turn.duration == 2.5

    def test_debate_phases_im_in_danger(self):
        """Test all debate phases exist - I'm in danger!"""
        phases = [
            DebatePhase.INTRODUCTION,
            DebatePhase.OPENING_STATEMENTS,
            DebatePhase.MAIN_ARGUMENTS,
            DebatePhase.REBUTTALS,
            DebatePhase.CLOSING_STATEMENTS,
            DebatePhase.CONCLUSION
        ]

        for phase in phases:
            assert phase.value is not None

    def test_listener_management_go_banana(self):
        """Test adding and removing listeners - Go banana!"""
        engine = DebateEngine("Are grapes fun to play with?")

        async def dummy_listener(data):
            pass

        # Add listener
        engine.add_listener(dummy_listener)
        assert len(engine.listeners) == 1

        # Remove listener
        engine.remove_listener(dummy_listener)
        assert len(engine.listeners) == 0

    def test_transcript_generation_me_fail_english(self):
        """Test transcript generation - Me fail English? That's unpossible!"""
        engine = DebateEngine("Should homework be made of chocolate?")

        # Add some mock history
        engine.history.append(DebateTurn(
            agent_id="agent_pro",
            agent_name="Dr. Advocate",
            role=DebateRole.PRO,
            statement="Chocolate homework would increase student engagement!",
            audio_data=None,
            timestamp=1000.0,
            phase=DebatePhase.OPENING_STATEMENTS
        ))

        transcript = engine.get_transcript()

        assert "DEBATE TRANSCRIPT" in transcript
        assert "Should homework be made of chocolate?" in transcript
        assert "Dr. Advocate" in transcript
        assert "Chocolate homework" in transcript

    def test_statistics_i_choo_choo_choose_you(self):
        """Test statistics generation - I choo-choo-choose you!"""
        engine = DebateEngine("Should trains give valentines?", max_rounds=2)

        # Add mock turns
        engine.history.append(DebateTurn(
            agent_id="agent_pro",
            agent_name="Dr. Advocate",
            role=DebateRole.PRO,
            statement="Pro argument",
            audio_data=None,
            timestamp=1000.0,
            phase=DebatePhase.MAIN_ARGUMENTS,
            duration=1.5
        ))
        engine.history.append(DebateTurn(
            agent_id="agent_con",
            agent_name="Prof. Challenger",
            role=DebateRole.CON,
            statement="Con argument",
            audio_data=None,
            timestamp=1001.0,
            phase=DebatePhase.MAIN_ARGUMENTS,
            duration=2.0
        ))

        stats = engine.get_statistics()

        assert stats["debate_id"] == engine.debate_id
        assert stats["topic"] == "Should trains give valentines?"
        assert stats["total_turns"] == 2
        assert stats["pro_turns"] == 1
        assert stats["con_turns"] == 1
        assert stats["total_duration"] == 3.5

    def test_debate_roles_when_i_grow_up(self):
        """Test debate roles - When I grow up I want to be a principal or a caterpillar!"""
        assert DebateRole.PRO.value == "pro"
        assert DebateRole.CON.value == "con"
        assert DebateRole.MODERATOR.value == "moderator"


class TestRalphAsyncDebateFunctions:
    """
    Async tests for debate engine
    "The doctor said I wouldn't have so many nose bleeds if I kept my finger outta there."
    """

    @pytest.mark.asyncio
    async def test_create_turn_tastes_like_burning(self):
        """Test async turn creation - It tastes like burning!"""
        engine = DebateEngine("Is fire hot?")
        agent = engine.agents["pro"]

        turn = await engine.create_turn(
            agent=agent,
            statement="Fire is indeed very hot.",
            phase=DebatePhase.MAIN_ARGUMENTS,
            is_rebuttal=False
        )

        assert turn.agent_name == agent.name
        assert turn.statement == "Fire is indeed very hot."
        assert len(engine.history) == 1

    @pytest.mark.asyncio
    async def test_listener_notification_sleep_thats_where_im_a_viking(self):
        """Test listener notifications - Sleep! That's where I'm a Viking!"""
        engine = DebateEngine("Are dreams real?")

        received_events = []

        async def capture_listener(data):
            received_events.append(data)

        engine.add_listener(capture_listener)

        # Create a turn which should notify listeners
        agent = engine.agents["pro"]
        await engine.create_turn(
            agent=agent,
            statement="Dreams are the best part of sleeping!",
            phase=DebatePhase.OPENING_STATEMENTS
        )

        # Wait for async notification
        await asyncio.sleep(0.1)

        assert len(received_events) == 1
        assert received_events[0]["event"] == "turn_completed"


# Ralph Wiggum Quotes for test output
RALPH_QUOTES = [
    "I'm learnding!",
    "Me fail English? That's unpossible!",
    "My cat's breath smells like cat food.",
    "I bent my Wookie.",
    "Hi, Super Nintendo Chalmers!",
    "I choo-choo-choose you!",
    "It tastes like burning!",
    "Sleep! That's where I'm a Viking!",
    "Go banana!",
    "When I grow up I want to be a principal or a caterpillar!",
    "That's where I saw the leprechaun. He tells me to burn things.",
    "Mrs. Krabappel and Principal Skinner were in the closet making babies!",
]


if __name__ == "__main__":
    import random
    print(f"\n🎭 Running tests... {random.choice(RALPH_QUOTES)}\n")
    pytest.main([__file__, "-v", "--tb=short"])