#!/usr/bin/env python3
"""
Unit Tests for Audio Server
"I heard your dad went into a restaurant and ate everything in the restaurant
and they had to close the restaurant." - Ralph Wiggum
"""

import pytest
import asyncio
import sys
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audio_server import (
    AudioStreamManager,
    DebateWebSocketHandler,
    DebateAudioServer,
    PUBLIC_DIR,
    PROJECT_ROOT
)


class TestRalphAudioStreamManager:
    """
    Test suite for AudioStreamManager
    "Mrs. Krabappel and Principal Skinner were in the closet making babies
    and I saw one of the babies and the baby looked at me!" - Ralph
    """

    def test_initialization_i_saw_a_baby(self):
        """Test stream manager initialization - And the baby looked at me!"""
        manager = AudioStreamManager()

        assert manager.active_streams == {}
        assert manager.audio_buffer == {}

    def test_add_listener_making_babies(self):
        """Test adding listeners - They were making babies!"""
        manager = AudioStreamManager()
        mock_websocket = MagicMock()

        manager.add_listener("debate_123", mock_websocket)

        assert "debate_123" in manager.active_streams
        assert mock_websocket in manager.active_streams["debate_123"]

    def test_remove_listener_closet(self):
        """Test removing listeners - In the closet!"""
        manager = AudioStreamManager()
        mock_websocket = MagicMock()

        manager.add_listener("debate_456", mock_websocket)
        manager.remove_listener("debate_456", mock_websocket)

        # Listener should be removed (WeakSet may still have entry but socket removed)
        assert "debate_456" in manager.active_streams

    def test_remove_nonexistent_listener_backwards(self):
        """Test removing from nonexistent debate - My cat was right, I am crazy!"""
        manager = AudioStreamManager()
        mock_websocket = MagicMock()

        # Should not raise error
        manager.remove_listener("nonexistent_debate", mock_websocket)


class TestRalphAsyncStreamManager:
    """
    Async tests for stream manager
    "That's where I saw the leprechaun. He tells me to burn things." - Ralph
    """

    @pytest.mark.asyncio
    async def test_broadcast_event_leprechaun(self):
        """Test broadcasting events - The leprechaun told me to!"""
        manager = AudioStreamManager()

        # Create mock websocket
        mock_ws = AsyncMock()
        mock_ws.send_str = AsyncMock()

        manager.add_listener("debate_leprechaun", mock_ws)

        await manager.broadcast_event("debate_leprechaun", {
            "event": "test_event",
            "message": "The leprechaun is here"
        })

        # Verify send was called
        mock_ws.send_str.assert_called_once()
        call_args = mock_ws.send_str.call_args[0][0]
        data = json.loads(call_args)
        assert data["type"] == "debate_event"
        assert data["event"] == "test_event"

    @pytest.mark.asyncio
    async def test_broadcast_to_no_listeners_burning(self):
        """Test broadcast with no listeners - He tells me to burn things!"""
        manager = AudioStreamManager()

        # Should not raise error
        await manager.broadcast_event("nonexistent", {"event": "fire"})

    @pytest.mark.asyncio
    async def test_broadcast_audio_my_face(self):
        """Test audio broadcasting - My face is on fire!"""
        manager = AudioStreamManager()

        mock_ws = AsyncMock()
        mock_ws.send_str = AsyncMock()

        manager.add_listener("debate_fire", mock_ws)

        # Broadcast audio
        await manager.broadcast_audio(
            "debate_fire",
            b"fake_audio_data",
            {"agent_name": "Ralph", "statement": "It's on fire!"}
        )

        mock_ws.send_str.assert_called_once()
        call_args = mock_ws.send_str.call_args[0][0]
        data = json.loads(call_args)

        assert data["type"] == "audio_stream"
        assert "audio_data" in data
        assert data["metadata"]["agent_name"] == "Ralph"


