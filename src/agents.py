#!/usr/bin/env python3
"""
PydanticAI Agents for AI Debate Arena
"Me fail debate? That's unpossible!" - Ralph Wiggum

Multi-debater system with intelligent moderation.
"""

import os
import asyncio
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.models.openai import OpenAIModel
from dotenv import load_dotenv
import logging

from models import (
    Debater,
    DebateConfig,
    DebateArgument,
    ModeratorAction,
    TopicRelevanceCheck,
    DebateTurnResult,
    DebateState
)

load_dotenv()
logger = logging.getLogger(__name__)


@dataclass
class DebateContext:
    """Context passed to agents during debate"""
    topic: str
    topic_description: Optional[str]
    current_round: int
    total_rounds: int
    debater: Debater
    other_debaters: List[Debater]
    recent_arguments: List[DebateTurnResult]
    is_rebuttal: bool = False
    target_debater: Optional[str] = None


@dataclass
class ModeratorContext:
    """Context passed to moderator agent"""
    topic: str
    topic_description: Optional[str]
    debaters: List[Debater]
    recent_turns: List[DebateTurnResult]
    current_phase: str
    strictness: str
    last_argument: Optional[DebateArgument] = None
    last_speaker: Optional[str] = None


def get_model():
    """Get the best available model for PydanticAI

    API keys should be set via environment variables:
    - GROQ_API_KEY for Groq
    - OPENAI_API_KEY for OpenAI
    """
    groq_key = os.getenv('GROQ_API_KEY')
    if groq_key:
        logger.info("Using Groq model for agents")
        # PydanticAI reads GROQ_API_KEY from environment automatically
        return GroqModel('llama-3.1-8b-instant')

    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        logger.info("Using OpenAI model for agents")
        # PydanticAI reads OPENAI_API_KEY from environment automatically
        return OpenAIModel('gpt-3.5-turbo')

    # Fallback - will fail if no API key is set
    logger.warning("No API key found, attempting default Groq model")
    return GroqModel('llama-3.1-8b-instant')


# ============================================================================
# DEBATER AGENT
# ============================================================================

debater_agent = Agent(
    model=get_model(),
    output_type=DebateArgument,
    system_prompt="""You are a skilled debate participant. Your role is to argue persuasively for your assigned position while engaging respectfully with other viewpoints.

IMPORTANT RULES:
1. Stay focused on the debate topic - do not go off on tangents
2. Make clear, concise arguments (2-3 sentences for main claim)
3. Support your position with evidence and reasoning
4. When rebutting, directly address the other debater's points
5. Maintain your character's personality and argument style
6. Be respectful but firm in defending your position

Your response must be a structured argument with:
- main_claim: Your primary point (2-3 clear sentences)
- supporting_points: 1-3 pieces of evidence/reasoning
- rebuttal_to: Name of debater you're responding to (if applicable)
- rhetorical_strategy: Your approach (logical, emotional, ethical)
- confidence_level: 0.0-1.0 how confident you are"""
)


@debater_agent.system_prompt
async def debater_dynamic_prompt(ctx: RunContext[DebateContext]) -> str:
    """Build dynamic system prompt based on debater context"""
    context = ctx.deps

    # Build context about other debaters
    others_info = "\n".join([
        f"- {d.name} ({d.position.name}): {d.position.stance}"
        for d in context.other_debaters
    ])

    # Build recent argument context
    recent_context = ""
    if context.recent_arguments:
        recent_context = "\n\nRecent arguments in this debate:\n"
        for turn in context.recent_arguments[-4:]:  # Last 4 turns
            recent_context += f"- {turn.debater_name} ({turn.position_name}): {turn.argument.main_claim}\n"

    prompt = f"""
You are {context.debater.name}, arguing from the {context.debater.position.name} position.

YOUR POSITION: {context.debater.position.stance}
YOUR KEY BELIEFS: {', '.join(context.debater.position.key_beliefs)}
YOUR PERSONALITY: {context.debater.personality}
YOUR ARGUMENT STYLE: {context.debater.argument_style}

DEBATE TOPIC: {context.topic}
{f"TOPIC CONTEXT: {context.topic_description}" if context.topic_description else ""}

OTHER DEBATERS:
{others_info}

CURRENT ROUND: {context.current_round} of {context.total_rounds}
{recent_context}

{"You are REBUTTING " + context.target_debater + ". Directly address their arguments." if context.is_rebuttal and context.target_debater else "Make your argument for your position."}

Remember: Stay ON TOPIC. The moderator will redirect you if you stray from "{context.topic}"
"""
    return prompt


