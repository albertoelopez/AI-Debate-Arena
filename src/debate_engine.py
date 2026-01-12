#!/usr/bin/env python3

import asyncio
import json
import time
from enum import Enum
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Callable
import logging

# Try to import liquid_audio, fallback if not available
try:
    from liquid_audio import LiquidAudio
    LIQUID_AUDIO_AVAILABLE = True
except ImportError:
    LIQUID_AUDIO_AVAILABLE = False
    LiquidAudio = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DebateRole(Enum):
    PRO = "pro"
    CON = "con"
    MODERATOR = "moderator"

class DebatePhase(Enum):
    INTRODUCTION = "introduction"
    OPENING_STATEMENTS = "opening_statements"
    MAIN_ARGUMENTS = "main_arguments"
    REBUTTALS = "rebuttals"
    CLOSING_STATEMENTS = "closing_statements"
    CONCLUSION = "conclusion"

@dataclass
class Agent:
    id: str
    name: str
    role: DebateRole
    voice_id: int
    personality: str
    argument_style: str
    
@dataclass
class DebateTurn:
    agent_id: str
    agent_name: str
    role: DebateRole
    statement: str
    audio_data: Optional[bytes]
    timestamp: float
    phase: DebatePhase
    is_rebuttal: bool = False
    duration: float = 0.0

