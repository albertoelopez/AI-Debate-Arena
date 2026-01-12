#!/usr/bin/env python3
"""
Pytest Configuration
"What's a battle?" - Ralph Wiggum
"""

import pytest
import sys
import asyncio
from pathlib import Path

# Add src to path for all tests
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def pytest_configure(config):
    """Configure pytest with custom markers - I'm learnding!"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests - Sleep! That's where I'm a Viking!"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def ralph_quote():
    """Get a random Ralph Wiggum quote - My cat's breath smells like cat food!"""
    import random
    quotes = [
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
        "I'm Idaho!",
        "I dressed myself!",
        "Even my boogers are delicious!",
        "The doctor said I wouldn't have so many nose bleeds if I kept my finger outta there.",
        "I found a moon rock in my nose!",
        "Slow down, Bart! My legs don't know how to be as long as yours!",
        "My parents won't let me use scissors!",
        "Miss Hoover, I glued my head to my shoulder!",
        "Look big Daddy, it's Regular Daddy!",
        "I'm a pop sensation!",
        "Daddy, I'm scared. Too scared to wet my pants!",
        "That's my sandbox! I'm not allowed to go in the deep end.",
        "This is my swing! You stole my swing!",
        "The strong must protect the sweet.",
        "What's a battle?",
        "I eated the purple berries!",
        "They taste like... burning.",
    ]
    return random.choice(quotes)


def pytest_report_header(config):
    """Add Ralph Wiggum header to test output"""
    return [
        "",
        "🎭 AI Debate Arena Test Suite",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        '"I\'m learnding!" - Ralph Wiggum',
        "",
    ]


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Add Ralph Wiggum footer to test output"""
    import random
    quotes = [
        "That's unpossible!",
        "I bent my Wookie testing this!",
        "It tastes like burning!",
        "Go banana!",
        "I'm a unitard!",
    ]

    if exitstatus == 0:
        terminalreporter.write_line("")
        terminalreporter.write_line("✅ All tests passed! \"I'm learnding!\" - Ralph", green=True)
    else:
        terminalreporter.write_line("")
        terminalreporter.write_line(f"❌ Some tests failed! \"{random.choice(quotes)}\" - Ralph", red=True)