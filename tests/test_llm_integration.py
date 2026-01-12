#!/usr/bin/env python3
"""
Unit Tests for LLM Integration
"The doctor said I wouldn't have so many nose bleeds if I kept my finger outta there." - Ralph
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llm_integration import LLMArgumentGenerator, DebateLLMBridge


class TestRalphWiggumLLMGenerator:
    """
    Test suite for LLMArgumentGenerator
    "What's a battle?" - Ralph Wiggum
    """

    def test_provider_selection_my_worm_went_in_my_mouth(self):
        """Test provider selection logic - My worm went in my mouth and then I ate it!"""
        # Clear environment for testing
        with patch.dict(os.environ, {
            'GROQ_API_KEY': '',
            'GOOGLE_API_KEY': '',
            'OLLAMA_URL': 'http://localhost:11434'
        }, clear=True):
            generator = LLMArgumentGenerator()
            assert generator.provider == "ollama"

    def test_groq_priority_thats_my_sandbox(self):
        """Test Groq is prioritized when available - That's my sandbox! I'm not allowed to go in the deep end."""
        with patch.dict(os.environ, {
            'GROQ_API_KEY': 'test_groq_key',
            'GOOGLE_API_KEY': 'test_google_key',
        }):
            generator = LLMArgumentGenerator()
            assert generator.provider == "groq"

    def test_google_fallback_leprechaun(self):
        """Test Google fallback - He tells me to burn things."""
        with patch.dict(os.environ, {
            'GROQ_API_KEY': '',
            'GOOGLE_API_KEY': 'test_google_key',
        }, clear=True):
            generator = LLMArgumentGenerator()
            assert generator.provider == "google"

    def test_ollama_model_selection_im_a_unitard(self):
        """Test Ollama model selection - I'm a unitard!"""
        generator = LLMArgumentGenerator()
        best_model = generator._select_best_ollama_model()

        # Should pick gemma2 as it's the best available
        assert best_model == "gemma2:latest"

    def test_fallback_response_opening_my_nose_is_bleeding(self):
        """Test fallback opening statement - My nose makes its own bubblegum!"""
        generator = LLMArgumentGenerator()

        pro_response = generator._fallback_response(
            "opening statement for pro position"
        )
        con_response = generator._fallback_response(
            "opening statement for con position"
        )

        assert "support" in pro_response.lower() or "proposition" in pro_response.lower()

    def test_fallback_response_rebuttal_daddy_says(self):
        """Test fallback rebuttal - Daddy says I'm this close to going to sleep forever!"""
        generator = LLMArgumentGenerator()

        rebuttal = generator._fallback_response("rebuttal to opponent")

        assert "opponent" in rebuttal.lower() or "evidence" in rebuttal.lower()

    def test_fallback_response_closing_the_pointy_kitty(self):
        """Test fallback closing statement - The pointy kitty took it!"""
        generator = LLMArgumentGenerator()

        pro_closing = generator._fallback_response(
            "closing statement for pro position"
        )
        con_closing = generator._fallback_response(
            "closing statement for con position"
        )

        assert len(pro_closing) > 20  # Not empty
        assert len(con_closing) > 20

    def test_context_formatting_i_eated_the_purple_berries(self):
        """Test context formatting - I eated the purple berries!"""
        generator = LLMArgumentGenerator()

        turns = [
            {"agent_name": "Ralph", "statement": "These taste like grandma!"},
            {"agent_name": "Lisa", "statement": "Ralph, those are poison!"},
        ]

        formatted = generator._format_context(turns)

        assert "Ralph: These taste like grandma!" in formatted
        assert "Lisa: Ralph, those are poison!" in formatted

    def test_empty_context_formatting_my_knob_tastes_funny(self):
        """Test empty context - My knob tastes funny!"""
        generator = LLMArgumentGenerator()

        formatted = generator._format_context([])

        assert formatted == "No prior context."


