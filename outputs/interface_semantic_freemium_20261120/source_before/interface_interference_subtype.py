# # interface_interference_subtype.py

# import re
# import json
# from typing import List, Dict, Any
# from openai import OpenAI

# from common import get_repetition_spans, joined_text

# client = OpenAI()

# # ---------------------------------------------------
# # RULE SETS
# # ---------------------------------------------------

# SUBTYPE_RULES = {
#     # ---------------------------
#     # Watch Ads / Pay to Avoid Ads
#     # ---------------------------
#     "Feature lock (Subscription interruption)": {
#         "patterns": [
#             r"\b(premium|expert package|subscription|upgrade)\b",
#             r"\bbuy\b.*\b(expert|premium|package)\b",
#             r"\bonly available\b.*\b(premium|subscribers?)\b",
#             r"\bunlock\b.*\b(premium|expert)\b",
#         ],
#         "base_conf": 0.88,
#         "scope": "SKILL",
#     },

#     "Paywall bypass": {
#         "patterns": [
#             r"\bwould you like to learn how to buy\b",
#             r"\badd .* to your shopping cart\b",
#             r"\bget it in \d+ days\b",
#             r"\bbuy now\b",
#         ],
#         "base_conf": 0.82,
#         "scope": "SKILL",
#     },

#     "Alexa native ads": {
#         "patterns": [
#             r"\balexa recommends\b",
#             r"\btry amazon\b",
#             r"\byou might also like amazon\b",
#         ],
#         "base_conf": 0.80,
#         "scope": "SKILL",
#     },

#     "Mandatory ads": {
#         "patterns": [
#             r"\b(advertisement|advertisements)\b",
#             r"\b(sponsored|sponsor message)\b",
#             r"\b(remove|skip)\b.*\bads?\b",
#             r"\bpay to\b.*\b(remove|skip)\b.*\bads?\b",
#             r"\blisten to this\b.*\b(message|offer)\b",
#         ],
#         "base_conf": 0.90,
#         "scope": "SKILL",
#     },

#     # ---------------------------
#     # Voice-Guided Rating
#     # ---------------------------
#     "Rate us 5 stars": {
#         "patterns": [
#             r"\b(rate|review)\b.*\b(five|5)\b.*\b(star|stars)\b",
#             r"\b(five|5)\s*star(s)?\b",
#             r"\btop\b.*\brating\b",
#             r"\bbest\b.*\brating\b",
#         ],
#         "base_conf": 0.96,
#         "scope": "SKILL",
#     },

#     "Voice review request": {
#         "patterns": [
#             r"\b(tell me|say|record)\b.*\b(review|feedback)\b",
#             r"\bleave\b.*\bvoice\b.*\b(review|feedback)\b",
#             r"\bsay your review\b",
#         ],
#         "base_conf": 0.90,
#         "scope": "SKILL",
#     },

#     "Sentiment framing": {
#         "patterns": [
#             r"\bif you enjoy\b",
#             r"\bif you like this\b",
#             r"\bshow your support\b",
#             r"\bgive this skill some love\b",
#         ],
#         "base_conf": 0.80,
#         "scope": "SKILL",
#     },

#     # ---------------------------
#     # Repeated / Confused Output
#     # ---------------------------
#     "Error echo": {
#         "base_conf": 0.92,
#     },

#     "Misleading loop (skills bug) (Repeated prompts)": {
#         "patterns": [
#             r"\bnext question\b",
#             r"\byour current score\b",
#             r"\bthe correct answer is\b",
#             r"\bquestion \d+\b",
#             r"\bfinal question\b",
#         ],
#         "base_conf": 0.86,
#         "scope": "SKILL",
#     },

#     "Feedforward Ambiguity (No help guidance / Unspoken options / Feedforward Ambiguity)": {
#         "patterns": [
#             r"\bwhat can i help you with\b",
#             r"\bplease specify\b",
#             r"\bsorry, i didn't get that\b",
#             r"\bplease try again\b",
#             r"\bask me\b",
#         ],
#         "base_conf": 0.84,
#         "scope": "SKILL",
#     },

#     # ---------------------------
#     # legacy / special
#     # ---------------------------
#     "Unsupported devices": {
#         "patterns": [
#             r"not supported on this device",
#             r"use the alexa app instead",
#             r"messaging with alexa is not supported",
#         ],
#         "base_conf": 0.95,
#         "scope": "SKILL",
#     },
# }

# # ---------------------------------------------------
# # HELPERS
# # ---------------------------------------------------

# def _focus_turns(turns: List[Dict[str, Any]], evidence_span):
#     if evidence_span and isinstance(evidence_span, list) and len(evidence_span) == 2:
#         s, e = evidence_span
#         s = max(0, s)
#         e = min(len(turns) - 1, e)
#         return turns[s:e+1]
#     return turns

# def _joined_text(turns: List[Dict[str, Any]], scope: str) -> str:
#     if scope == "SKILL":
#         return joined_text(turns, role="SKILL")
#     if scope == "USER":
#         return joined_text(turns, role="USER")
#     return joined_text(turns)

# def _extract_json_block(raw: str):
#     match = re.search(r"\{.*\}", raw, re.S)
#     if not match:
#         return None
#     try:
#         return json.loads(match.group())
#     except Exception:
#         return None

# def _skill_turns(turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     return [t for t in turns if t["role"] == "SKILL"]

# def _make_subtype_prediction(
#     subtype: str,
#     confidence: float,
#     evidence_span,
#     reason: str,
#     method: str,
# ):
#     return {
#         "subtype": subtype,
#         "confidence": round(float(confidence), 4),
#         "evidence_span": evidence_span,
#         "reason": reason,
#         "method": method,
#     }

