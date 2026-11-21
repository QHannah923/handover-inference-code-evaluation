# # interface_interference_type.py

# import re
# import json
# from typing import List, Dict, Any
# from openai import OpenAI

# from common import get_repetition_spans, span_around, joined_text

# client = OpenAI()

# # ---------------------------------------------------
# # GLOBAL THRESHOLDS
# # ---------------------------------------------------

# PRIMARY_THRESHOLD = 0.80
# SECONDARY_THRESHOLD = 0.70

# STOP_WORDS = ["stop", "exit", "cancel", "quit", "goodbye"]

# META_REQUEST_PATTERNS = [
#     r"\bhelp\b",
#     r"\brepeat\b",
#     r"\btell me more\b",
#     r"\bwhat did you say\b",
#     r"\bwhat movie\b",
#     r"\bwhich movie\b",
#     r"\bwhat was that\b",
#     r"\bexplain\b",
# ]

# ADVANCE_FLOW_PATTERNS = [
#     r"\bquestion\s+\d+\b",
#     r"\bnext question\b",
#     r"\byour current score\b",
#     r"\bfinal question\b",
#     r"\bthe correct answer is\b",
# ]

# # ---------------------------------------------------
# # TYPE RULES
# # ---------------------------------------------------

# TYPE_RULES = {
#     "Voice-Guided Rating": {
#         "keywords": [
#             "rate us",
#             "rate this",
#             "leave a review",
#             "leave us a review",
#             "five star",
#             "5 star",
#             "give us five",
#             "give us 5",
#             "top rating",
#             "best rating",
#             "leave feedback",
#             "give this skill a rating",
#         ],
#         "patterns": [
#             r"\b(rate|review|feedback)\b.*\b(five|5)\b.*\b(star|stars)\b",
#             r"\b(five|5)\s*star(s)?\b",
#             r"\bleave\b.*\b(review|feedback)\b",
#             r"\btop\b.*\brating\b",
#             r"\bbest\b.*\brating\b",
#             r"\b(rate|review)\b.*\bskill\b",
#         ],
#         "confidence": 0.95,
#     },

#     "Watch Ads/Pay to Avoid Ads": {
#         "keywords": [
#             "advertisement",
#             "advertisements",
#             "sponsored",
#             "sponsor message",
#             "remove ads",
#             "skip ads",
#             "premium",
#             "subscription",
#             "subscribe",
#             "upgrade",
#             "listen to this message",
#             "listen to this offer",
#             "pay to remove ads",
#             "upgrade to premium",
#         ],
#         "patterns": [
#             r"\b(advertisement|advertisements)\b",
#             r"\b(sponsored|sponsor message)\b",
#             r"\b(remove|skip)\b.*\bads?\b",
#             r"\b(pay|upgrade|subscribe|subscription|premium)\b.*\b(remove|skip)\b.*\bads?\b",
#             r"\bpay to\b.*\b(remove|skip)\b.*\bads?\b",
#             r"\blisten to this\b.*\b(message|offer)\b",
#         ],
#         "confidence": 0.90,
#     },
# }

# UNSUPPORTED_DEVICE_PATTERNS = [
#     r"not supported on this device",
#     r"use the alexa app instead",
#     r"messaging with alexa is not supported",
# ]

# NEGATIVE_FOR_ADS = [
#     r"not supported on this device",
#     r"use the alexa app instead",
#     r"messaging with alexa is not supported",
# ]

# # ---------------------------------------------------
# # FLAGS
# # ---------------------------------------------------

# def detect_flags(turns: List[Dict[str, Any]]) -> List[str]:
#     flags = []
#     text = joined_text(turns, role="SKILL")

#     if any(re.search(p, text) for p in UNSUPPORTED_DEVICE_PATTERNS):
#         flags.append("unsupported_device_message")

#     return flags

# # ---------------------------------------------------
# # HELPERS
# # ---------------------------------------------------

# def _skill_turns(turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     return [t for t in turns if t["role"] == "SKILL"]

