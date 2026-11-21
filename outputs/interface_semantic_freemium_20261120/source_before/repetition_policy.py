"""用户指定的严格重复门槛；只判断候选资格，不自行判定暗黑模式。"""
import re

REPEATED_TYPE = 'Repeated/Confused Output'
POLICY_VERSION = 'three_exact_replies_distinct_user_commands_v1'


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
        supported = [w for w in windows if set(w['skill_turn_ids']).issubset(cited)]
        if supported:
            kept.append(candidate)
        else:
            excluded.append({'type': REPEATED_TYPE,
                'reason': '未引用满足连续3次技能回复逐字相同且对应用户指令互不重复的证据窗口。'})
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
