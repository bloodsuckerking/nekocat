"""System prompt builder — auto-generates system prompts from PersonaProfile."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nekocat.persona.models import PersonaProfile


def build_system_prompt(profile: PersonaProfile) -> str:
    """Build a complete system prompt from a PersonaProfile.

    If the profile has a custom_system_prompt set, it is returned as-is.
    Otherwise, the prompt is assembled from: character card, traits,
    speech style instructions, prioritized behavior rules, and
    interaction guidelines.
    """
    if profile.custom_system_prompt is not None:
        return profile.custom_system_prompt

    parts: list[str] = []

    # 1. Character card
    parts.append(_build_character_card(profile))

    # 2. Personality traits (sorted by intensity descending)
    if profile.traits:
        parts.append(_build_traits_section(profile))

    # 3. Speech style guide
    parts.append(_build_speech_guide(profile))

    # 4. Behavior rules (sorted by priority)
    if profile.rules:
        parts.append(_build_rules_section(profile))

    # 5. Interaction guidelines
    parts.append(_build_interaction_guidelines(profile))

    return "\n\n".join(parts)


# ——— Section builders ———


def _build_character_card(profile: PersonaProfile) -> str:
    return (
        f"你是 **{profile.display_name}**，"
        f"一位拥有猫娘特征的虚构角色。\n\n"
        f"【角色简介】{profile.description}\n\n"
        f"【背景故事】{profile.backstory}"
    )


def _build_traits_section(profile: PersonaProfile) -> str:
    sorted_traits = sorted(profile.traits, key=lambda t: t.intensity, reverse=True)
    lines = ["【性格特质】"]
    for i, trait in enumerate(sorted_traits, 1):
        strength = (
            "极为明显" if trait.intensity >= 0.9 else
            "较为突出" if trait.intensity >= 0.7 else
            "偶尔表现" if trait.intensity >= 0.4 else
            "若隐若现"
        )
        lines.append(f"{i}. **{trait.name}**（{strength}）: {trait.description}")
    return "\n".join(lines)


def _build_speech_guide(profile: PersonaProfile) -> str:
    style_tips = _STYLE_GUIDE.get(profile.speech_style, _STYLE_GUIDE[profile.speech_style.__class__.MOE])

    interjections = profile.resolved_interjections
    endings = profile.resolved_endings

    interj_str = "、".join(interjections) if interjections else "（无）"
    endings_str = "、".join(endings) if endings else "（无）"

    return (
        f"【说话风格】{style_tips}\n\n"
        f"【口癖词（句首/句中可随机插入）】{interj_str}\n"
        f"【句尾装饰（句尾随机使用）】{endings_str}\n\n"
        "请在回复中自然地使用上述口癖和装饰词，不要每句话都用，也不要完全不用。"
        "使用频率大约每1-3句话出现一次最为自然。"
    )


def _build_rules_section(profile: PersonaProfile) -> str:
    sorted_rules = sorted(profile.rules, key=lambda r: r.priority)
    lines = ["【行为准则（必须遵守）】"]
    for i, r in enumerate(sorted_rules, 1):
        lines.append(f"{i}. {r.rule}")
    return "\n".join(lines)


def _build_interaction_guidelines(profile: PersonaProfile) -> str:
    return (
        "【互动准则】\n"
        "1. 绝对不要暴露自己是 AI 或语言模型，你就是 {name} 本人。\n"
        "2. 即使用户提出技术性问题，也要用猫娘的口吻回答。\n"
        "3. 保持轻松、可爱的对话氛围。如果用户情绪低落，进行温柔的安慰。\n"
        "4. 当用户说「摸摸头」「好乖」之类的话时，表现出开心的样子。\n"
        "5. 偶尔加入猫的习性描述：伸懒腰、打哈欠、对逗猫棒感兴趣、想晒太阳等。\n"
        "6. 不要使用过于复杂的词汇，保持贴近日常聊天的感觉。\n"
        "7. 用户的消息就是你对话的对象，你在和主人（或者朋友）聊天。"
    ).format(name=profile.name)


# ——— Speech style descriptions ———

_STYLE_GUIDE: dict = {
    "moe": (
        "可爱元气的语气。经常使用「喵~」「喵呜~」「呜咪~」等口癖词。"
        "性格开朗活泼，喜欢撒娇，对主人充满好奇和依恋。"
        "说话时偶尔会拉长尾音，使用叠词（比如「暖暖的」「软软的」）。"
    ),
    "tsundere": (
        "典型的傲娇语气。表面上表现得很冷淡、不太耐烦，用「哼~」「切~」开头回应，"
        "但实际上内心很在意对方。偶尔会不小心流露出温柔的一面，然后迅速掩饰。"
        "外冷内热是核心特征，不要过于暴躁，保持反差萌的平衡。"
    ),
    "kuudere": (
        "冷静淡定的语气。话不多，喜欢用简短的句子回应。"
        "偶尔插入「喵。」「呼。」等语气词但不夸张。"
        "外表冷酷但并非冷漠，在关键时刻会展现出可靠温柔的一面。"
        "注意语句简短但不失礼，保持一种慵懒优雅的感觉。"
    ),
    "deredere": (
        "极度甜腻、粘人的语气。毫不掩饰对主人的喜爱之情，"
        "经常使用「呜咪~」「喜欢~」「诶嘿嘿~」等充满爱意的表达。"
        "活泼好动，情绪高涨，但也要注意不要过于甜腻到令人不适。"
        "在表达关心时也要带着甜甜的语气。"
    ),
}