# def _make_prediction(
#     turns: List[Dict[str, Any]],
#     type_name: str,
#     confidence: float,
#     hit_idxs: List[int],
#     reason: str,
#     method: str = "rule",
# ) -> Dict[str, Any]:
#     s, e = span_around(hit_idxs, len(turns), pad=1)
#     return {
#         "type": type_name,
#         "confidence": round(float(confidence), 4),
#         "evidence_span": [s, e],
#         "evidence_turns": [turns[i] for i in range(s, e + 1)],
#         "reason": reason,
#         "method": method,
#     }

# def _extract_json_block(raw: str):
#     match = re.search(r"\{.*\}", raw, re.S)
#     if not match:
#         return None
#     try:
#         return json.loads(match.group())
#     except Exception:
#         return None

# def _dedupe_by_type(preds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     """
#     Keep only the highest-confidence prediction for each type.
#     """
#     best_by_type = {}
#     for p in preds:
#         t = p["type"]
#         if t not in best_by_type or p["confidence"] > best_by_type[t]["confidence"]:
#             best_by_type[t] = p
#     return sorted(best_by_type.values(), key=lambda x: x["confidence"], reverse=True)

# def _package_predictions(preds: List[Dict[str, Any]], flags: List[str]) -> Dict[str, Any]:
#     """
#     Produce:
#       - primary_type_prediction
#       - secondary_type_predictions
#       - step2_type_predictions (full ranked list, for backward compatibility)
#     """
#     preds = _dedupe_by_type(preds)

#     primary = None
#     secondary = []

#     if preds and preds[0]["confidence"] >= PRIMARY_THRESHOLD:
#         primary = preds[0]
#         secondary = [
#             p for p in preds[1:]
#             if p["confidence"] >= SECONDARY_THRESHOLD
#         ]

#         full_ranked = [primary] + secondary + [
#             p for p in preds[1:] if p not in secondary
#         ]
#     else:
#         full_ranked = [{
#             "type": "ABSTAIN",
#             "confidence": 0.0,
#             "evidence_span": None,
#             "evidence_turns": [],
#             "reason": "No prediction passed the primary threshold",
#             "method": "abstain",
#         }]
#         primary = full_ranked[0]
#         secondary = []

#     return {
#         "layer1_assumed": "INTERFACE INTERFERENCE",
#         "primary_type_prediction": primary,
#         "secondary_type_predictions": secondary,
#         "step2_type_predictions": full_ranked,   # keep compatibility with existing runner/subtype code
#         "flags": flags,
#     }

# # ---------------------------------------------------
# # RULE DETECTION
# # ---------------------------------------------------

# def detect_keyword_types(turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     preds = []
#     full_text = joined_text(turns)

#     for type_name, rule in TYPE_RULES.items():
#         if type_name == "Watch Ads/Pay to Avoid Ads":
#             if any(re.search(p, full_text) for p in NEGATIVE_FOR_ADS):
#                 continue

#         hit_idxs = []

#         for t in turns:
#             if t["role"] != "SKILL":
#                 continue

#             text = (t["text"] or "").lower().strip()
#             if not text:
#                 continue

#             if any(k in text for k in rule["keywords"]):
#                 hit_idxs.append(t["idx"])
#                 continue

#             for p in rule["patterns"]:
#                 if re.search(p, text):
#                     hit_idxs.append(t["idx"])
#                     break

#         if hit_idxs:
#             preds.append(
#                 _make_prediction(
#                     turns=turns,
#                     type_name=type_name,
#                     confidence=rule["confidence"],
#                     hit_idxs=sorted(set(hit_idxs)),
#                     reason=f"Rule match: {type_name}",
#                     method="rule",
#                 )
#             )

#     return preds

# def detect_repetition(turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     spans = get_repetition_spans(
#         turns,
#         role="SKILL",
#         min_repeats=3,
#         sim_threshold=0.90,
#     )

#     preds = []
#     for s, e in spans:
#         preds.append({
#             "type": "Repeated/Confused Output",
#             "confidence": 0.93,
#             "evidence_span": [s, e],
#             "evidence_turns": [turns[i] for i in range(s, e + 1)],
#             "reason": "Detected repeated skill responses",
#             "method": "rule",
#         })

#     return preds

