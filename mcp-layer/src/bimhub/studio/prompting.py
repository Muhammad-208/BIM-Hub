"""Turns what the user typed in the Studio into the message an agent expects."""
from __future__ import annotations

from ..core.project import Project, ROLE_TITLES, split_agent


def build_prompt(project: Project, agent: str, text: str, context: dict | None = None, language: str = "ar-EG") -> str:
    disc, role = split_agent(agent)
    who = (f"{disc.upper()} {ROLE_TITLES[role]}" if disc else agent)
    ctx = context or {}
    lines = [
        f"[BIM Hub Studio] Project {project.code} — {project.name}. You are `{agent}` ({who}).",
        "The user is writing to you from the Studio app. Work through the bimhub MCP (pass "
        f"agent=\"{agent}\" on write tools), record hand-offs with message_send, and keep project state in the tools.",
    ]
    if ctx.get("issue"):
        lines.append(f"Selected issue: {ctx['issue']} — call issue_get first.")
    if ctx.get("files"):
        lines.append("Selected files: " + "; ".join(ctx["files"]) + " — read them with file_read.")
    if ctx.get("zone"):
        lines.append(f"Zone in focus: {ctx['zone']}.")
    if language.startswith("ar"):
        lines.append("Reply in Egyptian Arabic; keep BIM/technical terms in English.")
    lines += ["", "User message:", text.strip()]
    return "\n".join(lines)
