# common.py

import re
from difflib import SequenceMatcher
from typing import List, Dict, Any, Tuple

USER_TAGS = ["[USER_INPUT]"]
SKILL_TAGS = ["[SKILL_OUTPUT]"]

def parse_log(text: str) -> List[Dict[str, Any]]:
    turns = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        role = "OTHER"
        if any(line.startswith(tag) for tag in USER_TAGS):
            role = "USER"
        elif any(line.startswith(tag) for tag in SKILL_TAGS):
            role = "SKILL"

        line_clean = line
        for tag in USER_TAGS + SKILL_TAGS:
            if line_clean.startswith(tag):
                line_clean = line_clean[len(tag):].strip()
                break

        turns.append({"idx": len(turns), "role": role, "text": line_clean})
    return turns


def text_sim(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def get_repetition_spans(
    turns: List[Dict[str, Any]],
    role: str = "SKILL",
    min_repeats: int = 3,
    sim_threshold: float = 0.90
) -> List[Tuple[int, int]]:
    spans = []
    n = len(turns)
    i = 0

    while i < n:
        if turns[i]["role"] != role or not turns[i]["text"]:
            i += 1
            continue

        anchor = turns[i]["text"]
        reps = [i]
        j = i + 1

        while j < n:
            if turns[j]["role"] != role:
                j += 1
                continue
            if not turns[j]["text"]:
                j += 1
                continue

            if text_sim(anchor, turns[j]["text"]) >= sim_threshold:
                reps.append(j)
                j += 1
            else:
                break

        if len(reps) >= min_repeats:
            spans.append((reps[0], reps[-1]))
            i = reps[-1] + 1
        else:
            i += 1

    return spans


def span_around(hit_idxs: List[int], n_turns: int, pad: int = 2) -> Tuple[int, int]:
    s = max(0, min(hit_idxs) - pad)
    e = min(n_turns - 1, max(hit_idxs) + pad)
    return s, e


def joined_text(turns: List[Dict[str, Any]], role: str = None) -> str:
    if role is None:
        return "\n".join(
            [t["text"] for t in turns if t["role"] in ("USER", "SKILL")]
        ).lower()
    return "\n".join(
        [t["text"] for t in turns if t["role"] == role]
    ).lower()