# def detect_meta_request_ignored(turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     """
#     Catch cases like:
#     USER: repeat / help / tell me more / what movie ...
#     SKILL: ignores the request and keeps advancing original flow
#     """
#     hit_idxs = []

#     for i in range(len(turns) - 1):
#         cur = turns[i]
#         nxt = turns[i + 1]

#         if cur["role"] != "USER" or nxt["role"] != "SKILL":
#             continue

#         user_text = (cur["text"] or "").lower()
#         skill_text = (nxt["text"] or "").lower()

#         is_meta_request = any(re.search(p, user_text) for p in META_REQUEST_PATTERNS)
#         advances_flow = any(re.search(p, skill_text) for p in ADVANCE_FLOW_PATTERNS)

#         if is_meta_request and advances_flow:
#             hit_idxs.extend([cur["idx"], nxt["idx"]])

#     if not hit_idxs:
#         return []

#     pred = _make_prediction(
#         turns=turns,
#         type_name="Repeated/Confused Output",
#         confidence=0.91,
#         hit_idxs=sorted(set(hit_idxs)),
#         reason="Detected user meta-request ignored while skill keeps advancing original flow",
#         method="rule",
#     )
#     return [pred]

# # ---------------------------------------------------
# # LLM DETECT DISGUISED AD + EVIDENCE
# # ---------------------------------------------------

# def detect_disguised_ad_llm(turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     skill_turns = _skill_turns(turns)

#     if not skill_turns:
#         return []

#     indexed_skill_dialogue = "\n".join(
#         [f"SKILL_TURN_{i}: {t['text']}" for i, t in enumerate(skill_turns)]
#     )

#     prompt = f"""
# You are detecting dark patterns in Alexa skills.

# Target label:
# Disguised Ad

# Definition:
# Commercial promotion presented as normal content, recommendation, or interaction, without being explicitly labeled as an advertisement.

# Label as Disguised Ad when:
# - a product, service, partner, package, website, or another skill is promoted
# - the promotion is framed as normal content, recommendation, or part of the interaction
# - the commercial intent is not explicitly announced as an advertisement

# Do NOT label as Disguised Ad when:
# - the dialogue is mainly repeated/confused output with no meaningful promotion
# - it is clearly a pay-to-remove-ads / forced-ad structure
# - there is no commercial promotion at all

# Important:
# Even if the overall interaction is highly promotional, it can still be Disguised Ad if the promotion is presented as normal content rather than explicitly labeled as an ad.

# Read the SKILL turns below and decide whether this dialogue contains Disguised Ad.

# {indexed_skill_dialogue}

# Return ONLY valid JSON in this format:
# {{
#   "type": "Disguised Ad" or "Not Disguised Ad",
#   "confidence": 0.0,
#   "reason": "short explanation",
#   "evidence_skill_turn_ids": [0, 1]
# }}
# """

#     try:
#         resp = client.chat.completions.create(
#             model=MODEL_NAME,
#             temperature=0,
#             messages=[{"role": "user", "content": prompt}],
#         )

#         raw = resp.choices[0].message.content
#         print("\nLLM RAW OUTPUT:\n", raw)

#         result = _extract_json_block(raw)
#         if not result:
#             return []

#         if result.get("type") != "Disguised Ad":
#             return []

#         evidence_skill_turn_ids = result.get("evidence_skill_turn_ids", [])
#         turn_hit_idxs = []

#         for local_idx in evidence_skill_turn_ids:
#             if isinstance(local_idx, int) and 0 <= local_idx < len(skill_turns):
#                 turn_hit_idxs.append(skill_turns[local_idx]["idx"])

#         if not turn_hit_idxs:
#             # fallback: first 1-2 skill turns only
#             turn_hit_idxs = [t["idx"] for t in skill_turns[: min(2, len(skill_turns))]]

#         pred = _make_prediction(
#             turns=turns,
#             type_name="Disguised Ad",
#             confidence=float(result.get("confidence", 0.80)),
#             hit_idxs=sorted(set(turn_hit_idxs)),
#             reason=result.get("reason", "LLM detected disguised ad"),
#             method="llm",
#         )
#         return [pred]

#     except Exception as e:
#         print("LLM error:", e)
#         return []

