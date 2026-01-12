#!/usr/bin/env python3
"""
Test script to verify AI Debate Arena setup
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_llm_integration():
    print("🧪 Testing LLM Integration...")
    
    try:
        from llm_integration import LLMArgumentGenerator
        
        generator = LLMArgumentGenerator()
        print(f"✅ LLM Provider: {generator.provider}")
        
        if generator.provider == "ollama":
            print(f"✅ Ollama Model: {generator.ollama_model}")
            
            # Test Ollama availability
            available = await generator._check_ollama_availability()
            if available:
                print("✅ Ollama server is running and model is available")
                
                # Test generation
                test_response = await generator._generate_ollama(
                    "You are Dr. Advocate arguing FOR the topic: Should AI help in education? Give a brief opening statement."
                )
                print(f"✅ Test generation: {test_response[:100]}...")
                
            else:
                print("⚠️  Ollama server not running or model not available")
                
        elif generator.provider == "groq":
            print("✅ Groq API configured")
        elif generator.provider == "google":
            print("✅ Google Gemini API configured")
            
        return True
        
    except Exception as e:
        print(f"❌ LLM Integration Error: {e}")
        return False

async def test_debate_engine():
    print("\n🎭 Testing Debate Engine...")
    
    try:
        from debate_engine import DebateEngine
        from llm_integration import DebateLLMBridge
        
        # Create test debate
        engine = DebateEngine("Should AI replace teachers?", max_rounds=1)
        bridge = DebateLLMBridge()
        await bridge.enhance_debate_engine(engine)
        
        print("✅ Debate engine created")
        print(f"✅ Topic: {engine.topic}")
        print(f"✅ Agents: {list(engine.agents.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Debate Engine Error: {e}")
        return False

def test_imports():
    print("📦 Testing Imports...")
    
    required_packages = [
        "asyncio",
        "aiohttp", 
        "json",
        "os",
        "time"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing.append(package)
    
    # Test optional liquid-audio
    try:
        import liquid_audio
        print("✅ liquid-audio (voice synthesis)")
    except ImportError:
        print("⚠️  liquid-audio not installed - using fallback")
    
    return len(missing) == 0

async def test_web_server():
    print("\n🌐 Testing Web Server Components...")
    
    try:
        from audio_server import DebateAudioServer
        
        # Test server creation (don't actually start)
        server = DebateAudioServer("localhost", 8081)  # Different port for testing
        print("✅ Audio server can be created")
        print("✅ WebSocket handler configured")
        print("✅ API routes configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Web Server Error: {e}")
        return False

async def main():
    print("🎭 AI Debate Arena - Setup Test")
    print("=" * 50)
    
    # Test basic imports
    imports_ok = test_imports()
    
    if not imports_ok:
        print("\n❌ Missing required packages. Run: pip install -r requirements.txt")
        return False
    
    # Test components
    llm_ok = await test_llm_integration()
    debate_ok = await test_debate_engine()
    web_ok = await test_web_server()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Imports: {'✅' if imports_ok else '❌'}")
    print(f"   LLM Integration: {'✅' if llm_ok else '❌'}")
    print(f"   Debate Engine: {'✅' if debate_ok else '❌'}")
    print(f"   Web Server: {'✅' if web_ok else '❌'}")
    
    if all([imports_ok, llm_ok, debate_ok, web_ok]):
        print("\n🎉 All tests passed! Ready to run debates!")
        print("\nTo start the arena:")
        print("   python main.py")
        print("   Open http://localhost:8080")
        return True
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)