class TestRalphAsyncLLMFunctions:
    """
    Async tests for LLM generation
    "Eww, Daddy! This tastes like Grandma!" - Ralph Wiggum
    """

    @pytest.mark.asyncio
    async def test_generate_opening_statement_fun_toys(self):
        """Test opening statement generation - Fun toys are fun!"""
        with patch.dict(os.environ, {'GROQ_API_KEY': '', 'GOOGLE_API_KEY': ''}, clear=True):
            generator = LLMArgumentGenerator()

            # This will use fallback since no API keys
            statement = await generator.generate_opening_statement(
                agent_name="Ralph",
                agent_personality="enthusiastic",
                agent_style="simple observations",
                position="pro",
                topic="Should school have more nap time?"
            )

            assert len(statement) > 10  # Got a response
            assert isinstance(statement, str)

    @pytest.mark.asyncio
    async def test_generate_argument_burning(self):
        """Test argument generation - It tastes like burning!"""
        with patch.dict(os.environ, {'GROQ_API_KEY': '', 'GOOGLE_API_KEY': ''}, clear=True):
            generator = LLMArgumentGenerator()

            argument = await generator.generate_argument(
                agent_name="Ralph",
                agent_personality="innocent",
                agent_style="honest observations",
                position="con",
                topic="Is fire dangerous?",
                round_num=1,
                context=[]
            )

            assert len(argument) > 10
            assert isinstance(argument, str)

    @pytest.mark.asyncio
    async def test_generate_rebuttal_banana(self):
        """Test rebuttal generation - Go banana!"""
        with patch.dict(os.environ, {'GROQ_API_KEY': '', 'GOOGLE_API_KEY': ''}, clear=True):
            generator = LLMArgumentGenerator()

            rebuttal = await generator.generate_rebuttal(
                agent_name="Ralph",
                agent_personality="confused",
                agent_style="tangential",
                position="pro",
                topic="Are bananas the best fruit?",
                opponent_argument="Apples are clearly superior to bananas."
            )

            assert len(rebuttal) > 10

    @pytest.mark.asyncio
    async def test_generate_closing_principal_caterpillar(self):
        """Test closing generation - When I grow up I want to be a principal or a caterpillar!"""
        with patch.dict(os.environ, {'GROQ_API_KEY': '', 'GOOGLE_API_KEY': ''}, clear=True):
            generator = LLMArgumentGenerator()

            closing = await generator.generate_closing_statement(
                agent_name="Ralph",
                agent_personality="dreamy",
                position="pro",
                topic="Should we have career day more often?",
                key_points=["Careers are fun", "Caterpillars are cool"]
            )

            assert len(closing) > 10


class TestDebateLLMBridge:
    """
    Test the bridge between LLM and Debate Engine
    "Um, Miss Hoover? There's a dog in the vent." - Ralph
    """

    @pytest.mark.asyncio
    async def test_bridge_enhances_engine_super_nintendo(self):
        """Test bridge enhances debate engine - Hi, Super Nintendo Chalmers!"""
        from debate_engine import DebateEngine

        engine = DebateEngine("Should video games be educational?")
        bridge = DebateLLMBridge()

        await bridge.enhance_debate_engine(engine)

        # Check that methods were replaced
        assert engine._generate_opening_statement is not None
        assert engine._generate_argument is not None
        assert engine._generate_rebuttal is not None
        assert engine._generate_closing_statement is not None


class TestOllamaIntegration:
    """
    Test Ollama-specific functionality
    "I found a moon rock in my nose!" - Ralph
    """

    @pytest.mark.asyncio
    async def test_ollama_availability_check_moon_rock(self):
        """Test Ollama availability check - That's where I found the moon rock!"""
        generator = LLMArgumentGenerator()

        # This should work if Ollama is running
        available = await generator._check_ollama_availability()

        # Just verify it returns a boolean without error
        assert isinstance(available, bool)

    @pytest.mark.asyncio
    async def test_ollama_generation_with_timeout_nose_goblins(self):
        """Test Ollama generation with proper timeout - I found nose goblins!"""
        with patch.dict(os.environ, {'GROQ_API_KEY': '', 'GOOGLE_API_KEY': ''}, clear=True):
            generator = LLMArgumentGenerator()

            # Should either work or fallback gracefully
            response = await generator._generate_ollama(
                "You are Ralph Wiggum. Say something about nose goblins."
            )

            assert isinstance(response, str)
            assert len(response) > 0


# More Ralph quotes for entertainment
RALPH_TEST_QUOTES = [
    "I'm Idaho!",
    "I dressed myself!",
    "Even my boogers are delicious!",
    "I like men now!",
    "This is my swing! You stole my swing!",
    "The children are right to laugh at you, Ralph.",
    "I'm a pop sensation!",
    "Slow down, Bart! My legs don't know how to be as long as yours!",
]

if __name__ == "__main__":
    import random
    print(f"\n🧪 Testing LLM Integration... {random.choice(RALPH_TEST_QUOTES)}\n")
    pytest.main([__file__, "-v", "--tb=short"])