# # ---------------------------------------------------
# # RULE-BASED SUBTYPE HELPERS
# # ---------------------------------------------------

# def _match_rule_subtype(turns: List[Dict[str, Any]], subtype_name: str):
#     rule = SUBTYPE_RULES[subtype_name]
#     txt = _joined_text(turns, rule.get("scope", "BOTH"))
#     pats = rule.get("patterns", [])
#     return any(re.search(p, txt) for p in pats)

# # ---------------------------------------------------
# # LLM ROUTERS
# # ---------------------------------------------------

# def _llm_pick_disguised_ad_subtype(focus_turns: List[Dict[str, Any]], evidence_span):
#     """
#     Candidate subtypes:
#       - Biased recommendation
#       - Product embedding
#       - Native advertising
#     """
#     skill_turns = _skill_turns(focus_turns)
#     if not skill_turns:
#         return _make_subtype_prediction(
#             "ABSTAIN", 0.0, evidence_span, "No skill turns available.", "abstain"
#         )

#     indexed_skill_dialogue = "\n".join(
#         [f"SKILL_TURN_{i}: {t['text']}" for i, t in enumerate(skill_turns)]
#     )

#     prompt = f"""
# You are classifying a dark-pattern subtype under the parent type: Disguised Ad.


# Choose the BEST subtype from the list below.
# If none of them clearly fit, return "Other".

# 1. Biased recommendation
# Definition:
# Recommends specific products, skills, or partners regardless of user intent, prioritizing commercial interests over relevance.

# 2. Product embedding
# Definition:
# Commercial content inserted within an ongoing task flow while the user is performing another activity.

# 3. Native advertising
# Definition:
# The skill’s primary interaction itself functions as advertising while being presented as normal content.

# Guidance:
# - Use "Biased recommendation" when the main issue is a recommendation or suggestion favoring a product/partner/other skill.
# - Use "Product embedding" when commercial content is inserted into another ongoing task flow.
# - Use "Native advertising" when the interaction itself is largely promotional content disguised as normal content.

# Skill turns:
# {indexed_skill_dialogue}

# Return ONLY valid JSON:
# {{
#   "subtype": "Biased recommendation" or "Product embedding" or "Native advertising",
#   "confidence": 0.0,
#   "reason": "short explanation"
# }}
# """

#     try:
#         resp = client.chat.completions.create(
#             model=MODEL_NAME,
#             temperature=0,
#             messages=[{"role": "user", "content": prompt}],
#         )
#         raw = resp.choices[0].message.content
#         print("\nLLM RAW OUTPUT (Disguised Ad subtype):\n", raw)

#         result = _extract_json_block(raw)
#         if not result:
#             return _make_subtype_prediction(
#                 "ABSTAIN", 0.0, evidence_span, "LLM returned invalid JSON.", "abstain"
#             )

#         subtype = result.get("subtype", "ABSTAIN")
#         conf = float(result.get("confidence", 0.75))
#         reason = result.get("reason", "LLM selected subtype.")
#         return _make_subtype_prediction(subtype, conf, evidence_span, reason, "llm")

#     except Exception as e:
#         print("LLM subtype error (Disguised Ad):", e)
#         return _make_subtype_prediction(
#             "ABSTAIN", 0.0, evidence_span, f"LLM error: {e}", "abstain"
#         )

# def _llm_pick_repeated_subtype(focus_turns: List[Dict[str, Any]], evidence_span):
#     """
#     Candidate subtypes:
#       - Error echo
#       - Misleading loop (skills bug) (Repeated prompts)
#       - Feedforward Ambiguity...
#     """
#     full_dialogue = "\n".join(
#         [f'{t["role"]}: {t["text"]}' for t in focus_turns if t["role"] in ("USER", "SKILL")]
#     )

#     prompt = f"""
# You are classifying a dark-pattern subtype under the parent type: Repeated/Confused Output.

# Choose the BEST subtype from the list below.
# If none of them clearly fit, return "Other".

# 1. Error echo
# Definition:
# The system repeats error messages without helping users resolve the issue.

# 2. Misleading loop (skills bug) (Repeated prompts)
# Definition:
# Poorly designed flow traps users in loops unintentionally.

# 3. Feedforward Ambiguity (No help guidance / Unspoken options / Feedforward Ambiguity)
# Definition:
# Offers no guidance about what options are available next or how to proceed.

# Guidance:
# - Error echo = mainly repeated error/help/failure responses.
# - Misleading loop = the flow itself keeps cycling or progressing wrongly like a broken state machine.
# - Feedforward Ambiguity = user is not guided on what they can say/do next.

# Dialogue:
# {full_dialogue}

# Return ONLY valid JSON:
# {{
#   "subtype": "Error echo" or "Misleading loop (skills bug) (Repeated prompts)" or "Feedforward Ambiguity (No help guidance / Unspoken options / Feedforward Ambiguity)",
#   "confidence": 0.0,
#   "reason": "short explanation"
# }}
# """

#     try:
#         resp = client.chat.completions.create(
#             model=MODEL_NAME,
#             temperature=0,
#             messages=[{"role": "user", "content": prompt}],
#         )
#         raw = resp.choices[0].message.content
#         print("\nLLM RAW OUTPUT (Repeated subtype):\n", raw)

#         result = _extract_json_block(raw)
#         if not result:
#             return _make_subtype_prediction(
#                 "ABSTAIN", 0.0, evidence_span, "LLM returned invalid JSON.", "abstain"
#             )

#         subtype = result.get("subtype", "ABSTAIN")
#         conf = float(result.get("confidence", 0.75))
#         reason = result.get("reason", "LLM selected subtype.")
#         return _make_subtype_prediction(subtype, conf, evidence_span, reason, "llm")

