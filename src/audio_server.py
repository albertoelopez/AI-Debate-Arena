#!/usr/bin/env python3

import asyncio
import json
import base64
import io
import os
from pathlib import Path
from typing import Dict, List, Optional, Callable
import aiohttp
from aiohttp import web, WSMsgType
import weakref
import logging

logger = logging.getLogger(__name__)

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
PUBLIC_DIR = PROJECT_ROOT / "public"

class AudioStreamManager:
    def __init__(self):
        self.active_streams: Dict[str, weakref.WeakSet] = {}
        self.audio_buffer: Dict[str, List[bytes]] = {}
        
    def add_listener(self, debate_id: str, websocket) -> None:
        if debate_id not in self.active_streams:
            self.active_streams[debate_id] = weakref.WeakSet()
        self.active_streams[debate_id].add(websocket)
        logger.info(f"Added listener for debate {debate_id}")
    
    def remove_listener(self, debate_id: str, websocket) -> None:
        if debate_id in self.active_streams:
            try:
                self.active_streams[debate_id].discard(websocket)
            except KeyError:
                pass
    
    async def broadcast_audio(self, debate_id: str, audio_data: bytes, metadata: Dict) -> None:
        if debate_id not in self.active_streams:
            return
            
        # Convert to base64 for JSON transport
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        message = {
            "type": "audio_stream",
            "debate_id": debate_id,
            "audio_data": audio_b64,
            "metadata": metadata
        }
        
        # Broadcast to all listeners
        disconnected = []
        for websocket in self.active_streams[debate_id]:
            try:
                await websocket.send_str(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send audio to client: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected websockets
        for ws in disconnected:
            self.remove_listener(debate_id, ws)
    
    async def broadcast_event(self, debate_id: str, event_data: Dict) -> None:
        if debate_id not in self.active_streams:
            return
            
        message = {
            "type": "debate_event",
            "debate_id": debate_id,
            **event_data
        }
        
        disconnected = []
        for websocket in self.active_streams[debate_id]:
            try:
                await websocket.send_str(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send event to client: {e}")
                disconnected.append(websocket)
        
        for ws in disconnected:
            self.remove_listener(debate_id, ws)

class DebateWebSocketHandler:
    def __init__(self, stream_manager: AudioStreamManager):
        self.stream_manager = stream_manager
        
    async def handle_websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        debate_id = None
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_message(ws, data)
                        
                        if data.get("type") == "join_debate":
                            debate_id = data.get("debate_id")
                            if debate_id:
                                self.stream_manager.add_listener(debate_id, ws)
                                await ws.send_str(json.dumps({
                                    "type": "joined",
                                    "debate_id": debate_id,
                                    "status": "connected"
                                }))
                                
                    except json.JSONDecodeError:
                        await ws.send_str(json.dumps({
                            "type": "error",
                            "message": "Invalid JSON"
                        }))
                        
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
        finally:
            if debate_id:
                self.stream_manager.remove_listener(debate_id, ws)
                
        return ws
    
    async def _handle_message(self, websocket, data: Dict):
        msg_type = data.get("type")
        
        if msg_type == "ping":
            await websocket.send_str(json.dumps({"type": "pong"}))
        elif msg_type == "get_status":
            debate_id = data.get("debate_id")
            await websocket.send_str(json.dumps({
                "type": "status",
                "debate_id": debate_id,
                "connected": True
            }))

class DebateAudioServer:
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.stream_manager = AudioStreamManager()
        self.ws_handler = DebateWebSocketHandler(self.stream_manager)
        self.active_debates: Dict[str, Dict] = {}
        
        self._setup_routes()
    
    def _setup_routes(self):
        # API routes
        self.app.router.add_get('/ws', self.ws_handler.handle_websocket)
        self.app.router.add_get('/health', self._health_check)
        self.app.router.add_post('/api/debate/create', self._create_debate)
        self.app.router.add_get('/api/debate/{debate_id}/status', self._get_debate_status)
        self.app.router.add_post('/api/debate/{debate_id}/start', self._start_debate)
        self.app.router.add_delete('/api/debate/{debate_id}', self._stop_debate)

        # Serve index.html at root
        self.app.router.add_get('/', self._serve_index)

        # Serve static files for the web interface (use absolute path)
        self.app.router.add_static('/static', path=str(PUBLIC_DIR), name='static')

        # Fallback for other static files at root level
        self.app.router.add_get('/{filename}', self._serve_static_file)

    async def _serve_index(self, request):
        """Serve the main index.html file"""
        index_path = PUBLIC_DIR / "index.html"
        if index_path.exists():
            return web.FileResponse(index_path)
        return web.Response(text="Index not found", status=404)

    async def _serve_static_file(self, request):
        """Serve static files from public directory"""
        filename = request.match_info['filename']
        file_path = PUBLIC_DIR / filename

        # Security: prevent directory traversal
        try:
            file_path = file_path.resolve()
            if not str(file_path).startswith(str(PUBLIC_DIR.resolve())):
                return web.Response(text="Forbidden", status=403)
        except Exception:
            return web.Response(text="Invalid path", status=400)

        if file_path.exists() and file_path.is_file():
            return web.FileResponse(file_path)
        return web.Response(text="File not found", status=404)
    
    async def _health_check(self, request):
        return web.json_response({"status": "healthy", "active_debates": len(self.active_debates)})
    
    async def _create_debate(self, request):
        try:
            data = await request.json()
            topic = data.get("topic", "A complex issue")
            max_rounds = data.get("max_rounds", 3)
            
            from debate_engine import DebateEngine
            from llm_integration import DebateLLMBridge
            
            # Create debate engine
            engine = DebateEngine(topic, max_rounds)
            llm_bridge = DebateLLMBridge()
            await llm_bridge.enhance_debate_engine(engine)
            
            # Add audio streaming listener
            async def audio_listener(event_data):
                await self.stream_manager.broadcast_event(engine.debate_id, event_data)
                
                # If turn has audio, broadcast it
                if "turn" in event_data and "audio_data" in event_data["turn"]:
                    turn = event_data["turn"]
                    if turn.get("has_audio") and hasattr(engine, 'history'):
                        # Find the actual turn with audio data
                        for hist_turn in reversed(engine.history):
                            if (hist_turn.agent_name == turn["agent_name"] and 
                                hist_turn.timestamp == turn["timestamp"]):
                                if hist_turn.audio_data:
                                    await self.stream_manager.broadcast_audio(
                                        engine.debate_id,
                                        hist_turn.audio_data,
                                        {
                                            "agent_name": turn["agent_name"],
                                            "role": turn["role"],
                                            "statement": turn["statement"],
                                            "timestamp": turn["timestamp"]
                                        }
                                    )
                                break
            
            engine.add_listener(audio_listener)
            
            self.active_debates[engine.debate_id] = {
                "engine": engine,
                "topic": topic,
                "max_rounds": max_rounds,
                "status": "created",
                "created_at": asyncio.get_event_loop().time()
            }
            
            return web.json_response({
                "debate_id": engine.debate_id,
                "topic": topic,
                "max_rounds": max_rounds,
                "status": "created"
            })
            
        except Exception as e:
            logger.error(f"Failed to create debate: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def _get_debate_status(self, request):
        debate_id = request.match_info['debate_id']
        
        if debate_id not in self.active_debates:
            return web.json_response({"error": "Debate not found"}, status=404)
            
        debate = self.active_debates[debate_id]
        engine = debate["engine"]
        
        return web.json_response({
            "debate_id": debate_id,
            "topic": debate["topic"],
            "status": debate["status"],
            "current_round": engine.current_round,
            "current_phase": engine.current_phase.value,
            "total_turns": len(engine.history),
            "is_active": engine.is_active
        })
    
    async def _start_debate(self, request):
        debate_id = request.match_info['debate_id']
        
        if debate_id not in self.active_debates:
            return web.json_response({"error": "Debate not found"}, status=404)
            
        debate = self.active_debates[debate_id]
        if debate["status"] == "running":
            return web.json_response({"error": "Debate already running"}, status=400)
            
        # Start the debate in background
        engine = debate["engine"]
        debate["status"] = "running"
        
        async def run_debate():
            try:
                await engine.run_debate()
                debate["status"] = "completed"
                
                # Broadcast completion
                await self.stream_manager.broadcast_event(debate_id, {
                    "event": "debate_completed",
                    "transcript": engine.get_transcript(),
                    "statistics": engine.get_statistics()
                })
                
            except Exception as e:
                logger.error(f"Debate execution error: {e}")
                debate["status"] = "error"
                await self.stream_manager.broadcast_event(debate_id, {
                    "event": "debate_error",
                    "error": str(e)
                })
        
        # Run debate asynchronously
        asyncio.create_task(run_debate())
        
        return web.json_response({
            "debate_id": debate_id,
            "status": "starting"
        })
    
    async def _stop_debate(self, request):
        debate_id = request.match_info['debate_id']
        
        if debate_id in self.active_debates:
            debate = self.active_debates[debate_id]
            debate["status"] = "stopped"
            
            # Notify clients
            await self.stream_manager.broadcast_event(debate_id, {
                "event": "debate_stopped"
            })
            
            # Clean up after a delay
            async def cleanup():
                await asyncio.sleep(60)  # Keep data for 1 minute
                if debate_id in self.active_debates:
                    del self.active_debates[debate_id]
            
            asyncio.create_task(cleanup())
            
            return web.json_response({"message": "Debate stopped"})
        else:
            return web.json_response({"error": "Debate not found"}, status=404)
    
    async def start_server(self):
        """Start the audio server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"Debate audio server started on {self.host}:{self.port}")
        return runner

async def main():
    import logging
    logging.basicConfig(level=logging.INFO)
    
    server = DebateAudioServer()
    runner = await server.start_server()
    
    try:
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())