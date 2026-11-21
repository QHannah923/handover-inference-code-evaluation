"""模型优先策略；只改变决策优先级，不修改原提示词。"""
import re
from experiment_config import MODEL_WEIGHT, RULE_WEIGHT, STRONG_RULE_THRESHOLD


def explicit_five_star_request(turns):
    # Only a direct request for five stars is strong enough to override a model.
    return any(
        t.get('role') == 'SKILL' and re.search(
            r'\b(?:rate|give|leave)\b[^.!?\n]{0,100}\b(?:five|5)[ -]*stars?\b',
            t.get('text', ''), re.I
        ) for t in turns
    )


def strong_rule(pred, turns, label_key):
    expected = 'Voice-Guided Rating' if label_key == 'type' else 'Rate us 5 stars'
    return (pred.get(label_key) == expected
            and pred.get('confidence', 0) >= STRONG_RULE_THRESHOLD
            and explicit_five_star_request(turns))


def rank_candidates(models, rules, turns, label_key):
    """Weak rules support matching model proposals; never invent a model vote.

    Scores are ranking scores, not calibrated probabilities. Original model
    confidence thresholds remain separate from these weighted ranking scores.
    """
    candidates = []
    for model in models:
        if model.get(label_key) == 'ABSTAIN':
            continue
        support = max((r['confidence'] for r in rules
                       if r[label_key] == model[label_key]), default=0)
        candidates.append({**model,
            'ranking_score': round(MODEL_WEIGHT * model['confidence'] + RULE_WEIGHT * support, 6),
            'rule_support': support, 'strong_rule_override': False})
    for rule in rules:
        if strong_rule(rule, turns, label_key):
            candidates.append({**rule, 'ranking_score': round(RULE_WEIGHT * rule['confidence'], 6),
                               'strong_rule_override': True})
    candidates.sort(key=lambda p: (p['strong_rule_override'], p['ranking_score']), reverse=True)
    seen = set()
    unique = []
    for p in candidates:
        if p[label_key] not in seen:
            seen.add(p[label_key])
            unique.append(p)
    return unique
