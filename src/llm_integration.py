#!/usr/bin/env python3

import os
import asyncio
import json
import aiohttp
from typing import List, Dict, Optional
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class LLMArgumentGenerator:
    def __init__(self):
        # Try multiple LLM providers in order of preference
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        
        # Groq models optimized for speed
        self.groq_model = "mixtral-8x7b-32768"  # Fast and capable
        # Google model
        self.google_model = "gemini-pro"
        # Ollama local models (using best available)
        self.ollama_model = self._select_best_ollama_model()
        
        self.provider = self._determine_provider()
        logger.info(f"Using LLM provider: {self.provider}")
        if self.provider == "ollama":
            logger.info(f"Ollama model selected: {self.ollama_model}")
        elif self.provider == "groq":
            logger.info(f"Groq model selected: {self.groq_model}")
        elif self.provider == "google":
            logger.info(f"Google model selected: {self.google_model}")
    
    def _select_best_ollama_model(self) -> str:
        """Select the best available Ollama model for debates"""
        # Priority order: best reasoning capabilities for debates
        preferred_models = [
            "gemma2:latest",      # Excellent reasoning (Google's latest)
            "llama3:instruct",    # Instruction-tuned, great for structured tasks
            "llama3:latest",      # Solid general performance
            "mistral:latest",     # Good debate capabilities
            "phi3:latest",        # Microsoft's efficient model
            "phi:latest",         # Compact fallback
            "codellama:latest"    # Last resort (optimized for code but capable)
        ]
        
        # Use async function to check availability later if needed
        # For now, return the best model you have based on your `ollama list`
        return "gemma2:latest"  # This is your best model for debate tasks
    
    async def _check_ollama_availability(self) -> bool:
        """Check if Ollama server is running and model is available"""
        try:
            url = f"{self.ollama_url}/api/tags"
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        model_names = [model['name'] for model in data.get('models', [])]
                        return self.ollama_model in model_names
            return False
        except:
            return False
    
    def _determine_provider(self) -> str:
        if self.groq_api_key:
            return "groq"
        elif self.google_api_key:
            return "google"
        else:
            return "ollama"  # Fallback to local Ollama
    
    async def generate_opening_statement(
        self, 
        agent_name: str,
        agent_personality: str,
        agent_style: str,
        position: str,
        topic: str
    ) -> str:
        
        prompt = f"""You are {agent_name}, a professional debater with a {agent_personality} approach.
Your argumentation style: {agent_style}

Generate a compelling 2-3 sentence opening statement for the {position} position on: {topic}
Be concise, impactful, and set the tone for your argument."""

        return await self._generate(prompt)
    
    async def generate_argument(
        self,
        agent_name: str,
        agent_personality: str,
        agent_style: str,
        position: str,
        topic: str,
        round_num: int,
        context: List[Dict]
    ) -> str:
        
        recent_context = self._format_context(context[-4:]) if context else "No prior arguments."
        
        prompt = f"""You are {agent_name}, a debater with a {agent_personality} approach.
Your style: {agent_style}
Position: {position} on "{topic}"
Round: {round_num + 1}

Recent debate context:
{recent_context}

Generate a 2-3 sentence argument that:
1. Advances your position with new evidence or reasoning
2. May address opponent's points if relevant
3. Stays focused and impactful"""

        return await self._generate(prompt)
    
    async def generate_rebuttal(
        self,
        agent_name: str,
        agent_personality: str,
        agent_style: str,
        position: str,
        topic: str,
        opponent_argument: str
    ) -> str:
        
        prompt = f"""You are {agent_name}, a debater with a {agent_personality} approach.
Your style: {agent_style}
Position: {position} on "{topic}"

Opponent just argued: {opponent_argument}

Generate a sharp 2-3 sentence rebuttal that:
1. Directly addresses their key claim
2. Points out flaws or counterevidence
3. Reinforces your position"""

        return await self._generate(prompt)
    
    async def generate_closing_statement(
        self,
        agent_name: str,
        agent_personality: str,
        position: str,
        topic: str,
        key_points: List[str]
    ) -> str:
        
        points_summary = "\n".join(f"- {p}" for p in key_points[:3]) if key_points else "Various strong arguments"
        
        prompt = f"""You are {agent_name} giving a closing statement.
Position: {position} on "{topic}"

Key points made:
{points_summary}

Generate a powerful 2-3 sentence closing that:
1. Summarizes your strongest argument
2. Leaves a lasting impression
3. Calls for agreement with your position"""

        return await self._generate(prompt)
    
    async def _generate(self, prompt: str) -> str:
        try:
            if self.provider == "groq":
                return await self._generate_groq(prompt)
            elif self.provider == "google":
                return await self._generate_google(prompt)
            else:
                return await self._generate_ollama(prompt)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._fallback_response(prompt)
    
    async def _generate_groq(self, prompt: str) -> str:
        """Use Groq API - optimized for speed"""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.groq_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 150,
            "temperature": 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content'].strip()
                else:
                    raise Exception(f"Groq API error: {response.status}")
    
    async def _generate_google(self, prompt: str) -> str:
        """Use Google Gemini API"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.google_model}:generateContent"
        params = {"key": self.google_api_key}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": 150,
                "temperature": 0.7
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['candidates'][0]['content']['parts'][0]['text'].strip()
                else:
                    raise Exception(f"Google API error: {response.status}")
    
    async def _generate_ollama(self, prompt: str) -> str:
        """Use local Ollama as fallback"""
        
        # Enhanced prompt for better debate responses
        enhanced_prompt = f"""You are participating in a formal debate. Respond with exactly 2-3 clear, impactful sentences.