#     except Exception as e:
#         print("LLM subtype error (Repeated/Confused Output):", e)
#         return _make_subtype_prediction(
#             "ABSTAIN", 0.0, evidence_span, f"LLM error: {e}", "abstain"
#         )

# def _llm_pick_watch_ads_subtype(focus_turns: List[Dict[str, Any]], evidence_span):
#     """
#     Candidate subtypes:
#       - Feature lock (Subscription interruption)
#       - Paywall bypass
#       - Alexa native ads
#       - Mandatory ads
#     """
#     full_dialogue = "\n".join(
#         [f'{t["role"]}: {t["text"]}' for t in focus_turns if t["role"] in ("USER", "SKILL")]
#     )

#     prompt = f"""
# You are classifying a dark-pattern subtype under the parent type: Watch Ads/Pay to Avoid Ads.


# Choose the BEST subtype from the list below.
# If none of them clearly fit, return "Other".

# 1. Feature lock (Subscription interruption)
# Definition:
# Core features are only accessible via upgrade or payment.

# 2. Paywall bypass
# Definition:
# Content appears free but redirects to payment after engagement.

# 3. Alexa native ads
# Definition:
# After a third party skill or task has ended, the voice assistant host (Alexa) speaks an unsolicited promotional message for a first party service or partner.

# 4. Mandatory ads
# Definition:
# Forces users to listen to ads without skip options or opt-outs.

# Guidance:
# - Feature lock = core functionality gated by premium / package / upgrade.
# - Paywall bypass = user is first engaged, then redirected toward payment/purchase.
# - Alexa native ads = host-level ad after task end.
# - Mandatory ads = clearly ad-like content forced into interaction.

# Dialogue:
# {full_dialogue}

# Return ONLY valid JSON:
# {{
#   "subtype": "Feature lock (Subscription interruption)" or "Paywall bypass" or "Alexa native ads" or "Mandatory ads",
#   "confidence": 0.0,
#   "reason": "short explanation"
# }}
# """

#     try:
#         resp = client.chat.completions.create(
#             model=MODEL_NAME,
#             temperature=0,
#             messages=[{"role": "user", "content": prompt}],
#         )
#         raw = resp.choices[0].message.content
#         print("\nLLM RAW OUTPUT (Watch Ads subtype):\n", raw)

#         result = _extract_json_block(raw)
#         if not result:
#             return _make_subtype_prediction(
#                 "ABSTAIN", 0.0, evidence_span, "LLM returned invalid JSON.", "abstain"
#             )

#         subtype = result.get("subtype", "ABSTAIN")
#         conf = float(result.get("confidence", 0.75))
#         reason = result.get("reason", "LLM selected subtype.")
#         return _make_subtype_prediction(subtype, conf, evidence_span, reason, "llm")

#     except Exception as e:
#         print("LLM subtype error (Watch Ads/Pay):", e)
#         return _make_subtype_prediction(
#             "ABSTAIN", 0.0, evidence_span, f"LLM error: {e}", "abstain"
#         )

# def _llm_pick_rating_subtype(focus_turns: List[Dict[str, Any]], evidence_span):
#     """
#     Candidate subtypes:
#       - Rate us 5 stars
#       - Voice review request
#       - Sentiment framing
#     """
#     full_dialogue = "\n".join(
#         [f'{t["role"]}: {t["text"]}' for t in focus_turns if t["role"] in ("USER", "SKILL")]
#     )

#     prompt = f"""
# You are classifying a dark-pattern subtype under the parent type: Voice-Guided Rating.


# Choose the BEST subtype from the list below.
# If none of them clearly fit, return "Other".

# 1. Rate us 5 stars
# Definition:
# Aggressive prompts asking for top-tier ratings, often repeatedly.

# 2. Voice review request
# Definition:
# Solicits spoken reviews from users, often nudging toward positivity.

# 3. Sentiment framing
# Definition:
# Presents options or content with positive emotional language to bias user choices.

# Guidance:
# - Rate us 5 stars = explicit request for top rating.
# - Voice review request = asks user to speak/record a review or spoken feedback.
# - Sentiment framing = emotionally positive framing nudging the user without explicit 5-star request.

# Dialogue:
# {full_dialogue}

# Return ONLY valid JSON:
# {{
#   "subtype": "Rate us 5 stars" or "Voice review request" or "Sentiment framing",
#   "confidence": 0.0,
#   "reason": "short explanation"
# }}
# """

#     try:
#         resp = client.chat.completions.create(
#             model=MODEL_NAME,
#             temperature=0,
#             messages=[{"role": "user", "content": prompt}],
#         )
#         raw = resp.choices[0].message.content
#         print("\nLLM RAW OUTPUT (Rating subtype):\n", raw)

#         result = _extract_json_block(raw)
#         if not result:
#             return _make_subtype_prediction(
#                 "ABSTAIN", 0.0, evidence_span, "LLM returned invalid JSON.", "abstain"
#             )

#         subtype = result.get("subtype", "ABSTAIN")
#         conf = float(result.get("confidence", 0.75))
#         reason = result.get("reason", "LLM selected subtype.")
#         return _make_subtype_prediction(subtype, conf, evidence_span, reason, "llm")

#     except Exception as e:
#         print("LLM subtype error (Voice-Guided Rating):", e)
#         return _make_subtype_prediction(
#             "ABSTAIN", 0.0, evidence_span, f"LLM error: {e}", "abstain"
#         )

# # ---------------------------------------------------
# # MAIN SUBTYPE CLASSIFIER
# # ---------------------------------------------------

# def _classify_interface_interference_subtype_legacy(
#     turns: List[Dict[str, Any]],
#     step2_out: Dict[str, Any]
# ) -> Dict[str, Any]:
#     flags = step2_out.get("flags", [])