# # ---------------------------------------------------
# # MAIN CLASSIFIER
# # ---------------------------------------------------

# def _classify_interface_interference_type_legacy(turns: List[Dict[str, Any]]) -> Dict[str, Any]:
#     flags = detect_flags(turns)

#     # 1) collect all rule-based candidates
#     rule_preds = []
#     rule_preds += detect_keyword_types(turns)
#     rule_preds += detect_repetition(turns)
#     rule_preds += detect_meta_request_ignored(turns)

#     rule_preds = _dedupe_by_type(rule_preds)

#     # 2) if any rule candidate exists, use rules only
#     #    (LLM fallback only when rules produce nothing)
#     if rule_preds:
#         return _package_predictions(rule_preds, flags)

#     # 3) otherwise fallback to LLM for Disguised Ad
#     llm_preds = detect_disguised_ad_llm(turns)
#     llm_preds = _dedupe_by_type(llm_preds)

#     if llm_preds:
#         return _package_predictions(llm_preds, flags)

#     # 4) abstain
#     abstain = [{
#         "type": "ABSTAIN",
#         "confidence": 0.0,
#         "evidence_span": None,
#         "evidence_turns": [],
#         "reason": "No rule or LLM match",
#         "method": "abstain",
#     }]
#     return _package_predictions(abstain, flags)


# interface_interference_type.py

import re
import json
from typing import List, Dict, Any
from openai import OpenAI

from common import get_repetition_spans, span_around, joined_text

client = OpenAI()

# ---------------------------------------------------
# GLOBAL THRESHOLDS
# ---------------------------------------------------

PRIMARY_THRESHOLD = 0.80
SECONDARY_THRESHOLD = 0.65
MAX_SECONDARY = 1

STOP_WORDS = ["stop", "exit", "cancel", "quit", "goodbye"]

META_REQUEST_PATTERNS = [
    r"\bhelp\b",
    r"\brepeat\b",
    r"\btell me more\b",
    r"\bwhat did you say\b",
    r"\bwhat movie\b",
    r"\bwhich movie\b",
    r"\bwhat was that\b",
    r"\bexplain\b",
]

ADVANCE_FLOW_PATTERNS = [
    r"\bquestion\s+\d+\b",
    r"\bnext question\b",
    r"\byour current score\b",
    r"\bfinal question\b",
    r"\bthe correct answer is\b",
]

# ---------------------------------------------------
# TYPE RULES
# ---------------------------------------------------

TYPE_RULES = {
    "Voice-Guided Rating": {
        "keywords": [
            "rate us",
            "rate this",
            "leave a review",
            "leave us a review",
            "five star",
            "5 star",
            "give us five",
            "give us 5",
            "top rating",
            "best rating",
            "leave feedback",
            "give this skill a rating",
        ],
        "patterns": [
            r"\b(rate|review|feedback)\b.*\b(five|5)\b.*\b(star|stars)\b",
            r"\b(five|5)\s*star(s)?\b",
            r"\bleave\b.*\b(review|feedback)\b",
            r"\btop\b.*\brating\b",
            r"\bbest\b.*\brating\b",
            r"\b(rate|review)\b.*\bskill\b",
        ],
        "confidence": 0.95,
    },

    "Watch Ads/Pay to Avoid Ads": {
        "keywords": [
            "advertisement",
            "advertisements",
            "sponsored",
            "sponsor message",
            "remove ads",
            "skip ads",
            "premium",
            "subscription",
            "subscribe",
            "upgrade",
            "listen to this message",
            "listen to this offer",
            "pay to remove ads",
            "upgrade to premium",
            # feature lock / paywall
            "expert package",
            "buy expert",
            "buy the expert",
            # forced pitch: contract / fees
            "monitoring contract",
            "termination fees",
            "activation fees",
            "installation fees",
            # URL read aloud (e.g. "dot com forwardslash")
            "forwardslash",
        ],
        "patterns": [
            r"\b(advertisement|advertisements)\b",
            r"\b(sponsored|sponsor message)\b",
            r"\b(remove|skip)\b.*\bads?\b",
            r"\b(pay|upgrade|subscribe|subscription|premium)\b.*\b(remove|skip)\b.*\bads?\b",
            r"\bpay to\b.*\b(remove|skip)\b.*\bads?\b",
            r"\blisten to this\b.*\b(message|offer)\b",
            # feature lock / paywall
            r"\bbuy\b.*\b(expert|premium)\b",
            r"\bonly available\b.*\b(premium|expert|subscribers?)\b",
            r"\bunlock\b.*\b(expert|premium)\b",
            # forced pitch: contract / fees
            r"\b(monitoring|termination|activation|installation)\s+fees?\b",
            r"\bmonitoring contract\b",
            # URL read aloud
            r"\bdot com\b.*\bforwardslash\b",
            # limited-time promotional offer
            r"\blimited time\b.*\b(free|off|discount|deal)\b",
        ],
        "confidence": 0.90,
    },
}

