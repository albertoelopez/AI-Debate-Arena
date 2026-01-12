#!/usr/bin/env python3
"""
AI Debate Arena Server v2 - Multi-Debater Edition
"Hi, Super Nintendo Chalmers!" - Ralph Wiggum

Supports N debaters with custom positions via REST API and WebSocket.
"""

import asyncio
import json
import base64
import os
from pathlib import Path
from typing import Dict, List, Optional
from aiohttp import web, WSMsgType
import weakref
import logging

from models import DebateConfig, Debater, DebaterPosition, DEBATE_TEMPLATES, create_custom_debate
from debate_engine_v2 import MultiDebateEngine

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
PUBLIC_DIR = PROJECT_ROOT / "public"


class StreamManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.connections: Dict[str, weakref.WeakSet] = {}

    def add(self, debate_id: str, ws):
        if debate_id not in self.connections:
            self.connections[debate_id] = weakref.WeakSet()
        self.connections[debate_id].add(ws)

    def remove(self, debate_id: str, ws):
        if debate_id in self.connections:
            self.connections[debate_id].discard(ws)

    async def broadcast(self, debate_id: str, data: dict):
        if debate_id not in self.connections:
            return

        message = json.dumps(data)
        dead = []

        for ws in self.connections[debate_id]:
            try:
                await ws.send_str(message)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.remove(debate_id, ws)


