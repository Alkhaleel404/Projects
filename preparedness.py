"""Session-local, non-sensitive preparedness checklist content."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChecklistItem:
    id: str
    phase: str
    title: str
    guidance: str


CHECKLIST = (
    ChecklistItem(
        "alerts",
        "Before heavy rain",
        "Turn on trusted weather and emergency alerts",
        "Follow current instructions from NYC Emergency Management and the National Weather Service.",
    ),
    ChecklistItem(
        "supplies",
        "Before heavy rain",
        "Gather water, a flashlight, batteries, and a charged power bank",
        "Keep essential supplies together and follow official guidance for your household.",
    ),
    ChecklistItem(
        "documents",
        "Before heavy rain",
        "Keep important documents in a dry, easy-to-reach place",
        "Use a sealed container or a secure digital copy where appropriate.",
    ),
    ChecklistItem(
        "pets",
        "Before heavy rain",
        "Plan for pets and service animals",
        "Include food, medication as directed by a veterinarian, identification, and a carrier.",
    ),
    ChecklistItem(
        "travel",
        "During heavy rain",
        "Check official alerts before traveling",
        "Delay nonessential trips when conditions are hazardous; street conditions can change quickly.",
    ),
    ChecklistItem(
        "water",
        "During heavy rain",
        "Stay out of floodwater",
        "Do not walk, swim, or drive through floodwater. It can hide hazards and move quickly.",
    ),
    ChecklistItem(
        "electrical",
        "During heavy rain",
        "Keep away from downed wires and electrical equipment in water",
        "Report immediate hazards to the appropriate authorities; do not approach or touch them.",
    ),
    ChecklistItem(
        "official",
        "After heavy rain",
        "Wait for official guidance before returning to affected areas",
        "Avoid floodwater and follow instructions from emergency services and city agencies.",
    ),
    ChecklistItem(
        "damage",
        "After heavy rain",
        "Report urgent hazards through official city channels",
        "Use NYC 311 for non-emergency service requests and 911 for immediate emergencies.",
    ),
)


def select_checklist_items(
    *,
    include_pets: bool = True,
    include_documents: bool = True,
    include_travel: bool = True,
) -> tuple[ChecklistItem, ...]:
    excluded: set[str] = set()
    if not include_pets:
        excluded.add("pets")
    if not include_documents:
        excluded.update(("documents", "supplies"))
    if not include_travel:
        excluded.add("travel")
    return tuple(item for item in CHECKLIST if item.id not in excluded)


def create_checklist_text(
    completed_ids: set[str],
    items: tuple[ChecklistItem, ...] = CHECKLIST,
) -> str:
    known_ids = {item.id for item in items}
    if not completed_ids.issubset(known_ids):
        raise ValueError("The checklist contains an unknown item.")
    lines = [
        "RainRoute NYC — personal preparedness checklist",
        "Follow current emergency instructions. Never enter floodwater.",
        "",
    ]
    for phase in dict.fromkeys(item.phase for item in items):
        lines.append(phase)
        for item in items:
            if item.phase == phase:
                mark = "[x]" if item.id in completed_ids else "[ ]"
                lines.append(f"{mark} {item.title} — {item.guidance}")
        lines.append("")
    return "\n".join(lines)