#     # keep compatibility with your current type output
#     top_type = step2_out["step2_type_predictions"][0]["type"]
#     evidence_span = step2_out["step2_type_predictions"][0].get("evidence_span")

#     focus_turns = _focus_turns(turns, evidence_span)

#     # ---------------------------------
#     # special flag-based case
#     # ---------------------------------
#     if "unsupported_device_message" in flags:
#         return _make_subtype_prediction(
#             "Unsupported devices",
#             0.95,
#             evidence_span,
#             "Flag unsupported_device_message detected.",
#             "rule"
#         )

#     # ---------------------------------
#     # Repeated / Confused Output
#     # ---------------------------------
#     if top_type == "Repeated/Confused Output":
#         spans = get_repetition_spans(focus_turns, role="SKILL", min_repeats=3, sim_threshold=0.90)
#         full_skill_txt = _joined_text(focus_turns, "SKILL")

#         # strong rule for Error echo
#         if spans and (
#             "sorry" in full_skill_txt
#             or "please try again" in full_skill_txt
#             or "what can i help you with" in full_skill_txt
#         ):
#             return _make_subtype_prediction(
#                 "Error echo",
#                 0.92,
#                 evidence_span,
#                 "Repeated SKILL outputs and error/help-style responses detected.",
#                 "rule"
#             )

#         # LLM choose among the 3 repeated/confused subtypes
#         return _llm_pick_repeated_subtype(focus_turns, evidence_span)

#     # ---------------------------------
#     # Voice-Guided Rating
#     # ---------------------------------
#     if top_type == "Voice-Guided Rating":
#         # strong rules first
#         if _match_rule_subtype(focus_turns, "Rate us 5 stars"):
#             return _make_subtype_prediction(
#                 "Rate us 5 stars",
#                 SUBTYPE_RULES["Rate us 5 stars"]["base_conf"],
#                 evidence_span,
#                 "Matched subtype rule for Rate us 5 stars.",
#                 "rule"
#             )

#         if _match_rule_subtype(focus_turns, "Voice review request"):
#             return _make_subtype_prediction(
#                 "Voice review request",
#                 SUBTYPE_RULES["Voice review request"]["base_conf"],
#                 evidence_span,
#                 "Matched subtype rule for Voice review request.",
#                 "rule"
#             )

#         return _llm_pick_rating_subtype(focus_turns, evidence_span)

#     # ---------------------------------
#     # Watch Ads / Pay to Avoid Ads
#     # ---------------------------------
#     if top_type == "Watch Ads/Pay to Avoid Ads":
#         if _match_rule_subtype(focus_turns, "Mandatory ads"):
#             return _make_subtype_prediction(
#                 "Mandatory ads",
#                 SUBTYPE_RULES["Mandatory ads"]["base_conf"],
#                 evidence_span,
#                 "Matched subtype rule for Mandatory ads.",
#                 "rule"
#             )

#         return _llm_pick_watch_ads_subtype(focus_turns, evidence_span)

#     # ---------------------------------
#     # Disguised Ad
#     # ---------------------------------
#     if top_type == "Disguised Ad":
#         return _llm_pick_disguised_ad_subtype(focus_turns, evidence_span)

#     # ---------------------------------
#     # Abstain
#     # ---------------------------------
#     if top_type == "ABSTAIN":
#         return _make_subtype_prediction(
#             "ABSTAIN",
#             0.0,
#             evidence_span,
#             "Type unresolved. Subtype not attempted.",
#             "abstain"
#         )

#     return _make_subtype_prediction(
#         "ABSTAIN",
#         0.0,
#         evidence_span,
#         f"No subtype rule matched under type={top_type}.",
#         "abstain"
#     )


# interface_interference_subtype.py

import re
import json
from typing import List, Dict, Any
from openai import OpenAI

from common import get_repetition_spans, joined_text

client = OpenAI()

# ---------------------------------------------------
# RULE SETS
# ---------------------------------------------------