class DebateServerV2:
    """Multi-debater debate server with PydanticAI integration"""

    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.streams = StreamManager()
        self.debates: Dict[str, MultiDebateEngine] = {}

        self._setup_routes()

    def _setup_routes(self):
        # WebSocket
        self.app.router.add_get('/ws', self._handle_websocket)

        # API Routes
        self.app.router.add_get('/health', self._health)
        self.app.router.add_get('/api/templates', self._list_templates)
        self.app.router.add_get('/api/templates/{name}', self._get_template)
        self.app.router.add_post('/api/debate/create', self._create_debate)
        self.app.router.add_post('/api/debate/create-custom', self._create_custom_debate)
        self.app.router.add_get('/api/debate/{debate_id}', self._get_debate)
        self.app.router.add_post('/api/debate/{debate_id}/start', self._start_debate)
        self.app.router.add_delete('/api/debate/{debate_id}', self._stop_debate)
        self.app.router.add_get('/api/debate/{debate_id}/transcript', self._get_transcript)

        # Static files
        self.app.router.add_get('/', self._serve_index)
        self.app.router.add_get('/{filename}', self._serve_static)

    async def _handle_websocket(self, request):
        """Handle WebSocket connections"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        debate_id = None

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)

                        if data.get("type") == "join":
                            debate_id = data.get("debate_id")
                            if debate_id:
                                self.streams.add(debate_id, ws)
                                await ws.send_str(json.dumps({
                                    "type": "joined",
                                    "debate_id": debate_id
                                }))

                        elif data.get("type") == "ping":
                            await ws.send_str(json.dumps({"type": "pong"}))

                    except json.JSONDecodeError:
                        pass

                elif msg.type == WSMsgType.ERROR:
                    break

        finally:
            if debate_id:
                self.streams.remove(debate_id, ws)

        return ws

    async def _health(self, request):
        return web.json_response({
            "status": "healthy",
            "version": "2.0",
            "active_debates": len(self.debates),
            "available_templates": list(DEBATE_TEMPLATES.keys())
        })

    async def _list_templates(self, request):
        """List available debate templates"""
        templates = []
        for name, config in DEBATE_TEMPLATES.items():
            templates.append({
                "name": name,
                "topic": config.topic,
                "description": config.description,
                "num_debaters": len(config.debaters),
                "debaters": [
                    {"name": d.name, "position": d.position.name}
                    for d in config.debaters
                ]
            })
        return web.json_response({"templates": templates})

    async def _get_template(self, request):
        """Get a specific template configuration"""
        name = request.match_info['name']
        if name not in DEBATE_TEMPLATES:
            return web.json_response({"error": "Template not found"}, status=404)

        config = DEBATE_TEMPLATES[name]
        return web.json_response({
            "name": name,
            "topic": config.topic,
            "description": config.description,
            "max_rounds": config.max_rounds,
            "debaters": [
                {
                    "id": d.id,
                    "name": d.name,
                    "position": d.position.name,
                    "stance": d.position.stance,
                    "avatar": d.avatar_emoji
                }
                for d in config.debaters
            ]
        })

    async def _create_debate(self, request):
        """Create a debate from a template"""
        try:
            data = await request.json()
            template_name = data.get("template", "god_existence")
            max_rounds = data.get("max_rounds")

            engine = MultiDebateEngine.from_template(template_name)

            if max_rounds:
                engine.config.max_rounds = max_rounds

            # Set up event broadcasting
            async def broadcast_event(event):
                await self.streams.broadcast(engine.debate_id, event)

            engine.add_listener(broadcast_event)

            self.debates[engine.debate_id] = engine

            return web.json_response({
                "debate_id": engine.debate_id,
                "topic": engine.config.topic,
                "debaters": [
                    {
                        "id": d.id,
                        "name": d.name,
                        "position": d.position.name,
                        "avatar": d.avatar_emoji
                    }
                    for d in engine.config.debaters
                ],
                "max_rounds": engine.config.max_rounds,
                "status": "created"
            })

        except Exception as e:
            logger.error(f"Create debate failed: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def _create_custom_debate(self, request):
        """Create a custom debate with user-defined positions"""
        try:
            data = await request.json()

            topic = data.get("topic")
            if not topic:
                return web.json_response({"error": "Topic is required"}, status=400)

            positions = data.get("positions", [])
            if len(positions) < 2:
                return web.json_response({"error": "At least 2 positions required"}, status=400)

            max_rounds = data.get("max_rounds", 3)
            strictness = data.get("moderator_strictness", "moderate")

            # Build debater configurations (only include non-None values)
            debater_configs = []
            for pos in positions:
                config = {
                    "name": pos.get("name"),
                    "stance": pos.get("stance", f"Argues the {pos.get('name')} position"),
                }
                # Only add optional fields if they have values
                if pos.get("debater_name"):
                    config["debater_name"] = pos["debater_name"]
                if pos.get("personality"):
                    config["personality"] = pos["personality"]
                if pos.get("argument_style"):
                    config["argument_style"] = pos["argument_style"]
                if pos.get("avatar"):
                    config["avatar"] = pos["avatar"]
                if pos.get("key_beliefs"):
                    config["key_beliefs"] = pos["key_beliefs"]
                debater_configs.append(config)

            engine = MultiDebateEngine.create_custom(
                topic=topic,
                positions=debater_configs,
                max_rounds=max_rounds,
                moderator_strictness=strictness
            )

            # Set up event broadcasting
            async def broadcast_event(event):
                await self.streams.broadcast(engine.debate_id, event)

            engine.add_listener(broadcast_event)

            self.debates[engine.debate_id] = engine

            return web.json_response({
                "debate_id": engine.debate_id,
                "topic": engine.config.topic,
                "debaters": [
                    {
                        "id": d.id,
                        "name": d.name,
                        "position": d.position.name,
                        "stance": d.position.stance,
                        "avatar": d.avatar_emoji
                    }
                    for d in engine.config.debaters
                ],
                "max_rounds": engine.config.max_rounds,
                "status": "created"
            })

        except Exception as e:
            logger.error(f"Create custom debate failed: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def _get_debate(self, request):
        """Get debate status"""
        debate_id = request.match_info['debate_id']

        if debate_id not in self.debates:
            return web.json_response({"error": "Debate not found"}, status=404)

        engine = self.debates[debate_id]

        return web.json_response({
            "debate_id": debate_id,
            "topic": engine.config.topic,
            "phase": engine.state.phase,
            "current_round": engine.state.current_round,
            "total_rounds": engine.config.max_rounds,
            "is_active": engine.state.is_active,
            "total_turns": len(engine.state.turns),
            "debaters": [
                {
                    "id": d.id,
                    "name": d.name,
                    "position": d.position.name,
                    "avatar": d.avatar_emoji
                }
                for d in engine.config.debaters
            ]
        })

    async def _start_debate(self, request):
        """Start a debate"""
        debate_id = request.match_info['debate_id']

        if debate_id not in self.debates:
            return web.json_response({"error": "Debate not found"}, status=404)

        engine = self.debates[debate_id]

        if engine.state.is_active:
            return web.json_response({"error": "Debate already running"}, status=400)

        # Start in background
        asyncio.create_task(engine.run_debate())

        return web.json_response({
            "debate_id": debate_id,
            "status": "starting"
        })

    async def _stop_debate(self, request):
        """Stop and remove a debate"""
        debate_id = request.match_info['debate_id']

        if debate_id not in self.debates:
            return web.json_response({"error": "Debate not found"}, status=404)

        engine = self.debates[debate_id]
        engine.state.is_active = False

        # Notify clients
        await self.streams.broadcast(debate_id, {"event": "debate_stopped"})

        # Clean up after delay
        async def cleanup():
            await asyncio.sleep(60)
            if debate_id in self.debates:
                del self.debates[debate_id]

        asyncio.create_task(cleanup())

        return web.json_response({"message": "Debate stopped"})

    async def _get_transcript(self, request):
        """Get debate transcript"""
        debate_id = request.match_info['debate_id']

        if debate_id not in self.debates:
            return web.json_response({"error": "Debate not found"}, status=404)

        engine = self.debates[debate_id]

        return web.json_response({
            "debate_id": debate_id,
            "transcript": engine.get_transcript(),
            "statistics": engine.get_statistics()
        })

    async def _serve_index(self, request):
        index_path = PUBLIC_DIR / "index_v2.html"
        if not index_path.exists():
            index_path = PUBLIC_DIR / "index.html"
        if index_path.exists():
            return web.FileResponse(index_path)
        return web.Response(text="Index not found", status=404)

    async def _serve_static(self, request):
        filename = request.match_info['filename']
        file_path = PUBLIC_DIR / filename

        try:
            file_path = file_path.resolve()
            if not str(file_path).startswith(str(PUBLIC_DIR.resolve())):
                return web.Response(text="Forbidden", status=403)
        except Exception:
            return web.Response(text="Invalid path", status=400)

        if file_path.exists() and file_path.is_file():
            return web.FileResponse(file_path)
        return web.Response(text="Not found", status=404)

    async def start(self):
        """Start the server"""
        runner = web.AppRunner(self.app)
        await runner.setup()

        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        logger.info(f"🎭 Debate Arena v2 running at http://{self.host}:{self.port}")
        return runner


async def main():
    logging.basicConfig(level=logging.INFO)

    host = os.getenv('HOST', 'localhost')
    port = int(os.getenv('PORT', 8080))

    server = DebateServerV2(host, port)
    runner = await server.start()

    logger.info("💡 Open your browser to start multi-party debates!")
    logger.info("📚 Available templates: god_existence, ai_consciousness, free_will")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())