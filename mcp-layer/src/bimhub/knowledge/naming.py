"""ISO 19650 container-name validation driven by project.yaml → naming."""
from __future__ import annotations

import re
from pathlib import PurePath

FIELD = re.compile(r"\{(\w+)\}")


def validate_name(name: str, naming: dict, code: str) -> dict:
    stem = PurePath(name).stem if "." in name else name
    pattern = naming.get("pattern", "{project}-{originator}-{volume}-{level}-{type}-{role}-{number}")
    sep = naming.get("separator", "-")
    fields = FIELD.findall(pattern)
    parts = stem.split(sep)
    errors: list[str] = []
    if len(parts) != len(fields):
        errors.append(f"expected {len(fields)} fields ({sep.join(fields)}), found {len(parts)}")
        return {"name": name, "valid": False, "errors": errors}
    rules = naming.get("fields", {}) or {}
    for field, value in zip(fields, parts):
        rule = rules.get(field) or {}
        rx = rule.get("regex")
        if rx:
            rx = rx.replace("{{CODE}}", code)
            if not re.fullmatch(rx.strip("^$"), value):
                errors.append(f"{field}='{value}' does not match {rx}")
        vals = rule.get("values")
        if vals and value not in [str(v) for v in vals]:
            errors.append(f"{field}='{value}' not in {vals}")
    return {"name": name, "valid": not errors, "fields": dict(zip(fields, parts)), "errors": errors}