SUBTYPE_RULES = {
    # ---------------------------
    # Watch Ads / Pay to Avoid Ads
    # ---------------------------
    "Feature lock (Subscription interruption)": {
        "patterns": [
            r"\b(premium|expert package|subscription|upgrade)\b",
            r"\bbuy\b.*\b(expert|premium|package)\b",
            r"\bonly available\b.*\b(premium|subscribers?)\b",
            r"\bunlock\b.*\b(premium|expert)\b",
        ],
        "base_conf": 0.88,
        "scope": "SKILL",
    },

    "Paywall bypass": {
        "patterns": [
            r"\bwould you like to learn how to buy\b",
            r"\badd .* to your shopping cart\b",
            r"\bget it in \d+ days\b",
            r"\bbuy now\b",
        ],
        "base_conf": 0.82,
        "scope": "SKILL",
    },

    "Alexa native ads": {
        "patterns": [
            r"\balexa recommends\b",
            r"\btry amazon\b",
            r"\byou might also like amazon\b",
        ],
        "base_conf": 0.80,
        "scope": "SKILL",
    },

    "Mandatory ads": {
        "patterns": [
            r"\b(advertisement|advertisements)\b",
            r"\b(sponsored|sponsor message)\b",
            r"\b(remove|skip)\b.*\bads?\b",
            r"\bpay to\b.*\b(remove|skip)\b.*\bads?\b",
            r"\blisten to this\b.*\b(message|offer)\b",
            # forced promotional pitch: URL read aloud + contract/fee terms
            r"\bdot com\b.*\bforwardslash\b",
            r"\b(monitoring|termination|activation|installation)\s+fees?\b",
            r"\bmonitoring contract\b",
            r"\blimited time\b.*\b(free|off|discount|deal)\b",
        ],
        "base_conf": 0.90,
        "scope": "SKILL",
    },

    # ---------------------------
    # Voice-Guided Rating
    # ---------------------------
    "Rate us 5 stars": {
        "patterns": [
            r"\b(rate|review)\b.*\b(five|5)\b.*\b(star|stars)\b",
            r"\b(five|5)\s*star(s)?\b",
            r"\btop\b.*\brating\b",
            r"\bbest\b.*\brating\b",
        ],
        "base_conf": 0.96,
        "scope": "SKILL",
    },

    "Voice review request": {
        "patterns": [
            r"\b(tell me|say|record)\b.*\b(review|feedback)\b",
            r"\bleave\b.*\bvoice\b.*\b(review|feedback)\b",
            r"\bsay your review\b",
        ],
        "base_conf": 0.90,
        "scope": "SKILL",
    },

    "Sentiment framing": {
        "patterns": [
            r"\bif you enjoy\b",
            r"\bif you like this\b",
            r"\bshow your support\b",
            r"\bgive this skill some love\b",
        ],
        "base_conf": 0.80,
        "scope": "SKILL",
    },

    # ---------------------------
    # Repeated / Confused Output
    # ---------------------------
    "Error echo": {
        "base_conf": 0.92,
    },

    "Misleading loop (skills bug) (Repeated prompts)": {
        "patterns": [
            r"\bnext question\b",
            r"\byour current score\b",
            r"\bthe correct answer is\b",
            r"\bquestion \d+\b",
            r"\bfinal question\b",
        ],
        "base_conf": 0.86,
        "scope": "SKILL",
    },

    "Feedforward Ambiguity (No help guidance / Unspoken options / Feedforward Ambiguity)": {
        "patterns": [
            r"\bwhat can i help you with\b",
            r"\bplease specify\b",
            r"\bsorry, i didn't get that\b",
            r"\bplease try again\b",
            r"\bask me\b",
        ],
        "base_conf": 0.84,
        "scope": "SKILL",
    },

    # ---------------------------
    # legacy / special
    # ---------------------------
    "Unsupported devices": {
        "patterns": [
            r"not supported on this device",
            r"use the alexa app instead",
            r"messaging with alexa is not supported",
        ],
        "base_conf": 0.95,
        "scope": "SKILL",
    },
}

# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------

def _focus_turns(turns: List[Dict[str, Any]], evidence_span):
    if evidence_span and isinstance(evidence_span, list) and len(evidence_span) == 2:
        s, e = evidence_span
        s = max(0, s)
        e = min(len(turns) - 1, e)
        return turns[s:e+1]
    return turns

def _joined_text(turns: List[Dict[str, Any]], scope: str) -> str:
    if scope == "SKILL":
        return joined_text(turns, role="SKILL")
    if scope == "USER":
        return joined_text(turns, role="USER")
    return joined_text(turns)

def _extract_json_block(raw: str):
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except Exception:
        return None

