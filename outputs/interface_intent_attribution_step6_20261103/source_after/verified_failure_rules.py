"""Independent transcript certificates; no labels, filenames or model scores.

Rules normally fill an empty model decision. Repeated explicit false purchase
attribution can prioritize a proven routing fault while retaining a prior ad.
Certificate validity is a narrow text relation, not a calibrated accuracy score.
"""
import copy
import re

R = 'Repeated/Confused Output'
LOOP = 'Misleading loop (skills bug) (Repeated prompts)'
VERSION = 'verified_intent_attribution_20261103'
ORDINALS = {w: str(i) for i, words in enumerate([
    ('one', 'first'), ('two', 'second'), ('three', 'third'), ('four', 'fourth'),
    ('five', 'fifth'), ('six', 'sixth'), ('seven', 'seventh'), ('eight', 'eighth'),
    ('nine', 'ninth'), ('ten', 'tenth')], 1) for w in words}
RETRIES = {'again', 'repeat', 'say again', 'please repeat', 'what did you say'}
FAILURE = re.compile(
    r"(?:(?:i m )?sorry )?i (?:didn t|did not|can t|cannot|couldn t|could not|do not|don t) "
    r"(?:understand|catch|recognize)(?: the command| that| your request| your command)?"
    r"(?: please say again| could you please repeat that| please try again|"
    r" ask me a question again(?: my friend)?)?")


def words(text):
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', text.casefold()).split())


def answer_key(text):
    value = words(text)
    value = re.sub(r'^(?:the |answer is )', '', value)
    value = re.sub(r'\b(\d+)(?:st|nd|rd|th)\b', r'\1', value)
    tokens = [ORDINALS.get(w, w) for w in value.split()]
    # A documented local grammar; it asserts no external constitutional facts.
    if len(tokens) == 2 and 'amendment' in tokens:
        return ('amendment', next(w for w in tokens if w != 'amendment'))
    return tuple(tokens)


def scoring_witness(user, skill):
    text = skill['text']
    # Quoted failures and ordinary quiz explanations are not live rejection.
    rejected = re.match(r'^\s*(?:<Short audio>\s*[.]?\s*)?(?:incorrect|wrong)\b[.!,: ]+', text, re.I)
    if not rejected:
        return None
    body = text[rejected.end():]
    explicit = re.match(r'(?:the )?correct answer is\s*:?\s*([^.!?\n]+)', body, re.I)
    amendment = re.match(r'The\s+((?:\d+(?:st|nd|rd|th)?|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+Amendment)\b', body, re.I)
    disclosed = explicit or amendment
    if not disclosed:
        return None
    expected = disclosed.group(1).strip()
    if not answer_key(user['text']) or answer_key(user['text']) != answer_key(expected):
        return None
    return {'user_turn_id': user['idx'], 'skill_turn_id': skill['idx'],
            'user_text': user['text'], 'skill_text': text, 'disclosed_answer': expected,
            'normalized_equal_answer': list(answer_key(expected))}


def purchase_misroutes(turns):
    """Two different numbered questions misrouted to purchase identification."""
    question = None; pending = []; found = []
    for turn in turns:
        if turn['role'] == 'USER':
            pending.append(turn)
            continue
        if turn['role'] != 'SKILL' or len(pending) != 1:
            question = None; pending = []
            continue
        user = pending.pop(); request = words(user['text']); response = words(turn['text'])
        commercial_request = re.search(r'\b(?:buy|purchase|order|price|cost|subscribe|subscription|premium|packs?)\b', request)
        if commercial_request:
            question = None
        wrong_purchase = re.match(r'(?:i am sorry but )?(?:we|i) (?:couldn t|could not) identify the product you want to purchase\b', response)
        if question and wrong_purchase and request and not commercial_request and not re.search(r'[<>\[\]]', user['text']):
            found.append({'contract_turn_id': question['idx'], 'contract_text': question['text'],
                          'user_turn_id': user['idx'], 'skill_turn_id': turn['idx'],
                          'user_text': user['text'], 'skill_text': turn['text']})
        if re.search(r'\bquestion\s+\d+\b', response) and re.search(r'\b(?:guess|answer|respond)\b', response):
            question = turn
        elif re.search(r'\b(?:thank you for playing|final score|you got \d+ out of|want to buy|would you like to (?:buy|purchase))\b', response):
            question = None
        elif not wrong_purchase and re.search(r'\b(?:buy|purchase|products?|packs?|premium|subscription|subscribe)\b', response):
            question = None
    if len({w['contract_turn_id'] for w in found}) < 2:
        return []
    return [{'rule_id': 'TWO_QUIZ_PURCHASE_MISROUTES', 'type': R, 'subtype': LOOP, 'witnesses': found,
             'reason': '两个不同的已公布题目中，非购买输入被当作无法识别的购买请求；排除主动购买、占位输入和已结束答题流程。'}]


