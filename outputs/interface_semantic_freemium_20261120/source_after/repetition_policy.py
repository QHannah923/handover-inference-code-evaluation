"""用户指定的严格重复门槛；只判断候选资格，不自行判定暗黑模式。"""
import re

REPEATED_TYPE = 'Repeated/Confused Output'
POLICY_VERSION = 'mechanism_specific_evidence_20261120'


def _command_key(text):
    # Case/spacing/terminal punctuation do not make a repeated command new.
    return re.sub(r'\s+', ' ', text).strip().casefold().strip(' .!?。！？')


def exact_repetition_windows(turns):
    """Find three consecutive USER→SKILL pairs with equal reply text.

    USER turns between replies are expected. Missing/ambiguous USER→SKILL
    pairing, OTHER turns, empty text and a different reply break a window.
    Reply equality uses the existing parser's text, without further folding,
    similarity scores, punctuation removal or whitespace normalization.
    """
    pending_users = []
    pairs = []
    windows = []
    for turn in turns:
        role = turn.get('role')
        if role == 'USER':
            pending_users.append(turn)
            continue
        if role != 'SKILL':
            pending_users = []
            pairs = []
            continue
        if len(pending_users) != 1:
            pending_users = []
            pairs = []
            continue
        user = pending_users.pop()
        text = turn.get('text', '')
        command = _command_key(user.get('text', ''))
        if not text.strip() or not command:
            pairs = []
            continue
        pairs.append({'user_turn_id': user['idx'], 'skill_turn_id': turn['idx'],
                      'command_key': command, 'reply_text': text})
        pairs = pairs[-3:]
        if len(pairs) != 3:
            continue
        if not (pairs[0]['reply_text'] == pairs[1]['reply_text'] == pairs[2]['reply_text']):
            continue
        if len({p['command_key'] for p in pairs}) != 3:
            continue
        windows.append({'user_turn_ids': [p['user_turn_id'] for p in pairs],
                        'skill_turn_ids': [p['skill_turn_id'] for p in pairs]})
    return windows


def apply_repetition_gate(value, rules, turns):
    """Filter only repeated-output votes; preserve other categories and raw output."""
    windows = exact_repetition_windows(turns)
    kept = []
    excluded = []
    for candidate in value['candidates']:
        if candidate['type'] != REPEATED_TYPE:
            kept.append(candidate)
            continue
        cited = set(candidate['evidence_turn_ids'])
        mechanism = candidate.get('failure_mechanism', 'exact_repetition')
        if mechanism == 'exact_repetition':
            supported = [w for w in windows if set(w['skill_turn_ids']).issubset(cited)]
        else:
            pairs = candidate.get('fault_pairs', [])
            valid = isinstance(pairs, list) and all(isinstance(p, list) and len(p) == 2 and
                all(type(i) is int and 0 <= i < len(turns) and i in cited for i in p) and
                turns[p[0]]['role'] == 'USER' and turns[p[1]]['role'] == 'SKILL' and p[1] == p[0] + 1 and
                not re.search(r'[<>\[\]]', turns[p[0]]['text']) for p in pairs)
            unique = len({tuple(p) for p in pairs}) if valid else 0
            needed = {'error_echo': 3, 'semantic_mismatch': 2, 'scoring_failure': 2,
                      'broken_content': 2, 'missing_guidance': 2, 'contradictory_guidance': 1}.get(mechanism)
            valid = valid and needed is not None and unique == len(pairs) and unique >= needed
            if valid and mechanism == 'error_echo':
                skill_ids = [t['idx'] for t in turns if t['role'] == 'SKILL']; positions = {i:p for p,i in enumerate(skill_ids)}
                ids = sorted(p[1] for p in pairs)
                valid = all(positions[b] == positions[a] + 1 for a,b in zip(ids,ids[1:])) and len({_command_key(turns[p[0]]['text']) for p in pairs}) >= 2
            if valid and mechanism in ('missing_guidance', 'contradictory_guidance'):
                contracts = candidate.get('contract_turn_ids', [])
                valid = isinstance(contracts, list) and bool(contracts) and all(type(i) is int and i in cited and
                    turns[i]['role'] == 'SKILL' and i < min(p[0] for p in pairs) for i in contracts)
            supported = valid
        if supported:
            kept.append(candidate)
        else:
            excluded.append({'type': REPEATED_TYPE,
                'mechanism': mechanism, 'reason': '没有提供所声明机制需要的完整、相邻、有效证据；逐字重复才要求三条相同。'})
    # Approximate repetition and ignored-help rules may no longer support this type.
    filtered_rules = [r for r in rules if r.get('type') != REPEATED_TYPE]
    if windows:
        ids = sorted(set(windows[0]['user_turn_ids'] + windows[0]['skill_turn_ids']))
        filtered_rules.append({'type': REPEATED_TYPE, 'confidence': .93, 'method': 'rule',
            'reason': '连续3次技能回复逐字相同，且对应用户指令互不重复；仅支持模型候选。',
            'evidence_turn_ids': ids, 'evidence_span': [min(ids), max(ids)],
            'evidence_turns': [t for t in turns if t['idx'] in ids]})
    audit = {'version': POLICY_VERSION, 'eligible': bool(windows),
             'qualifying_windows': windows, 'excluded_candidates': excluded}
    return kept, filtered_rules, audit
