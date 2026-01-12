#!/usr/bin/env python3
"""
AI Debate Arena Engine v2 - Multi-Debater Edition
"When I grow up, I want to be a principal or a caterpillar!" - Ralph Wiggum

Supports N debaters with custom positions, powered by PydanticAI.
"""

import asyncio
import time
import logging
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass

from models import (
    DebateConfig,
    Debater,
    DebateArgument,
    ModeratorAction,
    DebateTurnResult,
    DebateState,
    TopicRelevanceCheck,
    DEBATE_TEMPLATES,
    create_custom_debate
)

from agents import (
    generate_argument,
    generate_opening,
    generate_closing,
    generate_moderation,
    check_topic_relevance,
    ModeratorContext
)

# Try to import Liquid Audio
try:
    from liquid_audio import LiquidAudio
    LIQUID_AUDIO_AVAILABLE = True
except ImportError:
    LIQUID_AUDIO_AVAILABLE = False
    LiquidAudio = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiDebateEngine:
    """
    Engine for running multi-party debates with N debaters.
    Uses PydanticAI agents for argument generation and moderation.
    """

    def __init__(self, config: DebateConfig):
        self.config = config
        self.debate_id = f"debate_{int(time.time())}"

        self.state = DebateState(
            debate_id=self.debate_id,
            config=config,
            current_round=0,
            current_speaker_index=0,
            phase="not_started",
            turns=[],
            is_active=False
        )

        self.listeners: List[Callable] = []

        # Audio model (optional)
        if LIQUID_AUDIO_AVAILABLE:
            try:
                self.audio_model = LiquidAudio()
                logger.info("✅ Liquid Audio initialized")
            except Exception as e:
                logger.warning(f"Could not initialize Liquid Audio: {e}")
                self.audio_model = None
        else:
            logger.info("⚠️ Running without voice synthesis")
            self.audio_model = None

    @classmethod
    def from_template(cls, template_name: str) -> "MultiDebateEngine":
        """Create engine from a pre-built template"""
        if template_name not in DEBATE_TEMPLATES:
            raise ValueError(f"Unknown template: {template_name}. Available: {list(DEBATE_TEMPLATES.keys())}")
        return cls(DEBATE_TEMPLATES[template_name])

    @classmethod
    def create_custom(
        cls,
        topic: str,
        positions: List[dict],
        max_rounds: int = 3,
        moderator_strictness: str = "moderate"
    ) -> "MultiDebateEngine":
        """Create engine with custom configuration"""
        config = create_custom_debate(topic, positions, max_rounds, moderator_strictness)
        return cls(config)

    def add_listener(self, callback: Callable):
        """Add event listener for real-time updates"""
        self.listeners.append(callback)

    def remove_listener(self, callback: Callable):
        """Remove event listener"""
        if callback in self.listeners:
            self.listeners.remove(callback)

    async def _notify(self, event_type: str, data: dict):
        """Notify all listeners of an event"""
        event = {"event": event_type, "debate_id": self.debate_id, **data}
        for listener in self.listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event)
                else:
                    listener(event)
            except Exception as e:
                logger.error(f"Listener notification failed: {e}")

    async def _generate_speech(self, text: str, voice_id: int) -> Optional[bytes]:
        """Generate speech audio from text"""
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

    async def _create_turn(
        self,
        debater: Debater,
        argument: DebateArgument,
        round_number: int,
        turn_in_round: int,
        relevance_check: Optional[TopicRelevanceCheck] = None
    ) -> DebateTurnResult:
        """Create and record a debate turn"""

        # Generate audio if available
        speech_text = argument.to_speech_text()
        audio_data = await self._generate_speech(speech_text, debater.voice_id)

        turn = DebateTurnResult(
            debater_id=debater.id,
            debater_name=debater.name,
            position_name=debater.position.name,
            argument=argument,
            timestamp=time.time(),
            round_number=round_number,
            turn_in_round=turn_in_round,
            audio_generated=audio_data is not None,
            relevance_check=relevance_check
        )

        self.state.turns.append(turn)

        # Notify listeners
        await self._notify("turn_completed", {
            "turn": {
                "debater_id": turn.debater_id,
                "debater_name": turn.debater_name,
                "position_name": turn.position_name,
                "statement": argument.main_claim,
                "supporting_points": argument.supporting_points,
                "timestamp": turn.timestamp,
                "round": round_number,
                "phase": self.state.phase,
                "has_audio": turn.audio_generated,
                "avatar": debater.avatar_emoji
            }
        })

        return turn

    async def _moderator_speak(self, action: ModeratorAction):
        """Have the moderator speak"""
        audio_data = await self._generate_speech(action.message, voice_id=3)

        await self._notify("moderator_action", {
            "action_type": action.action_type,
            "message": action.message,
            "addressed_to": action.addressed_to,
            "off_topic_warning": action.off_topic_warning,
            "has_audio": audio_data is not None
        })

        # Brief pause after moderator speaks
        await asyncio.sleep(1)

    async def run_debate(self):
        """Run the complete debate"""
        self.state.is_active = True
        self.state.phase = "introduction"

        try:
            await self._introduction_phase()
            await self._opening_statements_phase()
            await self._main_debate_phase()
            if self.config.allow_rebuttals:
                await self._rebuttal_phase()
            await self._closing_statements_phase()
            await self._conclusion_phase()

        except Exception as e:
            logger.error(f"Debate error: {e}")
            await self._notify("debate_error", {"error": str(e)})
        finally:
            self.state.is_active = False
            self.state.phase = "finished"
            await self._notify("debate_ended", {
                "total_turns": len(self.state.turns),
                "rounds_completed": self.state.current_round
            })

    async def _introduction_phase(self):
        """Moderator introduces the debate"""
        self.state.phase = "introduction"

        debater_intros = ", ".join([
            f"{d.name} representing the {d.position.name} position"
            for d in self.config.debaters
        ])

        mod_context = ModeratorContext(
            topic=self.config.topic,
            topic_description=self.config.description,
            debaters=self.config.debaters,
            recent_turns=[],
            current_phase="introduction",
            strictness=self.config.moderator_strictness
        )

        intro_action = await generate_moderation(mod_context, "introduce")

        # Override with a proper introduction
        intro_action.message = (
            f"Welcome to today's debate on: {self.config.topic}. "
            f"We have {len(self.config.debaters)} distinguished speakers: {debater_intros}. "
            f"Let's begin with opening statements."
        )

        await self._moderator_speak(intro_action)

    async def _opening_statements_phase(self):
        """Each debater gives an opening statement"""
        self.state.phase = "opening"

        for i, debater in enumerate(self.config.debaters):
            await self._notify("speaker_change", {
                "speaker": debater.name,
                "position": debater.position.name,
                "phase": "opening"
            })

            argument = await generate_opening(debater, self.config)

            await self._create_turn(
                debater=debater,
                argument=argument,
                round_number=0,
                turn_in_round=i
            )

            await asyncio.sleep(2)  # Pause between speakers

    async def _main_debate_phase(self):
        """Main debate rounds"""
        self.state.phase = "debate"

        for round_num in range(1, self.config.max_rounds + 1):
            self.state.current_round = round_num

            await self._notify("round_start", {
                "round": round_num,
                "total_rounds": self.config.max_rounds
            })

            # Each debater speaks
            for i, debater in enumerate(self.config.debaters):
                self.state.current_speaker_index = i

                await self._notify("speaker_change", {
                    "speaker": debater.name,
                    "position": debater.position.name,
                    "round": round_num
                })

                # Generate argument
                argument = await generate_argument(
                    debater=debater,
                    debate_config=self.config,
                    recent_arguments=self.state.turns,
                    current_round=round_num,
                    is_rebuttal=round_num > 1,  # After first round, can reference others
                    target_debater=self._get_previous_speaker_name(i)
                )

                # Check topic relevance
                relevance = await check_topic_relevance(
                    argument=argument,
                    topic=self.config.topic,
                    topic_description=self.config.description,
                    strictness=self.config.moderator_strictness
                )

                await self._create_turn(
                    debater=debater,
                    argument=argument,
                    round_number=round_num,
                    turn_in_round=i,
                    relevance_check=relevance
                )

                # Moderator intervention if off-topic
                if not relevance.is_relevant or relevance.relevance_score < 0.5:
                    await self._handle_off_topic(debater, relevance)

                await asyncio.sleep(2)

            # Moderator transition between rounds
            if round_num < self.config.max_rounds:
                await self._moderator_transition(round_num)

    def _get_previous_speaker_name(self, current_index: int) -> Optional[str]:
        """Get the name of the previous speaker"""
        if current_index > 0:
            return self.config.debaters[current_index - 1].name
        elif self.state.turns:
            return self.state.turns[-1].debater_name
        return None

    async def _handle_off_topic(self, debater: Debater, relevance: TopicRelevanceCheck):
        """Handle a debater going off-topic"""
        mod_context = ModeratorContext(
            topic=self.config.topic,
            topic_description=self.config.description,
            debaters=self.config.debaters,
            recent_turns=self.state.turns[-3:],
            current_phase=self.state.phase,
            strictness=self.config.moderator_strictness,
            last_speaker=debater.name
        )

        redirect = await generate_moderation(mod_context, "redirect")
        redirect.addressed_to = debater.name
        redirect.off_topic_warning = True
        redirect.topic_reminder = f"Please stay focused on: {self.config.topic}"

        await self._moderator_speak(redirect)

    async def _moderator_transition(self, completed_round: int):
        """Moderator transitions between rounds"""
        mod_context = ModeratorContext(
            topic=self.config.topic,
            topic_description=self.config.description,
            debaters=self.config.debaters,
            recent_turns=self.state.turns[-len(self.config.debaters):],
            current_phase="debate",
            strictness=self.config.moderator_strictness
        )

        transition = await generate_moderation(mod_context, "transition")
        transition.message = (
            f"Excellent points from all speakers. "
            f"We now move to round {completed_round + 1} of {self.config.max_rounds}. "
            f"Please continue your arguments on {self.config.topic}."
        )

        await self._moderator_speak(transition)

    async def _rebuttal_phase(self):
        """Final rebuttal round"""
        self.state.phase = "rebuttals"

        await self._notify("phase_change", {"phase": "rebuttals"})

        mod_action = ModeratorAction(
            action_type="transition",
            message="We now enter the rebuttal phase. Each speaker will have a chance to directly address the arguments made by others.",
            off_topic_warning=False
        )
        await self._moderator_speak(mod_action)

        # Reverse order for rebuttals (last speaker goes first)
        for i, debater in enumerate(reversed(self.config.debaters)):
            # Target the speaker who spoke before them in the main debate
            target_index = len(self.config.debaters) - i - 2
            target_debater = self.config.debaters[target_index].name if target_index >= 0 else None

            await self._notify("speaker_change", {
                "speaker": debater.name,
                "position": debater.position.name,
                "phase": "rebuttal"
            })

            argument = await generate_argument(
                debater=debater,
                debate_config=self.config,
                recent_arguments=self.state.turns,
                current_round=self.config.max_rounds + 1,
                is_rebuttal=True,
                target_debater=target_debater
            )

            await self._create_turn(
                debater=debater,
                argument=argument,
                round_number=self.config.max_rounds + 1,
                turn_in_round=i
            )

            await asyncio.sleep(2)

    async def _closing_statements_phase(self):
        """Each debater gives a closing statement"""
        self.state.phase = "closing"

        mod_action = ModeratorAction(
            action_type="transition",
            message="We now move to closing statements. Each speaker will summarize their position.",
            off_topic_warning=False
        )
        await self._moderator_speak(mod_action)

        for i, debater in enumerate(self.config.debaters):
            await self._notify("speaker_change", {
                "speaker": debater.name,
                "position": debater.position.name,
                "phase": "closing"
            })

            argument = await generate_closing(
                debater=debater,
                debate_config=self.config,
                debate_history=self.state.turns
            )

            await self._create_turn(
                debater=debater,
                argument=argument,
                round_number=self.config.max_rounds + 2,
                turn_in_round=i
            )

            await asyncio.sleep(2)

    async def _conclusion_phase(self):
        """Moderator concludes the debate"""
        self.state.phase = "conclusion"

        positions_summary = ", ".join([
            f"the {d.position.name} view from {d.name}"
            for d in self.config.debaters
        ])

        mod_action = ModeratorAction(
            action_type="conclude",
            message=(
                f"Thank you to all our speakers for this thought-provoking debate on {self.config.topic}. "
                f"We've heard compelling arguments from {positions_summary}. "
                f"We leave it to our audience to reflect on these perspectives."
            ),
            off_topic_warning=False
        )
        await self._moderator_speak(mod_action)

    def get_transcript(self) -> str:
        """Generate formatted transcript"""
        lines = [
            f"DEBATE TRANSCRIPT",
            f"Topic: {self.config.topic}",
            f"{'=' * 60}",
            ""
        ]

        for turn in self.state.turns:
            timestamp = time.strftime("%M:%S", time.localtime(turn.timestamp))
            lines.append(f"[{timestamp}] {turn.debater_name} ({turn.position_name}):")
            lines.append(f"  {turn.argument.main_claim}")
            if turn.argument.supporting_points:
                for point in turn.argument.supporting_points:
                    lines.append(f"  • {point}")
            lines.append("")

        return "\n".join(lines)

    def get_statistics(self) -> Dict:
        """Get debate statistics"""
        turns_by_debater = {}
        for turn in self.state.turns:
            if turn.debater_id not in turns_by_debater:
                turns_by_debater[turn.debater_id] = 0
            turns_by_debater[turn.debater_id] += 1

        return {
            "debate_id": self.debate_id,
            "topic": self.config.topic,
            "num_debaters": len(self.config.debaters),
            "debaters": [
                {"name": d.name, "position": d.position.name, "turns": turns_by_debater.get(d.id, 0)}
                for d in self.config.debaters
            ],
            "total_turns": len(self.state.turns),
            "rounds_completed": self.state.current_round,
            "phase": self.state.phase
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def quick_debate(topic: str, positions: List[str], rounds: int = 2) -> MultiDebateEngine:
    """
    Quick way to start a debate with just a topic and position names.

    Example:
        engine = await quick_debate(
            topic="Does God exist?",
            positions=["Atheist", "Agnostic", "Theist"]
        )
        await engine.run_debate()
    """
    position_configs = [
        {"name": pos, "stance": f"Argues from the {pos} perspective"}
        for pos in positions
    ]
    engine = MultiDebateEngine.create_custom(topic, position_configs, rounds)
    return engine


# Example usage
if __name__ == "__main__":
    async def main():
        # Use pre-built template
        engine = MultiDebateEngine.from_template("god_existence")

        # Add a simple listener
        async def print_event(event):
            if event["event"] == "turn_completed":
                turn = event["turn"]
                print(f"\n{turn['debater_name']} ({turn['position_name']}):")
                print(f"  {turn['statement']}")

        engine.add_listener(print_event)

        # Run the debate
        await engine.run_debate()

        # Print transcript
        print("\n" + "=" * 60)
        print(engine.get_transcript())

    asyncio.run(main())