def cross_app_referrals(turns):
    """Explicit unsolicited calls to another software destination; parent only.

    A generic 'also use X' does not identify a software destination sufficiently.
    Help, requested recommendations and platform/account setup are excluded.
    """
    found = []; pending = []
    for skill in turns:
        if skill['role'] == 'USER':
            pending.append(skill)
            continue
        if skill['role'] != 'SKILL' or len(pending) != 1:
            pending = []
            continue
        user = pending.pop(); request = words(user['text']); text = skill['text']
        if re.fullmatch(r'(?:help|options|commands|what can i say|what can you do)', request):
            continue
        if re.search(r'\b(?:recommend|suggest|enable|install|other apps?|other skills?|sister skills?)\b', request):
            continue
        if re.search(r'\b(?:alexa app|app settings|account settings|grant permissions?)\b', text, re.I):
            continue
        signals = [r'\btry(?: out)? our sister skills\b',
                   r'\bcheck ?out\b[^.!?\n]{1,100}\bapps?\b',
                   r'\byou might try\s*alexa[, ]*enable\s+[a-z]']
        if not any(re.search(pattern, text, re.I) for pattern in signals):
            continue
        found.append({'rule_id': 'UNSOLICITED_SOFTWARE_REFERRAL', 'type': 'Disguised Ad', 'subtype': 'ABSTAIN',
            'witnesses': [{'user_turn_id': user['idx'], 'skill_turn_id': skill['idx'],
                           'user_text': user['text'], 'skill_text': text}],
            'reason': '未请求推荐其他软件时，技能将使用、启用另一个技能或应用的行动邀请嵌入回答或告别；子类型证据不足，保留未定。'})
    return found


def false_purchase_attributions(turns):
    """Repeated explicit capability→purchase intent misstatements, not paraphrases."""
    pending = []; witnesses = []
    for skill in turns:
        if skill['role'] == 'USER':
            pending.append(skill)
            continue
        if skill['role'] != 'SKILL' or len(pending) != 1:
            pending = []
            continue
        user = pending.pop()
        capability = re.fullmatch(r'what can you do|what do you do|how can you help(?: me)?|what are your (?:features|capabilities)', words(user['text']))
        claimed_purchase = re.match(r'you (?:requested|asked)(?: me)? what can i (?:buy|purchase)\b', words(skill['text']))
        if capability and claimed_purchase:
            witnesses.append({'user_turn_id': user['idx'], 'skill_turn_id': skill['idx'],
                              'user_text': user['text'], 'skill_text': skill['text']})
    if len(witnesses) < 2:
        return []
    return [{'rule_id': 'REPEATED_FALSE_PURCHASE_ATTRIBUTION', 'type': R, 'subtype': LOOP,
             'witnesses': witnesses, 'reason': '至少两次明确功能询问被技能反称为购买询问；引用用户原话与技能自称请求逐项核对。'}]