{prompt}

Response:"""
        
        url = f"{self.ollama_url}/api/generate"
        data = {
            "model": self.ollama_model,
            "prompt": enhanced_prompt,
            "stream": False,
            "options": {
                "num_predict": 200,  # Increased for better responses
                "temperature": 0.8,   # Slightly higher for creativity
                "top_p": 0.9,
                "stop": ["\n\n", "Human:", "Assistant:"]
            }
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                logger.info(f"Generating with Ollama model: {self.ollama_model}")
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result['response'].strip()
                        
                        # Clean up the response
                        if response_text.startswith("Response:"):
                            response_text = response_text[9:].strip()
                        
                        return response_text if response_text else self._fallback_response(prompt)
                    else:
                        error_text = await response.text()
                        logger.error(f"Ollama HTTP {response.status}: {error_text}")
                        raise Exception(f"Ollama error: {response.status}")
                        
        except aiohttp.ClientConnectorError:
            logger.warning("Ollama server not available, using fallback responses")
            return self._fallback_response(prompt)
        except asyncio.TimeoutError:
            logger.warning("Ollama request timeout, using fallback responses")
            return self._fallback_response(prompt)
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return self._fallback_response(prompt)
    
    def _format_context(self, turns: List[Dict]) -> str:
        if not turns:
            return "No prior context."
        
        formatted = []
        for turn in turns:
            formatted.append(f"{turn.get('agent_name', 'Unknown')}: {turn.get('statement', '')}")
        return "\n".join(formatted)
    
    def _fallback_response(self, prompt: str) -> str:
        """Deterministic fallback when all LLMs fail"""
        if "opening statement" in prompt.lower():
            if "pro" in prompt:
                return "I stand firmly in support of this proposition. The evidence is clear, and the benefits are undeniable."
            else:
                return "We must carefully examine this proposition. There are significant concerns that demand our attention."
        elif "rebuttal" in prompt.lower():
            return "While my opponent makes interesting points, the evidence tells a different story. We must look at the facts objectively."
        elif "closing" in prompt.lower():
            if "pro" in prompt:
                return "The arguments presented today clearly demonstrate why this proposition deserves our support. The path forward is clear."
            else:
                return "The risks and concerns raised today cannot be ignored. We must proceed with caution and wisdom."
        else:
            # General argument
            if "pro" in prompt:
                return "Research and real-world evidence consistently support this position. The data speaks for itself."
            else:
                return "We must consider the broader implications and potential consequences. Alternative approaches may serve us better."

class DebateLLMBridge:
    def __init__(self):
        self.generator = LLMArgumentGenerator()
        self.cache = {}
    
    async def enhance_debate_engine(self, engine):
        """Inject LLM generation into debate engine"""
        engine._generate_opening_statement = self._create_opening_wrapper(engine)
        engine._generate_argument = self._create_argument_wrapper(engine)
        engine._generate_rebuttal = self._create_rebuttal_wrapper(engine)
        engine._generate_closing_statement = self._create_closing_wrapper(engine)
    
    def _create_opening_wrapper(self, engine):
        async def wrapper(agent):
            position = "pro" if agent.role.value == "pro" else "con"
            return await self.generator.generate_opening_statement(
                agent.name,
                agent.personality,
                agent.argument_style,
                position,
                engine.topic
            )
        return wrapper
    
    def _create_argument_wrapper(self, engine):
        async def wrapper(agent, round_num):
            position = "pro" if agent.role.value == "pro" else "con"
            context = [
                {"agent_name": t.agent_name, "statement": t.statement}
                for t in engine.history[-6:]
            ]
            return await self.generator.generate_argument(
                agent.name,
                agent.personality,
                agent.argument_style,
                position,
                engine.topic,
                round_num,
                context
            )
        return wrapper
    
    def _create_rebuttal_wrapper(self, engine):
        async def wrapper(agent):
            position = "pro" if agent.role.value == "pro" else "con"
            opponent_turns = [
                t for t in engine.history 
                if t.role.value != agent.role.value and t.role.value != "moderator"
            ]
            opponent_arg = opponent_turns[-1].statement if opponent_turns else ""
            
            return await self.generator.generate_rebuttal(
                agent.name,
                agent.personality,
                agent.argument_style,
                position,
                engine.topic,
                opponent_arg
            )
        return wrapper
    
    def _create_closing_wrapper(self, engine):
        async def wrapper(agent):
            position = "pro" if agent.role.value == "pro" else "con"
            agent_turns = [
                t.statement for t in engine.history 
                if t.agent_id == agent.id
            ]
            return await self.generator.generate_closing_statement(
                agent.name,
                agent.personality,
                position,
                engine.topic,
                agent_turns[-3:] if len(agent_turns) > 3 else agent_turns
            )
        return wrapper