class DebateEngine:
    def __init__(self, topic: str, max_rounds: int = 5):
        self.topic = topic
        self.max_rounds = max_rounds
        self.current_round = 0
        self.current_phase = DebatePhase.INTRODUCTION
        self.debate_id = f"debate_{int(time.time())}"
        self.history: List[DebateTurn] = []
        self.listeners: List[Callable] = []
        self.is_active = False
        
        if LIQUID_AUDIO_AVAILABLE:
            try:
                self.audio_model = LiquidAudio()
                logger.info("✅ Liquid Audio model initialized")
            except Exception as e:
                logger.warning(f"Could not initialize Liquid Audio: {e}")
                self.audio_model = None
        else:
            logger.warning("⚠️  Liquid Audio not installed - debates will run without voice synthesis")
            self.audio_model = None
        
        self.agents = self._initialize_agents()
        
    def _initialize_agents(self) -> Dict[str, Agent]:
        return {
            "pro": Agent(
                id="agent_pro",
                name="Dr. Advocate",
                role=DebateRole.PRO,
                voice_id=0,
                personality="analytical, evidence-based, assertive",
                argument_style="uses statistics, research, and logical reasoning"
            ),
            "con": Agent(
                id="agent_con",
                name="Prof. Challenger",
                role=DebateRole.CON,
                voice_id=1,
                personality="critical, philosophical, thorough",
                argument_style="emphasizes ethics, implications, and alternative perspectives"
            ),
            "moderator": Agent(
                id="agent_mod",
                name="Moderator",
                role=DebateRole.MODERATOR,
                voice_id=2,
                personality="neutral, professional, engaging",
                argument_style="facilitates balanced discussion"
            )
        }
    
    async def generate_speech(self, text: str, voice_id: int) -> Optional[bytes]:
        if not self.audio_model:
            return None
            
        try:
            audio_data = await self.audio_model.generate(
                text=text,
                voice_id=voice_id,
                mode="sequential"
            )
            return audio_data
        except Exception as e:
            logger.error(f"Speech generation failed: {e}")
            return None
    
    async def create_turn(
        self, 
        agent: Agent, 
        statement: str, 
        phase: DebatePhase,
        is_rebuttal: bool = False
    ) -> DebateTurn:
        
        start_time = time.time()
        audio_data = await self.generate_speech(statement, agent.voice_id)
        duration = time.time() - start_time
        
        turn = DebateTurn(
            agent_id=agent.id,
            agent_name=agent.name,
            role=agent.role,
            statement=statement,
            audio_data=audio_data,
            timestamp=time.time(),
            phase=phase,
            is_rebuttal=is_rebuttal,
            duration=duration
        )
        
        self.history.append(turn)
        await self._notify_listeners(turn)
        
        return turn
    
    async def _notify_listeners(self, turn: DebateTurn):
        for listener in self.listeners:
            try:
                await listener({
                    "event": "turn_completed",
                    "turn": {
                        "agent_id": turn.agent_id,
                        "agent_name": turn.agent_name,
                        "role": turn.role.value,
                        "statement": turn.statement,
                        "timestamp": turn.timestamp,
                        "phase": turn.phase.value,
                        "is_rebuttal": turn.is_rebuttal,
                        "has_audio": turn.audio_data is not None
                    }
                })
            except Exception as e:
                logger.error(f"Failed to notify listener: {e}")
    
    def add_listener(self, callback: Callable):
        self.listeners.append(callback)
    
    def remove_listener(self, callback: Callable):
        if callback in self.listeners:
            self.listeners.remove(callback)
    
    async def run_debate(self):
        self.is_active = True
        
        try:
            await self._introduction_phase()
            await self._opening_statements_phase()
            await self._main_arguments_phase()
            await self._rebuttals_phase()
            await self._closing_statements_phase()
            await self._conclusion_phase()
        except Exception as e:
            logger.error(f"Debate error: {e}")
        finally:
            self.is_active = False
            await self._notify_debate_end()
    
    async def _introduction_phase(self):
        self.current_phase = DebatePhase.INTRODUCTION
        moderator = self.agents["moderator"]
        
        intro = f"Welcome to today's debate on: {self.topic}. I'm your moderator, {moderator.name}. "
        intro += f"Arguing for the proposition, we have {self.agents['pro'].name}. "
        intro += f"Arguing against, we have {self.agents['con'].name}. "
        intro += "Let's begin with opening statements."
        
        await self.create_turn(moderator, intro, DebatePhase.INTRODUCTION)
        await asyncio.sleep(2)
    
    async def _opening_statements_phase(self):
        self.current_phase = DebatePhase.OPENING_STATEMENTS
        
        for role in ["pro", "con"]:
            agent = self.agents[role]
            statement = await self._generate_opening_statement(agent)
            await self.create_turn(agent, statement, DebatePhase.OPENING_STATEMENTS)
            await asyncio.sleep(3)
    
    async def _main_arguments_phase(self):
        self.current_phase = DebatePhase.MAIN_ARGUMENTS
        
        for round_num in range(self.max_rounds):
            self.current_round = round_num + 1
            
            for role in ["pro", "con"]:
                agent = self.agents[role]
                argument = await self._generate_argument(agent, round_num)
                is_rebuttal = role == "con" and round_num > 0
                await self.create_turn(agent, argument, DebatePhase.MAIN_ARGUMENTS, is_rebuttal)
                await asyncio.sleep(2)
            
            if (round_num + 1) % 2 == 0:
                await self._moderator_interjection()
    
    async def _rebuttals_phase(self):
        self.current_phase = DebatePhase.REBUTTALS
        
        for role in ["con", "pro"]:
            agent = self.agents[role]
            rebuttal = await self._generate_rebuttal(agent)
            await self.create_turn(agent, rebuttal, DebatePhase.REBUTTALS, is_rebuttal=True)
            await asyncio.sleep(3)
    
    async def _closing_statements_phase(self):
        self.current_phase = DebatePhase.CLOSING_STATEMENTS
        
        for role in ["pro", "con"]:
            agent = self.agents[role]
            closing = await self._generate_closing_statement(agent)
            await self.create_turn(agent, closing, DebatePhase.CLOSING_STATEMENTS)
            await asyncio.sleep(3)
    
    async def _conclusion_phase(self):
        self.current_phase = DebatePhase.CONCLUSION
        moderator = self.agents["moderator"]
        
        conclusion = f"Thank you both for this engaging debate on {self.topic}. "
        conclusion += "The arguments presented today have given us much to consider. "
        conclusion += "I encourage our audience to reflect on these perspectives."
        
        await self.create_turn(moderator, conclusion, DebatePhase.CONCLUSION)
    
    async def _moderator_interjection(self):
        moderator = self.agents["moderator"]
        interjection = f"Excellent points from both sides. Let's continue exploring {self.topic}."
        await self.create_turn(moderator, interjection, self.current_phase)
        await asyncio.sleep(2)
    
    async def _generate_opening_statement(self, agent: Agent) -> str:
        position = "support" if agent.role == DebateRole.PRO else "oppose"
        return f"Good evening. I stand to {position} the proposition that {self.topic}. "
    
    async def _generate_argument(self, agent: Agent, round_num: int) -> str:
        return f"In round {round_num + 1}, I argue that regarding {self.topic}..."
    
    async def _generate_rebuttal(self, agent: Agent) -> str:
        return f"While my opponent makes some points, the evidence clearly shows..."
    
    async def _generate_closing_statement(self, agent: Agent) -> str:
        position = "supporting" if agent.role == DebateRole.PRO else "opposing"
        return f"In conclusion, the arguments for {position} this proposition are compelling..."
    
    async def _notify_debate_end(self):
        for listener in self.listeners:
            try:
                await listener({
                    "event": "debate_ended",
                    "debate_id": self.debate_id,
                    "total_turns": len(self.history)
                })
            except Exception as e:
                logger.error(f"Failed to notify debate end: {e}")
    
    def get_transcript(self) -> str:
        transcript = f"DEBATE TRANSCRIPT\nTopic: {self.topic}\n{'=' * 50}\n\n"
        
        for turn in self.history:
            timestamp = time.strftime("%M:%S", time.localtime(turn.timestamp))
            transcript += f"[{timestamp}] {turn.agent_name} ({turn.role.value}):\n"
            transcript += f"{turn.statement}\n\n"
        
        return transcript
    
    def get_statistics(self) -> Dict:
        pro_turns = [t for t in self.history if t.role == DebateRole.PRO]
        con_turns = [t for t in self.history if t.role == DebateRole.CON]
        
        return {
            "debate_id": self.debate_id,
            "topic": self.topic,
            "total_turns": len(self.history),
            "pro_turns": len(pro_turns),
            "con_turns": len(con_turns),
            "total_duration": sum(t.duration for t in self.history),
            "phases_completed": [p.value for p in DebatePhase]
        }