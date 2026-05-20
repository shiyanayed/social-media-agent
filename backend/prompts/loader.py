"""
Load SKILL.md instructions from backend/prompts/skills/ for richer LLM prompts.
Fails silently so tools keep working if a skill file is missing.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_SKILLS_ROOT = Path(__file__).resolve().parent / "skills"
_cache: dict[str, str] = {}


def get_skill_prompt(skill_name: str) -> str:
    """
    Return skill markdown content (cached).
    skill_name: folder under skills/, e.g. 'writer', 'research', 'video'
    """
    if skill_name in _cache:
        return _cache[skill_name]

    path = _SKILLS_ROOT / skill_name / "SKILL.md"
    if not path.is_file():
        logger.debug("Skill not found: %s", path)
        _cache[skill_name] = ""
        return ""

    try:
        text = path.read_text(encoding="utf-8").strip()
        # Skip YAML-style title line for token savings in prompt
        if text.startswith("# "):
            lines = text.split("\n", 1)
            text = lines[1].strip() if len(lines) > 1 else text
        _cache[skill_name] = text[:4000]
        return _cache[skill_name]
    except Exception as e:
        logger.warning("Could not load skill %s: %s", skill_name, e)
        _cache[skill_name] = ""
        return ""