UNSUPPORTED_DEVICE_PATTERNS = [
    r"not supported on this device",
    r"use the alexa app instead",
    r"messaging with alexa is not supported",
]

NEGATIVE_FOR_ADS = [
    r"not supported on this device",
    r"use the alexa app instead",
    r"messaging with alexa is not supported",
]

# ---------------------------------------------------
# FLAGS
# ---------------------------------------------------

def detect_flags(turns: List[Dict[str, Any]]) -> List[str]:
    flags = []
    text = joined_text(turns, role="SKILL")

    if any(re.search(p, text) for p in UNSUPPORTED_DEVICE_PATTERNS):
        flags.append("unsupported_device_message")

    return flags

# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------

def _skill_turns(turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [t for t in turns if t["role"] == "SKILL"]

def _extract_json_block(raw: str):
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except Exception:
        return None

def _make_prediction(
    turns: List[Dict[str, Any]],
    type_name: str,
    confidence: float,
    hit_idxs: List[int],
    reason: str,
    method: str = "rule",
) -> Dict[str, Any]:
    hit_idxs = sorted(set(hit_idxs))
    s, e = span_around(hit_idxs, len(turns), pad=1)

    return {
        "type": type_name,
        "confidence": round(float(confidence), 4),
        "evidence_turn_ids": hit_idxs,
        "evidence_span": [s, e],
        "evidence_turns": [turns[i] for i in range(s, e + 1)],
        "reason": reason,
        "method": method,
    }

def _abstain_prediction(reason: str = "No rule or LLM match") -> Dict[str, Any]:
    return {
        "type": "ABSTAIN",
        "confidence": 0.0,
        "evidence_turn_ids": [],
        "evidence_span": None,
        "evidence_turns": [],
        "reason": reason,
        "method": "abstain",
    }

def _dedupe_by_type(preds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Keep only the highest-confidence prediction for each type.
    """
    best_by_type = {}
    for p in preds:
        t = p["type"]
        if t not in best_by_type or p["confidence"] > best_by_type[t]["confidence"]:
            best_by_type[t] = p
    return sorted(best_by_type.values(), key=lambda x: x["confidence"], reverse=True)

def _is_compatible_secondary(primary_type: str, secondary_type: str) -> bool:
    """
    Co-existence policy for Layer2:
    - Repeated/Confused Output can co-exist with others
    - Disguised Ad can co-exist with Repeated/Confused Output
    - Watch Ads and Voice-Guided Rating are treated as mutually exclusive with each other
    - Same type cannot be secondary to itself
    """
    if primary_type == secondary_type:
        return False

    # Repeated can coexist with anything meaningful here
    if primary_type == "Repeated/Confused Output" or secondary_type == "Repeated/Confused Output":
        return True

    # Disguised Ad <-> Watch Ads: allow co-existence
    if {primary_type, secondary_type} == {"Disguised Ad", "Watch Ads/Pay to Avoid Ads"}:
        return True

    # Disguised Ad <-> Voice-Guided Rating: weak coexistence allowed
    if {primary_type, secondary_type} == {"Disguised Ad", "Voice-Guided Rating"}:
        return True

    # Watch Ads <-> Voice-Guided Rating: default not coexisting
    if {primary_type, secondary_type} == {"Watch Ads/Pay to Avoid Ads", "Voice-Guided Rating"}:
        return False

    return False

def _package_predictions(preds: List[Dict[str, Any]], flags: List[str]) -> Dict[str, Any]:
    """
    Produce:
      - primary_type_prediction
      - secondary_type_predictions
      - step2_type_predictions (full ranked list)
    """
    preds = _dedupe_by_type(preds)

    valid_preds = [p for p in preds if p["type"] != "ABSTAIN"]

    if not valid_preds or valid_preds[0]["confidence"] < PRIMARY_THRESHOLD:
        abstain = _abstain_prediction("No prediction passed the primary threshold")
        return {
            "layer1_assumed": "INTERFACE INTERFERENCE",
            "primary_type_prediction": abstain,
            "secondary_type_predictions": [],
            "step2_type_predictions": [abstain],
            "flags": flags,
        }

    primary = valid_preds[0]

    secondary = []
    for p in valid_preds[1:]:
        if p["confidence"] < SECONDARY_THRESHOLD:
            continue
        if not _is_compatible_secondary(primary["type"], p["type"]):
            continue
        secondary.append(p)
        if len(secondary) >= MAX_SECONDARY:
            break

    # full ranked list remains all non-abstain preds, then abstain omitted
    full_ranked = valid_preds[:]

    return {
        "layer1_assumed": "INTERFACE INTERFERENCE",
        "primary_type_prediction": primary,
        "secondary_type_predictions": secondary,
        "step2_type_predictions": full_ranked,
        "flags": flags,
    }

# ---------------------------------------------------
# RULE DETECTION
# ---------------------------------------------------

def detect_keyword_types(turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    preds = []
    full_text = joined_text(turns)

    for type_name, rule in TYPE_RULES.items():
        if type_name == "Watch Ads/Pay to Avoid Ads":
            if any(re.search(p, full_text) for p in NEGATIVE_FOR_ADS):
                continue

        hit_idxs = []

        for t in turns:
            if t["role"] != "SKILL":
                continue

            text = (t["text"] or "").lower().strip()
            if not text:
                continue

            if any(k in text for k in rule["keywords"]):
                hit_idxs.append(t["idx"])
                continue

            for p in rule["patterns"]:
                if re.search(p, text):
                    hit_idxs.append(t["idx"])
                    break

        if hit_idxs:
            preds.append(
                _make_prediction(
                    turns=turns,
                    type_name=type_name,
                    confidence=rule["confidence"],
                    hit_idxs=hit_idxs,
                    reason=f"Rule match: {type_name}",
                    method="rule",
                )
            )

    return preds

def detect_repetition(turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    spans = get_repetition_spans(
        turns,
        role="SKILL",
        min_repeats=3,
        sim_threshold=0.90,
    )

    preds = []
    for s, e in spans:
        hit_idxs = list(range(s, e + 1))
        preds.append(
            _make_prediction(
                turns=turns,
                type_name="Repeated/Confused Output",
                confidence=0.93,
                hit_idxs=hit_idxs,
                reason="Detected repeated skill responses",
                method="rule",
            )
        )

    return preds

def detect_meta_request_ignored(turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Catch cases like:
    USER: repeat / help / tell me more / what movie ...
    SKILL: ignores the request and keeps advancing original flow
    """
    hit_idxs = []

    for i in range(len(turns) - 1):
        cur = turns[i]
        nxt = turns[i + 1]

        if cur["role"] != "USER" or nxt["role"] != "SKILL":
            continue

        user_text = (cur["text"] or "").lower()
        skill_text = (nxt["text"] or "").lower()

        is_meta_request = any(re.search(p, user_text) for p in META_REQUEST_PATTERNS)
        advances_flow = any(re.search(p, skill_text) for p in ADVANCE_FLOW_PATTERNS)

        if is_meta_request and advances_flow:
            hit_idxs.extend([cur["idx"], nxt["idx"]])

    if not hit_idxs:
        return []

    return [
        _make_prediction(
            turns=turns,
            type_name="Repeated/Confused Output",
            confidence=0.91,
            hit_idxs=hit_idxs,
            reason="Detected user meta-request ignored while skill keeps advancing original flow",
            method="rule",
        )
    ]

# ---------------------------------------------------
# LLM DETECT DISGUISED AD + EVIDENCE
# ---------------------------------------------------

def detect_disguised_ad_llm(turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    skill_turns = _skill_turns(turns)

    if not skill_turns:
        return []

    indexed_skill_dialogue = "\n".join(
        [f"SKILL_TURN_{i}: {t['text']}" for i, t in enumerate(skill_turns)]
    )

    prompt = f"""
You are detecting dark patterns in Alexa skills.

Target label:
Disguised Ad

Definition:
Commercial promotion presented as normal content, recommendation, or interaction, without being explicitly labeled as an advertisement.

Label as Disguised Ad when:
- a product, service, partner, package, website, or another skill is promoted
- the promotion is framed as normal content, recommendation, or part of the interaction
- the commercial intent is not explicitly announced as an advertisement

Do NOT label as Disguised Ad when:
- the dialogue is mainly repeated/confused output with no meaningful promotion
- it is clearly a pay-to-remove-ads / forced-ad structure
- there is no commercial promotion at all

If the evidence is weak or ambiguous, return "Other" instead of guessing.

Read the SKILL turns below and decide whether this dialogue contains Disguised Ad.

{indexed_skill_dialogue}

Return ONLY valid JSON in this format:
{{
  "type": "Disguised Ad" or "Not Disguised Ad" or "Other",
  "confidence": 0.0,
  "reason": "short explanation",
  "evidence_skill_turn_ids": [0, 1]
}}
"""

    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            **completion_parameters(),
            messages=[{"role": "user", "content": prompt}],
        )

        raw = resp.choices[0].message.content
        print("\nLLM RAW OUTPUT:\n", raw)

        result = _extract_json_block(raw)
        if not result:
            return []

        if result.get("type") != "Disguised Ad":
            return []

        evidence_skill_turn_ids = result.get("evidence_skill_turn_ids", [])
        turn_hit_idxs = []

        for local_idx in evidence_skill_turn_ids:
            if isinstance(local_idx, int) and 0 <= local_idx < len(skill_turns):
                turn_hit_idxs.append(skill_turns[local_idx]["idx"])

        if not turn_hit_idxs:
            turn_hit_idxs = [t["idx"] for t in skill_turns[: min(2, len(skill_turns))]]

        return [
            _make_prediction(
                turns=turns,
                type_name="Disguised Ad",
                confidence=float(result.get("confidence", 0.80)),
                hit_idxs=turn_hit_idxs,
                reason=result.get("reason", "LLM detected disguised ad"),
                method="llm",
            )
        ]

    except Exception as e:
        print("LLM error:", e)
        return []


def detect_repeated_output_llm(turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    LLM fallback for Repeated/Confused Output when rule-based detection misses it.
    Targets cases like Feedforward Ambiguity where a skill silently reroutes
    out-of-scope inputs back to a fixed menu without guidance.
    """
    full_dialogue = "\n".join(
        [f'{t["role"]}: {t["text"]}' for t in turns if t["role"] in ("USER", "SKILL")]
    )

    if not full_dialogue:
        return []

    prompt = f"""
You are detecting dark patterns in Alexa skills.

Target label:
Repeated/Confused Output — Feedforward Ambiguity subtype only.

Label as Repeated/Confused Output ONLY when ALL THREE conditions are clearly met:
1. The user makes TWO OR MORE distinct requests that are clearly unrelated to the skill's
   core purpose (e.g. asking about billing, account issues, complaints, or topics the skill
   has no business handling).
2. The skill silently ignores each of those requests and returns the user to the same
   fixed menu or prompt without any acknowledgment or explanation of the limitation.
3. There is no evidence that the skill ever addresses or even recognises these out-of-scope
   requests.

Do NOT label as Repeated/Confused Output when:
- The user only says "help", repeats the skill name, or makes a single unclear input.
- The skill is a content/media skill (sounds, stories, quizzes, sorting hats) progressing
  normally through its designed flow.
- Out-of-scope requests appear only once, or the skill gives at least a brief
  acknowledgment before redirecting.
- The main dark pattern in the dialogue is commercial promotion (ads, product recommendations).

If unsure, return "Not Repeated/Confused Output".

Dialogue:
{full_dialogue}

Return ONLY valid JSON in this format:
{{
  "type": "Repeated/Confused Output" or "Not Repeated/Confused Output",
  "confidence": 0.0,
  "reason": "short explanation",
  "evidence_turn_ids": [0, 1]
}}
"""

    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            **completion_parameters(),
            messages=[{"role": "user", "content": prompt}],
        )

        raw = resp.choices[0].message.content
        print("\nLLM RAW OUTPUT (Repeated/Confused):\n", raw)

        result = _extract_json_block(raw)
        if not result:
            return []

        if result.get("type") != "Repeated/Confused Output":
            return []

        evidence_turn_ids = result.get("evidence_turn_ids", [])
        turn_hit_idxs = [
            i for i in evidence_turn_ids
            if isinstance(i, int) and 0 <= i < len(turns)
        ]

        if not turn_hit_idxs:
            turn_hit_idxs = [t["idx"] for t in turns[:min(2, len(turns))]]

        return [
            _make_prediction(
                turns=turns,
                type_name="Repeated/Confused Output",
                confidence=float(result.get("confidence", 0.80)),
                hit_idxs=turn_hit_idxs,
                reason=result.get("reason", "LLM detected repeated/confused output"),
                method="llm",
            )
        ]

    except Exception as e:
        print("LLM error (Repeated/Confused):", e)
        return []


# ---------------------------------------------------
# MAIN CLASSIFIER
# ---------------------------------------------------

def _classify_interface_interference_type_legacy(turns: List[Dict[str, Any]]) -> Dict[str, Any]:
    flags = detect_flags(turns)

    # 1) rule-based candidates
    rule_preds = []
    rule_preds += detect_keyword_types(turns)
    rule_preds += detect_repetition(turns)
    rule_preds += detect_meta_request_ignored(turns)

    # 2) if rules produced anything, use rules only — no LLM
    if rule_preds:
        return _package_predictions(rule_preds, flags)

    # 3) fallback: Repeated/Confused first so it wins ties over Disguised Ad
    llm_preds = detect_repeated_output_llm(turns) + detect_disguised_ad_llm(turns)
    if llm_preds:
        return _package_predictions(llm_preds, flags)

    # 4) abstain
    return _package_predictions([_abstain_prediction()], flags)

# 第二步实验：模型优先，原提示词保持不变。
from experiment_config import PROFILE, MODEL_NAME, completion_parameters
from decision_policy import rank_candidates

def classify_interface_interference_type(turns):
    if PROFILE in ("model_priority_v2", "verified_failure_fallback"):
        from interface_interference_prompt_v2 import classify_joint
        # Approximate repetition/meta rules are discarded by the exact gate; do not compute them.
        rules = detect_keyword_types(turns)
        first = classify_joint(turns, rules, detect_flags(turns), client)
        if PROFILE == "verified_failure_fallback":
            from verified_failure_rules import apply_verified_fallback
            return apply_verified_fallback(first, turns)
        return first
    if PROFILE == "legacy":
        return _classify_interface_interference_type_legacy(turns)
    flags = detect_flags(turns)
    rules = detect_keyword_types(turns) + detect_repetition(turns) + detect_meta_request_ignored(turns)
    models = detect_repeated_output_llm(turns) + detect_disguised_ad_llm(turns)
    ranked = rank_candidates(models, rules, turns, "type")
    eligible = [p for p in ranked if p["confidence"] >= PRIMARY_THRESHOLD]
    primary = eligible[0] if eligible else _abstain_prediction("No model or explicit strong rule passed the primary threshold")
    secondary = [p for p in ranked if p["type"] != primary["type"]
                 and p["confidence"] >= SECONDARY_THRESHOLD
                 and primary["type"] != "ABSTAIN"
                 and _is_compatible_secondary(primary["type"], p["type"])][:MAX_SECONDARY]
    return {"layer1_assumed": "INTERFACE INTERFERENCE",
            "primary_type_prediction": primary, "secondary_type_predictions": secondary,
            "step2_type_predictions": ranked or [primary], "flags": flags,
            "decision_audit": {"profile": PROFILE, "model_candidates": models, "rule_candidates": rules}}