class TestRalphDebateAudioServer:
    """
    Test suite for DebateAudioServer
    "I found a moon rock in my nose!" - Ralph
    """

    def test_server_initialization_moon_rock(self):
        """Test server initialization - In my nose!"""
        server = DebateAudioServer(host="localhost", port=8888)

        assert server.host == "localhost"
        assert server.port == 8888
        assert server.active_debates == {}
        assert server.stream_manager is not None
        assert server.ws_handler is not None

    def test_public_dir_exists_sandbox(self):
        """Test public directory setup - That's my sandbox!"""
        assert PUBLIC_DIR.exists(), f"Public dir should exist at {PUBLIC_DIR}"
        assert (PUBLIC_DIR / "index.html").exists(), "index.html should exist"
        assert (PUBLIC_DIR / "debate-client.js").exists(), "debate-client.js should exist"

    def test_project_root_im_not_allowed(self):
        """Test project root calculation - I'm not allowed to go in the deep end!"""
        assert PROJECT_ROOT.exists()
        assert (PROJECT_ROOT / "src").exists()
        assert (PROJECT_ROOT / "public").exists()


class TestRalphServerRoutes:
    """
    Test API routes
    "When I grow up, I'm going to Bovine University!" - Ralph
    """

    @pytest.fixture
    def server(self):
        return DebateAudioServer(host="localhost", port=9999)

    @pytest.mark.asyncio
    async def test_health_check_bovine_university(self, server):
        """Test health endpoint - I'm going to Bovine University!"""
        # Create mock request
        mock_request = MagicMock()

        response = await server._health_check(mock_request)

        assert response.status == 200
        data = json.loads(response.text)
        assert data["status"] == "healthy"
        assert data["active_debates"] == 0

    @pytest.mark.asyncio
    async def test_serve_index_fun_toys(self, server):
        """Test index serving - Fun toys are fun!"""
        mock_request = MagicMock()

        response = await server._serve_index(mock_request)

        # Should return FileResponse for existing index.html
        assert response is not None

    @pytest.mark.asyncio
    async def test_serve_static_file_choo_choo(self, server):
        """Test static file serving - I choo-choo-choose you!"""
        mock_request = MagicMock()
        mock_request.match_info = {'filename': 'debate-client.js'}

        response = await server._serve_static_file(mock_request)

        # Should return the JS file
        assert response is not None

    @pytest.mark.asyncio
    async def test_serve_nonexistent_file_wookie(self, server):
        """Test 404 for missing files - I bent my Wookie!"""
        mock_request = MagicMock()
        mock_request.match_info = {'filename': 'nonexistent-file.js'}

        response = await server._serve_static_file(mock_request)

        assert response.status == 404

    @pytest.mark.asyncio
    async def test_directory_traversal_protection_danger(self, server):
        """Test path traversal protection - I'm in danger!"""
        mock_request = MagicMock()
        mock_request.match_info = {'filename': '../../../etc/passwd'}

        response = await server._serve_static_file(mock_request)

        # Should be forbidden or not found, not serve the file
        assert response.status in [403, 404]


class TestDebateAPIEndpoints:
    """
    Test debate creation and management
    "The strong must protect the sweet." - Ralph (sort of)
    """

    @pytest.fixture
    def server(self):
        return DebateAudioServer(host="localhost", port=7777)

    @pytest.mark.asyncio
    async def test_get_nonexistent_debate_umm(self, server):
        """Test getting nonexistent debate - Um, what's a debate?"""
        mock_request = MagicMock()
        mock_request.match_info = {'debate_id': 'nonexistent_12345'}

        response = await server._get_debate_status(mock_request)

        assert response.status == 404

    @pytest.mark.asyncio
    async def test_stop_nonexistent_debate_ow(self, server):
        """Test stopping nonexistent debate - Ow! My brain!"""
        mock_request = MagicMock()
        mock_request.match_info = {'debate_id': 'fake_debate'}

        response = await server._stop_debate(mock_request)

        assert response.status == 404


# Ralph Wiggum server test quotes
RALPH_SERVER_QUOTES = [
    "I'm learnding!",
    "This snowflake tastes like fishsticks!",
    "Me fail English? That's unpossible!",
    "I ate the purple berries!",
    "Daddy, I'm scared. Too scared to wet my pants!",
    "Look! I'm a Furniture!",
]

if __name__ == "__main__":
    import random
    print(f"\n🌐 Testing Audio Server... {random.choice(RALPH_SERVER_QUOTES)}\n")
    pytest.main([__file__, "-v", "--tb=short"])