async def generate_argument(
    debater: Debater,
    debate_config: DebateConfig,
    recent_arguments: List[DebateTurnResult],
    current_round: int,
    is_rebuttal: bool = False,
    target_debater: Optional[str] = None
) -> DebateArgument:
    """Generate an argument for a debater"""

    other_debaters = [d for d in debate_config.debaters if d.id != debater.id]

    context = DebateContext(
        topic=debate_config.topic,
        topic_description=debate_config.description,
        current_round=current_round,
        total_rounds=debate_config.max_rounds,
        debater=debater,
        other_debaters=other_debaters,
        recent_arguments=recent_arguments,
        is_rebuttal=is_rebuttal,
        target_debater=target_debater
    )

    try:
        result = await debater_agent.run(
            f"Generate your argument for round {current_round} on the topic: {debate_config.topic}",
            deps=context
        )
        return result.output
    except Exception as e:
        logger.error(f"Failed to generate argument for {debater.name}: {e}")
        # Return fallback argument
        return DebateArgument(
            main_claim=f"From the {debater.position.name} perspective, {debater.position.stance}",
            supporting_points=debater.position.key_beliefs[:2],
            rhetorical_strategy="logical",
            confidence_level=0.7
        )


# ============================================================================
# MODERATOR AGENT
# ============================================================================

moderator_agent = Agent(
    model=get_model(),
    output_type=ModeratorAction,
    system_prompt="""You are an experienced debate moderator. Your role is to:
1. Keep the debate focused on the topic
2. Ensure all participants get fair speaking time
3. Redirect debaters who go off-topic
4. Summarize key points when transitioning
5. Maintain a respectful, professional atmosphere

You must return a ModeratorAction with:
- action_type: "introduce", "transition", "redirect", "summarize", or "conclude"
- message: What you say (2-3 sentences, professional tone)
- addressed_to: Specific debater if applicable
- off_topic_warning: True if issuing an off-topic warning
- topic_reminder: Brief reminder of the topic if redirecting"""
)


@moderator_agent.system_prompt
async def moderator_dynamic_prompt(ctx: RunContext[ModeratorContext]) -> str:
    """Build dynamic system prompt for moderator"""
    context = ctx.deps

    debaters_info = "\n".join([
        f"- {d.name}: {d.position.name} ({d.position.stance})"
        for d in context.debaters
    ])

    strictness_guide = {
        "relaxed": "Allow some tangential discussion if it's interesting and loosely related.",
        "moderate": "Gently redirect after one off-topic statement. Allow brief tangents.",
        "strict": "Immediately redirect any off-topic discussion. Keep debate tightly focused."
    }

    recent_context = ""
    if context.recent_turns:
        recent_context = "\n\nRecent debate turns:\n"
        for turn in context.recent_turns[-3:]:
            recent_context += f"- {turn.debater_name}: {turn.argument.main_claim[:100]}...\n"

    return f"""
DEBATE TOPIC: {context.topic}
{f"TOPIC CONTEXT: {context.topic_description}" if context.topic_description else ""}

DEBATERS:
{debaters_info}

CURRENT PHASE: {context.current_phase}
STRICTNESS LEVEL: {context.strictness}
GUIDANCE: {strictness_guide.get(context.strictness, strictness_guide["moderate"])}
{recent_context}

{"LAST SPEAKER: " + context.last_speaker if context.last_speaker else ""}
{"LAST ARGUMENT: " + context.last_argument.main_claim if context.last_argument else ""}

Your job is to keep this debate productive and focused on "{context.topic}"
"""


# ============================================================================
# TOPIC RELEVANCE CHECKER
# ============================================================================

relevance_agent = Agent(
    model=get_model(),
    output_type=TopicRelevanceCheck,
    system_prompt="""You are a debate topic analyzer. Your job is to determine if an argument is relevant to the debate topic.

Analyze the argument and return:
- is_relevant: True if the argument relates to the topic, False otherwise
- relevance_score: 0.0 (completely off-topic) to 1.0 (perfectly on-topic)
- off_topic_elements: List any parts that strayed from the topic
- suggested_redirect: If off-topic, suggest how to get back on track

Be fair but vigilant. Some tangential points are acceptable if they support the main argument."""
)