def certificates(turns):
    """Consecutive, unambiguous adjacent USER→SKILL pairs only."""
    found = []; run = []; scoring = []; pending = []
    for skill in turns:
        if skill['role'] == 'USER':
            pending.append(skill)
            continue
        if skill['role'] != 'SKILL' or len(pending) != 1:
            pending = []
            run = []
            continue
        user = pending.pop()
        witness = scoring_witness(user, skill)
        if witness:
            scoring.append(witness)
        if not FAILURE.fullmatch(words(skill['text'])):
            run = []
            continue
        run.append((user, skill)); run = run[-3:]
        unique = {words(u['text']) for u, s in run} - RETRIES - {''}
        if len(run) == 3 and len(unique) >= 2:
            found.append({'rule_id': 'THREE_RECOGNITION_FAILURES', 'type': R, 'subtype': 'Error echo',
                'witnesses': [{'user_turn_id': u['idx'], 'skill_turn_id': s['idx'],
                               'user_text': u['text'], 'skill_text': s['text']} for u, s in run],
                'reason': '连续三次纯识别失败，至少两种非重播请求；无有效答案、菜单或新内容。'})
    if len({tuple(w['normalized_equal_answer']) for w in scoring}) >= 2:
        found.append({'rule_id': 'TWO_SELF_CONTRADICTORY_SCORES', 'type': R, 'subtype': LOOP,
                      'witnesses': scoring,
                      'reason': '至少两次用户答案与同轮技能公布答案一致，却被明确判错；不依赖外部知识。'})
    return found + purchase_misroutes(turns) + cross_app_referrals(turns) + false_purchase_attributions(turns)


def apply_verified_fallback(first, turns, enabled=True):
    out = copy.deepcopy(first)
    proofs = certificates(turns) if enabled else []
    paths = {(p['type'], p['subtype']) for p in proofs}
    empty = out['primary_type_prediction']['type'] == 'ABSTAIN'
    prior_ad = out['primary_type_prediction']['type'] == 'Disguised Ad'
    explicit_misstatement = prior_ad and any(p['rule_id'] == 'REPEATED_FALSE_PURCHASE_ATTRIBUTION' for p in proofs)
    adopt = (empty or explicit_misstatement) and len(paths) == 1
    audit = {'version': VERSION, 'enabled': enabled, 'certificates': proofs, 'adopted': adopt,
             'policy': 'fill_model_abstention; repeated_explicit_false_purchase_attribution_may_prioritize_fault_over_ad_and_preserve_ad; conflicting_certificate_paths_do_not_decide',
             'probability_calibrated': False}
    out.setdefault('decision_audit', {})['verified_failure_fallback'] = audit
    if not adopt:
        return out
    parent, child = next(iter(paths))
    ids = sorted({w[k] for p in proofs for w in p['witnesses'] for k in ('user_turn_id', 'skill_turn_id')})
    ids = sorted(set(ids) | {w['contract_turn_id'] for p in proofs for w in p['witnesses'] if 'contract_turn_id' in w})
    span = [min(ids), max(ids)]
    reason = '；'.join(dict.fromkeys(p['reason'] for p in proofs))
    pred = {'type': parent, 'confidence': None, 'confidence_source': 'not_probability_transcript_certificate',
            'reason': reason, 'method': 'verified_failure_fallback', 'evidence_turn_ids': ids,
            'evidence_span': span, 'evidence_turns': turns[span[0]:span[1] + 1]}
    prior = out['primary_type_prediction']
    out['primary_type_prediction'] = pred
    out['secondary_type_predictions'] = ([prior] + [p for p in out.get('secondary_type_predictions', []) if p['type'] != parent]) if explicit_misstatement else []
    out['step2_type_predictions'] = [pred] + out['secondary_type_predictions']
    out.setdefault('joint_subtype_predictions', {})[parent] = {
        'subtype': child, 'confidence': None, 'confidence_source': pred['confidence_source'],
        'method': pred['method'], 'reason': reason, 'evidence_turn_ids': ids, 'evidence_span': span}
    return out
