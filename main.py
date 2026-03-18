#!/usr/bin/env python3
"""
AI Debate Arena - Main Entry Point
Real-time AI debates with Liquid Audio voice synthesis
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from audio_server import DebateAudioServer
from observability import setup_observability

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('debate_arena.log')
        ]
    )

async def main():
    """Main application entry point"""
    setup_observability("ai-debate-arena-v1")
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🎭 Starting AI Debate Arena...")
    
    # Get configuration from environment
    host = os.getenv('HOST', 'localhost')
    port = int(os.getenv('PORT', 8080))
    
    # Create and start the server
    server = DebateAudioServer(host=host, port=port)
    runner = await server.start_server()
    
    logger.info(f"🚀 Server running at http://{host}:{port}")
    logger.info("💡 Open your browser and navigate to the URL above to start debating!")
    
    try:
        # Keep the server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down server...")
    finally:
        await runner.cleanup()
        logger.info("✅ Server shutdown complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