async def check_topic_relevance(
    argument: DebateArgument,
    topic: str,
    topic_description: Optional[str],
    strictness: str
) -> TopicRelevanceCheck:
    """Check if an argument is relevant to the debate topic"""

    threshold = {"relaxed": 0.3, "moderate": 0.5, "strict": 0.7}.get(strictness, 0.5)

    try:
        result = await relevance_agent.run(
            f"""
            DEBATE TOPIC: {topic}
            {f"TOPIC CONTEXT: {topic_description}" if topic_description else ""}

            ARGUMENT TO CHECK:
            Main claim: {argument.main_claim}
            Supporting points: {', '.join(argument.supporting_points)}

            Is this argument relevant to the debate topic?
            """,
            deps=None
        )
        return result.output
    except Exception as e:
        logger.error(f"Relevance check failed: {e}")
        # Assume relevant if check fails
        return TopicRelevanceCheck(
            is_relevant=True,
            relevance_score=0.8,
            off_topic_elements=[],
            suggested_redirect=None
        )


async def generate_moderation(
    context: ModeratorContext,
    action_needed: str = "transition"
) -> ModeratorAction:
    """Generate a moderator action"""

    try:
        result = await moderator_agent.run(
            f"Generate a {action_needed} for the debate on: {context.topic}",
            deps=context
        )
        return result.output
    except Exception as e:
        logger.error(f"Moderation generation failed: {e}")
        # Return fallback moderation
        return ModeratorAction(
            action_type=action_needed,
            message=f"Let's continue our discussion on {context.topic}.",
            off_topic_warning=False
        )


# ============================================================================
# OPENING/CLOSING STATEMENT GENERATORS
# ============================================================================

opening_agent = Agent(
    model=get_model(),
    output_type=DebateArgument,
    system_prompt="""Generate a compelling opening statement for a debate participant.
The opening should:
1. Clearly state their position
2. Preview their main arguments
3. Be engaging and set the tone
4. Be 2-3 sentences maximum

Return as a DebateArgument with rhetorical_strategy="opening" """
)


closing_agent = Agent(
    model=get_model(),
    output_type=DebateArgument,
    system_prompt="""Generate a powerful closing statement for a debate participant.
The closing should:
1. Summarize their strongest points from the debate
2. Reinforce their position
3. Leave a lasting impression
4. Be 2-3 sentences maximum

Return as a DebateArgument with rhetorical_strategy="closing" """
)


async def generate_opening(
    debater: Debater,
    debate_config: DebateConfig
) -> DebateArgument:
    """Generate opening statement"""

    context = DebateContext(
        topic=debate_config.topic,
        topic_description=debate_config.description,
        current_round=0,
        total_rounds=debate_config.max_rounds,
        debater=debater,
        other_debaters=[d for d in debate_config.debaters if d.id != debater.id],
        recent_arguments=[]
    )

    try:
        result = await opening_agent.run(
            f"Generate opening statement for {debater.name} on: {debate_config.topic}",
            deps=context
        )
        return result.output
    except Exception as e:
        logger.error(f"Opening generation failed: {e}")
        return DebateArgument(
            main_claim=f"I stand here today to argue from the {debater.position.name} position. {debater.position.stance}",
            supporting_points=debater.position.key_beliefs[:2],
            rhetorical_strategy="opening",
            confidence_level=0.9
        )


async def generate_closing(
    debater: Debater,
    debate_config: DebateConfig,
    debate_history: List[DebateTurnResult]
) -> DebateArgument:
    """Generate closing statement"""

    # Get this debater's arguments from history
    my_arguments = [t for t in debate_history if t.debater_id == debater.id]

    context = DebateContext(
        topic=debate_config.topic,
        topic_description=debate_config.description,
        current_round=debate_config.max_rounds,
        total_rounds=debate_config.max_rounds,
        debater=debater,
        other_debaters=[d for d in debate_config.debaters if d.id != debater.id],
        recent_arguments=my_arguments
    )

    try:
        result = await closing_agent.run(
            f"Generate closing statement for {debater.name} on: {debate_config.topic}",
            deps=context
        )
        return result.output
    except Exception as e:
        logger.error(f"Closing generation failed: {e}")
        return DebateArgument(
            main_claim=f"In conclusion, the {debater.position.name} position offers the strongest case. {debater.position.stance}",
            supporting_points=["The evidence clearly supports this view."],
            rhetorical_strategy="closing",
            confidence_level=0.9
        )