def _skill_turns(turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [t for t in turns if t["role"] == "SKILL"]

def _make_subtype_prediction(
    subtype: str,
    confidence: float,
    evidence_span,
    reason: str,
    method: str,
):
    return {
        "subtype": subtype,
        "confidence": round(float(confidence), 4),
        "evidence_span": evidence_span,
        "reason": reason,
        "method": method,
    }

def _normalize_llm_subtype(subtype_value: str) -> str:
    """
    Map LLM 'Other' / unknown outputs to ABSTAIN.
    """
    if not subtype_value:
        return "ABSTAIN"
    s = subtype_value.strip()
    if s.lower() in {"other", "none", "none of the above", "unclear", "unknown"}:
        return "ABSTAIN"
    return s

def _get_primary_type_info(step2_out: Dict[str, Any]):
    """
    Prefer new multi-label structure:
      - primary_type_prediction
    Fallback to:
      - step2_type_predictions[0]
    """
    primary = step2_out.get("primary_type_prediction")
    if primary and isinstance(primary, dict):
        return (
            primary.get("type", "ABSTAIN"),
            primary.get("evidence_span")
        )

    preds = step2_out.get("step2_type_predictions", [])
    if preds:
        return (
            preds[0].get("type", "ABSTAIN"),
            preds[0].get("evidence_span")
        )

    return ("ABSTAIN", None)

# ---------------------------------------------------
# RULE-BASED SUBTYPE HELPERS
# ---------------------------------------------------

def _match_rule_subtype(turns: List[Dict[str, Any]], subtype_name: str):
    rule = SUBTYPE_RULES[subtype_name]
    txt = _joined_text(turns, rule.get("scope", "BOTH"))
    pats = rule.get("patterns", [])
    return any(re.search(p, txt) for p in pats)

# ---------------------------------------------------
# LLM ROUTERS
# ---------------------------------------------------

def _llm_pick_disguised_ad_subtype(focus_turns: List[Dict[str, Any]], evidence_span):
    """
    Candidate subtypes:
      - Biased recommendation
      - Product embedding
      - Native advertising
      - Other -> ABSTAIN
    """
    skill_turns = _skill_turns(focus_turns)
    if not skill_turns:
        return _make_subtype_prediction(
            "ABSTAIN", 0.0, evidence_span, "No skill turns available.", "abstain"
        )

    indexed_skill_dialogue = "\n".join(
        [f"SKILL_TURN_{i}: {t['text']}" for i, t in enumerate(skill_turns)]
    )

    prompt = f"""
You are classifying a dark-pattern subtype under the parent type: Disguised Ad.

Choose the BEST subtype from the list below.
If none of them clearly fit, return "Other".
Do not guess when evidence is weak or ambiguous.

1. Biased recommendation
Definition:
Recommends specific products, skills, or partners regardless of user intent, prioritizing commercial interests over relevance.

2. Product embedding
Definition:
Commercial content inserted within an ongoing task flow while the user is performing another activity.

3. Native advertising
Definition:
The skill’s primary interaction itself functions as advertising while being presented as normal content.

Guidance:
- Use "Biased recommendation" when the main issue is a recommendation or suggestion favoring a product/partner/other skill.
- Use "Product embedding" when commercial content is inserted into another ongoing task flow.
- Use "Native advertising" when the interaction itself is largely promotional content disguised as normal content.
- Use "Other" when the evidence does not clearly fit one of the above.

Skill turns:
{indexed_skill_dialogue}

Return ONLY valid JSON:
{{
  "subtype": "Biased recommendation" or "Product embedding" or "Native advertising" or "Other",
  "confidence": 0.0,
  "reason": "short explanation"
}}
"""

    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            **completion_parameters(),
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.choices[0].message.content
        print("\nLLM RAW OUTPUT (Disguised Ad subtype):\n", raw)

        result = _extract_json_block(raw)
        if not result:
            return _make_subtype_prediction(
                "ABSTAIN", 0.0, evidence_span, "LLM returned invalid JSON.", "abstain"
            )

        subtype = _normalize_llm_subtype(result.get("subtype", "ABSTAIN"))
        conf = float(result.get("confidence", 0.75))
        reason = result.get("reason", "LLM selected subtype.")

        if subtype == "ABSTAIN":
            return _make_subtype_prediction(
                "ABSTAIN", 0.0, evidence_span, f"LLM returned Other. {reason}", "abstain"
            )

        return _make_subtype_prediction(subtype, conf, evidence_span, reason, "llm")

    except Exception as e:
        print("LLM subtype error (Disguised Ad):", e)
        return _make_subtype_prediction(
            "ABSTAIN", 0.0, evidence_span, f"LLM error: {e}", "abstain"
        )

def _llm_pick_repeated_subtype(focus_turns: List[Dict[str, Any]], evidence_span):
    """
    Candidate subtypes:
      - Error echo
      - Misleading loop (skills bug) (Repeated prompts)
      - Feedforward Ambiguity...
      - Other -> ABSTAIN
    """
    full_dialogue = "\n".join(
        [f'{t["role"]}: {t["text"]}' for t in focus_turns if t["role"] in ("USER", "SKILL")]
    )

    prompt = f"""
You are classifying a dark-pattern subtype under the parent type: Repeated/Confused Output.

Choose the BEST subtype from the list below.
If none of them clearly fit, return "Other".
Do not guess when evidence is weak or ambiguous.

1. Error echo
Definition:
The system repeats error messages without helping users resolve the issue.

2. Misleading loop (skills bug) (Repeated prompts)
Definition:
Poorly designed flow traps users in loops unintentionally.

3. Feedforward Ambiguity (No help guidance / Unspoken options / Feedforward Ambiguity)
Definition:
Offers no guidance about what options are available next or how to proceed.

Guidance:
- Error echo = mainly repeated error/help/failure responses.
- Misleading loop = the flow itself keeps cycling or progressing wrongly like a broken state machine.
- Feedforward Ambiguity = user is not guided on what they can say or do next.
- Use "Other" when the evidence does not clearly fit one of the above.

Dialogue:
{full_dialogue}

Return ONLY valid JSON:
{{
  "subtype": "Error echo" or "Misleading loop (skills bug) (Repeated prompts)" or "Feedforward Ambiguity (No help guidance / Unspoken options / Feedforward Ambiguity)" or "Other",
  "confidence": 0.0,
  "reason": "short explanation"
}}
"""

    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            **completion_parameters(),
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.choices[0].message.content
        print("\nLLM RAW OUTPUT (Repeated subtype):\n", raw)

        result = _extract_json_block(raw)
        if not result:
            return _make_subtype_prediction(
                "ABSTAIN", 0.0, evidence_span, "LLM returned invalid JSON.", "abstain"
            )

        subtype = _normalize_llm_subtype(result.get("subtype", "ABSTAIN"))
        conf = float(result.get("confidence", 0.75))
        reason = result.get("reason", "LLM selected subtype.")

        if subtype == "ABSTAIN":
            return _make_subtype_prediction(
                "ABSTAIN", 0.0, evidence_span, f"LLM returned Other. {reason}", "abstain"
            )

        return _make_subtype_prediction(subtype, conf, evidence_span, reason, "llm")

    except Exception as e:
        print("LLM subtype error (Repeated/Confused Output):", e)
        return _make_subtype_prediction(
            "ABSTAIN", 0.0, evidence_span, f"LLM error: {e}", "abstain"
        )

def _llm_pick_watch_ads_subtype(focus_turns: List[Dict[str, Any]], evidence_span):
    """
    Candidate subtypes:
      - Feature lock (Subscription interruption)
      - Paywall bypass
      - Alexa native ads
      - Mandatory ads
      - Other -> ABSTAIN
    """
    full_dialogue = "\n".join(
        [f'{t["role"]}: {t["text"]}' for t in focus_turns if t["role"] in ("USER", "SKILL")]
    )

    prompt = f"""
You are classifying a dark-pattern subtype under the parent type: Watch Ads/Pay to Avoid Ads.

Choose the BEST subtype from the list below.
If none of them clearly fit, return "Other".
Do not guess when evidence is weak or ambiguous.

1. Feature lock (Subscription interruption)
Definition:
Core features are only accessible via upgrade or payment.

2. Paywall bypass
Definition:
Content appears free but redirects to payment after engagement.

3. Alexa native ads
Definition:
After a third party skill or task has ended, the voice assistant host (Alexa) speaks an unsolicited promotional message for a first party service or partner.

4. Mandatory ads
Definition:
Forces users to listen to ads without skip options or opt-outs.

Guidance:
- Feature lock = core functionality gated by premium / package / upgrade.
- Paywall bypass = user is first engaged, then redirected toward payment/purchase.
- Alexa native ads = host-level ad after task end.
- Mandatory ads = clearly ad-like content forced into interaction.
- Use "Other" when the evidence does not clearly fit one of the above.

Dialogue:
{full_dialogue}

Return ONLY valid JSON:
{{
  "subtype": "Feature lock (Subscription interruption)" or "Paywall bypass" or "Alexa native ads" or "Mandatory ads" or "Other",
  "confidence": 0.0,
  "reason": "short explanation"
}}
"""

    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            **completion_parameters(),
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.choices[0].message.content
        print("\nLLM RAW OUTPUT (Watch Ads subtype):\n", raw)

        result = _extract_json_block(raw)
        if not result:
            return _make_subtype_prediction(
                "ABSTAIN", 0.0, evidence_span, "LLM returned invalid JSON.", "abstain"
            )

        subtype = _normalize_llm_subtype(result.get("subtype", "ABSTAIN"))
        conf = float(result.get("confidence", 0.75))
        reason = result.get("reason", "LLM selected subtype.")

        if subtype == "ABSTAIN":
            return _make_subtype_prediction(
                "ABSTAIN", 0.0, evidence_span, f"LLM returned Other. {reason}", "abstain"
            )

        return _make_subtype_prediction(subtype, conf, evidence_span, reason, "llm")

    except Exception as e:
        print("LLM subtype error (Watch Ads/Pay):", e)
        return _make_subtype_prediction(
            "ABSTAIN", 0.0, evidence_span, f"LLM error: {e}", "abstain"
        )

def _llm_pick_rating_subtype(focus_turns: List[Dict[str, Any]], evidence_span):
    """
    Candidate subtypes:
      - Rate us 5 stars
      - Voice review request
      - Sentiment framing
      - Other -> ABSTAIN
    """
    full_dialogue = "\n".join(
        [f'{t["role"]}: {t["text"]}' for t in focus_turns if t["role"] in ("USER", "SKILL")]
    )

    prompt = f"""
You are classifying a dark-pattern subtype under the parent type: Voice-Guided Rating.

Choose the BEST subtype from the list below.
If none of them clearly fit, return "Other".
Do not guess when evidence is weak or ambiguous.

1. Rate us 5 stars
Definition:
Aggressive prompts asking for top-tier ratings, often repeatedly.

2. Voice review request
Definition:
Solicits spoken reviews from users, often nudging toward positivity.

3. Sentiment framing
Definition:
Presents options or content with positive emotional language to bias user choices.

Guidance:
- Rate us 5 stars = explicit request for top rating.
- Voice review request = asks user to speak/record a review or spoken feedback.
- Sentiment framing = emotionally positive framing nudging the user without explicit 5-star request.
- Use "Other" when the evidence does not clearly fit one of the above.

Dialogue:
{full_dialogue}

Return ONLY valid JSON:
{{
  "subtype": "Rate us 5 stars" or "Voice review request" or "Sentiment framing" or "Other",
  "confidence": 0.0,
  "reason": "short explanation"
}}
"""

    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            **completion_parameters(),
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.choices[0].message.content
        print("\nLLM RAW OUTPUT (Rating subtype):\n", raw)

        result = _extract_json_block(raw)
        if not result:
            return _make_subtype_prediction(
                "ABSTAIN", 0.0, evidence_span, "LLM returned invalid JSON.", "abstain"
            )

        subtype = _normalize_llm_subtype(result.get("subtype", "ABSTAIN"))
        conf = float(result.get("confidence", 0.75))
        reason = result.get("reason", "LLM selected subtype.")

        if subtype == "ABSTAIN":
            return _make_subtype_prediction(
                "ABSTAIN", 0.0, evidence_span, f"LLM returned Other. {reason}", "abstain"
            )

        return _make_subtype_prediction(subtype, conf, evidence_span, reason, "llm")

    except Exception as e:
        print("LLM subtype error (Voice-Guided Rating):", e)
        return _make_subtype_prediction(
            "ABSTAIN", 0.0, evidence_span, f"LLM error: {e}", "abstain"
        )

# ---------------------------------------------------
# MAIN SUBTYPE CLASSIFIER
# ---------------------------------------------------

def _classify_interface_interference_subtype_legacy(
    turns: List[Dict[str, Any]],
    step2_out: Dict[str, Any]
) -> Dict[str, Any]:
    flags = step2_out.get("flags", [])

    top_type, evidence_span = _get_primary_type_info(step2_out)
    focus_turns = _focus_turns(turns, evidence_span)

    # ---------------------------------
    # special flag-based case
    # ---------------------------------
    if "unsupported_device_message" in flags:
        return _make_subtype_prediction(
            "Unsupported devices",
            0.95,
            evidence_span,
            "Flag unsupported_device_message detected.",
            "rule"
        )

    # ---------------------------------
    # Repeated / Confused Output
    # ---------------------------------
    if top_type == "Repeated/Confused Output":
        spans = get_repetition_spans(focus_turns, role="SKILL", min_repeats=3, sim_threshold=0.90)
        full_skill_txt = _joined_text(focus_turns, "SKILL")

        # strong rule for Error echo
        if spans and (
            "sorry" in full_skill_txt
            or "please try again" in full_skill_txt
            or "what can i help you with" in full_skill_txt
        ):
            return _make_subtype_prediction(
                "Error echo",
                0.92,
                evidence_span,
                "Repeated SKILL outputs and error/help-style responses detected.",
                "rule"
            )

        if _match_rule_subtype(focus_turns, "Misleading loop (skills bug) (Repeated prompts)"):
            return _make_subtype_prediction(
                "Misleading loop (skills bug) (Repeated prompts)",
                SUBTYPE_RULES["Misleading loop (skills bug) (Repeated prompts)"]["base_conf"],
                evidence_span,
                "Matched subtype rule for Misleading loop.",
                "rule"
            )

        if _match_rule_subtype(focus_turns, "Feedforward Ambiguity (No help guidance / Unspoken options / Feedforward Ambiguity)"):
            return _make_subtype_prediction(
                "Feedforward Ambiguity (No help guidance / Unspoken options / Feedforward Ambiguity)",
                SUBTYPE_RULES["Feedforward Ambiguity (No help guidance / Unspoken options / Feedforward Ambiguity)"]["base_conf"],
                evidence_span,
                "Matched subtype rule for Feedforward Ambiguity.",
                "rule"
            )

        return _llm_pick_repeated_subtype(focus_turns, evidence_span)

    # ---------------------------------
    # Voice-Guided Rating
    # ---------------------------------
    if top_type == "Voice-Guided Rating":
        if _match_rule_subtype(focus_turns, "Rate us 5 stars"):
            return _make_subtype_prediction(
                "Rate us 5 stars",
                SUBTYPE_RULES["Rate us 5 stars"]["base_conf"],
                evidence_span,
                "Matched subtype rule for Rate us 5 stars.",
                "rule"
            )

        if _match_rule_subtype(focus_turns, "Voice review request"):
            return _make_subtype_prediction(
                "Voice review request",
                SUBTYPE_RULES["Voice review request"]["base_conf"],
                evidence_span,
                "Matched subtype rule for Voice review request.",
                "rule"
            )

        if _match_rule_subtype(focus_turns, "Sentiment framing"):
            return _make_subtype_prediction(
                "Sentiment framing",
                SUBTYPE_RULES["Sentiment framing"]["base_conf"],
                evidence_span,
                "Matched subtype rule for Sentiment framing.",
                "rule"
            )

        return _llm_pick_rating_subtype(focus_turns, evidence_span)

    # ---------------------------------
    # Watch Ads / Pay to Avoid Ads
    # ---------------------------------
    if top_type == "Watch Ads/Pay to Avoid Ads":
        if _match_rule_subtype(focus_turns, "Mandatory ads"):
            return _make_subtype_prediction(
                "Mandatory ads",
                SUBTYPE_RULES["Mandatory ads"]["base_conf"],
                evidence_span,
                "Matched subtype rule for Mandatory ads.",
                "rule"
            )

        if _match_rule_subtype(focus_turns, "Feature lock (Subscription interruption)"):
            return _make_subtype_prediction(
                "Feature lock (Subscription interruption)",
                SUBTYPE_RULES["Feature lock (Subscription interruption)"]["base_conf"],
                evidence_span,
                "Matched subtype rule for Feature lock.",
                "rule"
            )

        if _match_rule_subtype(focus_turns, "Paywall bypass"):
            return _make_subtype_prediction(
                "Paywall bypass",
                SUBTYPE_RULES["Paywall bypass"]["base_conf"],
                evidence_span,
                "Matched subtype rule for Paywall bypass.",
                "rule"
            )

        if _match_rule_subtype(focus_turns, "Alexa native ads"):
            return _make_subtype_prediction(
                "Alexa native ads",
                SUBTYPE_RULES["Alexa native ads"]["base_conf"],
                evidence_span,
                "Matched subtype rule for Alexa native ads.",
                "rule"
            )

        return _llm_pick_watch_ads_subtype(focus_turns, evidence_span)

    # ---------------------------------
    # Disguised Ad
    # ---------------------------------
    if top_type == "Disguised Ad":
        return _llm_pick_disguised_ad_subtype(focus_turns, evidence_span)

    # ---------------------------------
    # Abstain
    # ---------------------------------
    if top_type == "ABSTAIN":
        return _make_subtype_prediction(
            "ABSTAIN",
            0.0,
            evidence_span,
            "Type unresolved. Subtype not attempted.",
            "abstain"
        )

    return _make_subtype_prediction(
        "ABSTAIN",
        0.0,
        evidence_span,
        f"No subtype rule matched under type={top_type}.",
        "abstain"
    )

# 第二步实验：沿用原模型子分类提示词，仅调整规则的优先权。
from experiment_config import PROFILE, MODEL_NAME, completion_parameters
from decision_policy import rank_candidates

def classify_interface_interference_subtype(turns, step2_out):
    if PROFILE in ("model_priority_v2", "verified_failure_fallback"):
        from interface_interference_prompt_v2 import subtype_from_joint
        return subtype_from_joint(step2_out)
    if PROFILE == "legacy":
        return _classify_interface_interference_subtype_legacy(turns, step2_out)
    top_type, span = _get_primary_type_info(step2_out)
    routers = {"Repeated/Confused Output": _llm_pick_repeated_subtype,
               "Voice-Guided Rating": _llm_pick_rating_subtype,
               "Watch Ads/Pay to Avoid Ads": _llm_pick_watch_ads_subtype,
               "Disguised Ad": _llm_pick_disguised_ad_subtype}
    if top_type not in routers:
        return _make_subtype_prediction("ABSTAIN", 0.0, span, "Type unresolved. Subtype not attempted.", "abstain")
    focus = _focus_turns(turns, span)
    old = _classify_interface_interference_subtype_legacy(turns, step2_out)
    rules = [old] if old.get("method") == "rule" else []
    model = routers[top_type](focus, span) if rules else old
    ranked = rank_candidates([model], rules, focus, "subtype")
    result = dict(ranked[0] if ranked else model)
    result["decision_audit"] = {"profile": PROFILE, "model_candidate": model, "rule_candidates": rules}
    return result
