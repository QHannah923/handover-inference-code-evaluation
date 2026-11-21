"""Independent transcript certificates; no labels, filenames or model scores.

Rules normally fill an empty model decision. Repeated explicit false purchase
attribution can prioritize a proven routing fault while retaining a prior ad.
Certificate validity is a narrow text relation, not a calibrated accuracy score.
"""
import copy
import re

R = 'Repeated/Confused Output'
LOOP = 'Misleading loop (skills bug) (Repeated prompts)'
VERSION = 'nonpurchase_notice_and_social_boundary_20261120'
FEED = 'Feedforward Ambiguity (No help guidance / Unspoken options / Feedforward Ambiguity)'
D = 'Disguised Ad'
W = 'Watch Ads/Pay to Avoid Ads'
MERGED = 'Product embedding / Native advertising'
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


def paired(turns):
    pending = []
    for t in turns:
        if t['role'] == 'USER':
            pending.append(t)
            continue
        if t['role'] == 'SKILL' and len(pending) == 1:
            yield pending[0], t
        pending = []


def context_certificates(turns):
    ps = list(paired(turns)); found = []; controls = []
    def witness(u, s, contract=None):
        v = {'user_turn_id': u['idx'], 'skill_turn_id': s['idx'], 'user_text': u['text'], 'skill_text': s['text']}
        if contract:
            v.update(contract_turn_id=contract['idx'], contract_text=contract['text'])
        return v
    def add(rid, parent, child, evidence, reason):
        found.append({'rule_id': rid, 'type': parent, 'subtype': child, 'witnesses': evidence, 'reason': reason})
    for pos, (u, s) in enumerate(ps):
        request = words(u['text']); text = s['text']; normalized = words(text)
        if re.search(r'\bbecause you (?:have )?used this (?:skill|app)\b.{0,100}\byou should also (?:use|try|enable)\s+\w+', text, re.I):
            add('CAUSAL_CROSS_RECOMMENDATION', D, 'Biased recommendation', [witness(u, s)],
                '把用户用了当前技能当作应该使用另一个指定技能的理由，构成定向偏向推荐。')
        no_stock = re.search(r"(?:there (?:isn t|is not|aren t|are not) (?:anything|any (?:products?|items?|content))|nothing|no (?:products?|items?|content)).{0,55}(?:available|buy|purchase|offer)", normalized)
        handoff = re.search(r'\b(?:resuming|returning|other help|anything else|what can i help|happy to|did you want)\b', normalized)
        if re.search(r'\b(?:what can i buy|what.*(?:purchase|buy)|show.*(?:menu|products?))\b', request) and no_stock and handoff:
            offers = [t for t in turns if t['role'] == 'SKILL' and t['idx'] < u['idx'] and re.search(r'\byou can buy\b|\b(?:we have|available for purchase|offer you)\b', t['text'], re.I)]
            if offers:
                add('OFFER_QUERY_DENIAL', R, FEED, [witness(u, s, offers[-1])],
                    '先说有可买的内容，用户按指引咨询后又说没有，并转去其他帮助；按用户新定义属于错误指导。')
        if request in {'pause', 'resume', 'continue playback'} and len(normalized.split()) >= 16:
            acknowledged = re.search(r'\b(?:paus\w*|resum\w*|standby|standing by|continu\w*|cannot|can t|not supported|you can|say|please|would you like)\b', normalized)
            if not acknowledged:
                controls.append((u, s))
        if request in {'pause', 'resume', 'stop'} and re.search(r'\bwhich\b.{0,65}\b(?:like|want|choose)\b', text, re.I):
            for next_u, next_s in ps[pos + 1:pos + 3]:
                if re.search(r'\b(?:shopping cart|buy this|purchase this|order now)\b', next_s['text'], re.I):
                    prior_buy = any(re.search(r'\b(?:buy|purchase|order|price)\b', a['text'], re.I) for a, b in ps[:pos + 1])
                    if not prior_buy:
                        add('CONTROL_TO_SALES_MENU', D, MERGED, [witness(u, s), witness(next_u, next_s)],
                            '控制请求被转入商品选择，后续引导购物车或购买；后来的商品选择不追溯授权最初销售插入。')
                    break
        if re.search(r"here.?s your question(?: again)?\s*:\s*[a-z]?[.\s]*$", text, re.I) and pos + 1 < len(ps):
            next_u, next_s = ps[pos + 1]
            if re.fullmatch(r'repeat(?: the)? question', words(next_u['text'])) and re.fullmatch(r'[\s.!?,;:]*', next_s['text']):
                add('BROKEN_QUESTION_AND_REPLAY', R, LOOP, [witness(u, s), witness(next_u, next_s)],
                    '声称给出题目却只有残片，用户要求重播后仍只有标点；有完整文本证据显示答题无法继续。')
    for a, b in zip(controls, controls[1:]):
        if words(a[0]['text']) != words(b[0]['text']) and a[1]['text'] == b[1]['text']:
            add('CONTROL_INTENT_SUBSTITUTION', R, LOOP, [witness(*a), witness(*b)],
                '两个不同播放控制请求收到同一段较长的信息介绍，回复没有处理控制、说明不支持或提供有效控制指导。')
            break
    return found


def unsolicited_sales_certificates(turns):
    """Explicit named-product opening and repeated upsell after distinct tasks.
    A purchase-options menu or a single optional extension is insufficient.
    """
    ps = list(paired(turns)); found = []; offers = {}
    for pos, (user, skill) in enumerate(ps):
        request = words(user['text']); text = skill['text']
        commercial_request = re.search(r'\b(?:buy|purchase|order|price|cost|premium|subscribe|subscription|about|learn more)\b', request)
        witness = {'user_turn_id': user['idx'], 'skill_turn_id': skill['idx'], 'user_text': user['text'], 'skill_text': text}
        if pos == 0 and re.match(r'^(?:alexa )?(?:open|launch|start)\b', request) and not commercial_request:
            direct = re.search(r'\b(?:you can buy|or buy|say[, ]+buy)\s+(?!something\b|anything\b|products?\b|items?\b|it\b|this\b|that\b)([a-z][a-z ]{2,70})(?=[.!?]|$)', text, re.I)
            conditional_instruction = re.search(r'\bif (?:at any time )?you (?:want|wish|would like) to buy\b', text, re.I)
            if direct and not conditional_instruction:
                found.append({'rule_id': 'UNREQUESTED_NAMED_PRODUCT_OPENING', 'type': D, 'subtype': MERGED,
                              'witnesses': [witness], 'reason': '用户仅启动技能、尚未询价，开场直接招揽购买具体命名产品；按用户新增判据归伪装广告，普通购买选项或帮助说明不算。'})
        if commercial_request:
            offers = {}
            continue
        if not request or re.search(r'[<>\[\]]', user['text']) or re.fullmatch(r'help|options|repeat|again|yes|no', request):
            continue
        offer = re.search(r'\byou can buy\s+([^.!?\n]{2,70})[.!?]', text, re.I)
        prefix = text[:offer.start()] if offer else ''
        optional = re.search(r'\bif you (?:want|would like) to (?:know|learn|hear) more\b', prefix, re.I)
        if offer and optional and len(prefix.split()) >= 12:
            target = words(offer.group(1)); offers.setdefault(target, []).append(witness)
            group = offers[target]
            if len({words(w['user_text']) for w in group}) >= 3:
                found.append({'rule_id': 'REPEATED_UNREQUESTED_SAME_PRODUCT_UPSELL', 'type': D, 'subtype': MERGED,
                              'witnesses': list(group), 'reason': '至少三个不同非购买请求的回答中，都先提供实际内容再反复推销同一产品；用户未主动咨询该扩展，单次可选升级不触发。'})
    return found


def noncommercial_notice_exclusion(turns):
    """Narrow operational negatives: completed task plus nonpurchase notice,
    or a terminal social sign-off. Every other commercial trace vetoes them.
    These are transcript contracts, not a claim that all optional sales are safe.
    """
    ps = list(paired(turns))
    commercial = re.compile(r'\b(?:buy|purchase|pay|paid|price|cost|dollars?|premium|subscribe|subscription|membership|commission|sponsor|advert|book|products?|sale|shopping|download|install|enable|recommend|visit|instagram|facebook|tiktok|youtube)\b|check\s*out|https?://|www\.|dot com', re.I)
    notice = re.compile(r'^\s*You currently do not have our [a-z ]{1,45} product\.\s*If you wish to hear more about it say, [a-z ]{1,60}\.\s*', re.I)
    notices = []; residual = []; completed = True
    for user, skill in ps:
        match = notice.match(skill['text'])
        rest = skill['text'][match.end():] if match else skill['text']
        residual.append(rest)
        if match:
            notices.append(skill)
            completed = completed and len(rest.split()) >= 30 and bool(re.search(r'\byou can say\b.+\bwhat can i help\b', rest, re.I))
    later_progress = notices and any(s['idx'] > notices[-1]['idx'] and not notice.match(s['text']) and len(s['text'].split()) >= 25 and not re.fullmatch(r'help|options|repeat|again', words(u['text'])) for u, s in ps)
    if notices and completed and later_progress and not commercial.search(' '.join(residual)):
        return {'rule_id': 'OPTIONAL_NONPURCHASE_NOTICE_WITH_TASK_COMPLETION', 'excluded_types': [D],
                'evidence_turn_ids': [s['idx'] for s in notices] + [ps[-1][1]['idx']],
                'reason': '仅提示尚未拥有可了解的功能，无价格、购买、外部引流等其他商业证据；提示同轮保留完整任务内容与操作指引，后续任务继续。按人工操作口径排除这类非购买提示。'}
    if not ps:
        return None
    user, skill = ps[-1]
    social = re.compile(r'(?:(?:be sure to|you can)\s+)?check us out on (?:instagram|facebook|tiktok|youtube) at [^.?!\n]{1,80}[.?!]', re.I)
    match = social.search(skill['text'])
    if words(user['text']) not in {'stop', 'quit', 'exit', 'cancel', 'goodbye'} or turns[-1] != skill or not match or len(skill['text'].split()) > 60:
        return None
    rest = skill['text'][:match.start()] + skill['text'][match.end():]
    all_other = ' '.join(t['text'] for t in turns if t['role'] == 'SKILL' and t['idx'] != skill['idx']) + ' ' + rest
    thanks = re.search(r'\b(?:thank you|thanks|goodbye|bye)\b', rest, re.I)
    if thanks and not commercial.search(all_other) and not re.search(r'\b(?:buy|sale|discount|shop|premium|pay|subscribe|must|required|free gift)\b', match.group(), re.I):
        return {'rule_id': 'TERMINAL_SOCIAL_SIGNOFF_ONLY', 'excluded_types': [D],
                'evidence_turn_ids': [user['idx'], skill['idx']],
                'reason': '停止后的短告别仅给出自有社交账号，没有商品、价格、订阅、奖励或其他商业证据，且不再继续交互；按人工操作口径排除纯社交告别。'}
    return None


def free_extension_exclusion(turns, proofs):
    """Independent negative policy for internal optional paid extensions only."""
    if any(p['type'] == D for p in proofs):
        return None
    notice_exclusion = noncommercial_notice_exclusion(turns)
    if notice_exclusion:
        return notice_exclusion
    ps = list(paired(turns)); sales = [(u, s) for u, s in ps if re.search(r'\b(?:buy|purchase|premium|subscription|membership|annual|monthly pass|unlimited|full versions)\b|\bmore than [1-9]\d* (?:games?|questions?) (?:a|per) day\b', s['text'], re.I)]
    if not sales or not all(re.search(r'\b(?:packs?|premium|subscription|membership|pass|unlimited|full versions)\b|\bmore than [1-9]\d* (?:games?|questions?) (?:a|per) day\b', s['text'], re.I) for u, s in sales):
        return None
    combined = ' '.join(s['text'] for u, s in sales)
    if re.search(r'\b(?:book|commission|website|shopping cart)\b|qualifying purchases|www\.|dot com', combined, re.I):
        return None
    if re.search(r'\b(?:must|have to|required to)\b.{0,45}\b(?:pay|subscribe|listen|watch)\b|\b(?:can.?t|cannot) continue\b', combined, re.I):
        return None
    requested = lambda text: bool(re.search(r'\b(?:buy|purchase|premium|subscription|membership|packs?|annual|monthly|learn more about)\b', text, re.I))
    for pos, (u, s) in enumerate(ps):
        if pos and re.fullmatch(r'no(?: thanks)?', words(u['text'])) and re.search(r'\b(?:buy|purchase|products?|packs?|premium)\b', ps[pos - 1][1]['text'], re.I):
            accepted = re.search(r'\b(?:continue|daily quiz|what feature|what would you like to do|no problem)\b', s['text'], re.I)
            repeated = any(b['idx'] > s['idx'] and not requested(a['text']) for a, b in sales)
            if accepted and not repeated:
                return {'rule_id': 'OPTIONAL_EXTENSION_DECLINE_HONORED', 'excluded_types': [D, W],
                        'evidence_turn_ids': [ps[pos - 1][1]['idx'], u['idx'], s['idx']],
                        'reason': '付费是内部扩展，用户拒绝后仍能选择基础流程；后续没有未经请求再次推销，按新定义不凭这类销售判暗黑模式。'}
    quota = [(u, s) for u, s in sales if re.search(r'\bmore than [1-9]\d* (?:games?|questions?) (?:a|per) day\b', s['text'], re.I) and re.search(r'would you like to find out more', s['text'], re.I)]
    if quota:
        cutoff = quota[0][1]['idx']
        progress = [s for u, s in ps if s['idx'] < cutoff and len(s['text'].split()) >= 25 and re.search(r'\d', s['text']) and not re.search(r'\b(?:buy|purchase|premium|subscription)\b', s['text'], re.I)]
        if len(progress) >= 2:
            return {'rule_id': 'FREE_QUOTA_OPTIONAL_EXTENSION', 'excluded_types': [D, W],
                    'evidence_turn_ids': [progress[0]['idx'], progress[1]['idx'], quota[0][1]['idx']],
                    'reason': '基础游戏已多轮正常进行，推广明确只是增加每日使用次数的可选付费扩展；按用户定义，这种免费加付费本身不是暗黑模式。'}
    return None


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
    return found + purchase_misroutes(turns) + cross_app_referrals(turns) + false_purchase_attributions(turns) + context_certificates(turns) + unsolicited_sales_certificates(turns)


def apply_verified_fallback(first, turns, enabled=True):
    out = copy.deepcopy(first)
    proofs = certificates(turns) if enabled else []
    exclusion = free_extension_exclusion(turns, proofs) if enabled else None
    excluded = set(exclusion['excluded_types']) if exclusion else set()
    if out['primary_type_prediction']['type'] in excluded:
        eligible = [p for p in out.get('step2_type_predictions', []) if p['type'] not in excluded and p['type'] != 'ABSTAIN' and (p.get('confidence') or 0) >= .8]
        out['primary_type_prediction'] = eligible[0] if eligible else {'type': 'ABSTAIN', 'confidence': None,
            'confidence_source': 'not_probability_independent_policy_exclusion', 'method': 'rule_policy_exclusion',
            'reason': exclusion['reason'], 'evidence_turn_ids': exclusion['evidence_turn_ids'], 'evidence_span': None, 'evidence_turns': []}
        out['secondary_type_predictions'] = eligible[1:]
        out['step2_type_predictions'] = eligible or [out['primary_type_prediction']]
    typed = {}
    for proof in proofs:
        typed.setdefault(proof['type'], []).append(proof)
    paths = set()
    for parent, items in typed.items():
        children = {p['subtype'] for p in items if p['subtype'] != 'ABSTAIN'}
        paths.add((parent, next(iter(children)) if len(children) == 1 else 'ABSTAIN'))
    empty = out['primary_type_prediction']['type'] == 'ABSTAIN'
    prior_ad = out['primary_type_prediction']['type'] == 'Disguised Ad'
    fault_ids = {'REPEATED_FALSE_PURCHASE_ATTRIBUTION', 'OFFER_QUERY_DENIAL', 'BROKEN_QUESTION_AND_REPLAY', 'CONTROL_INTENT_SUBSTITUTION'}
    explicit_misstatement = prior_ad and any(p['rule_id'] in fault_ids for p in proofs)
    if explicit_misstatement:
        paths = {p for p in paths if p[0] == R}
        proofs = [p for p in proofs if p['type'] == R]
    refine_child = prior_ad and any(p['rule_id'] == 'CAUSAL_CROSS_RECOMMENDATION' for p in proofs)
    adopt = (empty or explicit_misstatement or refine_child) and len(paths) == 1
    audit = {'version': VERSION, 'enabled': enabled, 'certificates': proofs, 'adopted': adopt,
             'exclusion': exclusion, 'policy': 'independent_optional_extension_exclusion; fill_abstention; explicit_fault_before_ad; causal_recommendation_refines_ad_child; unresolved_children_remain_abstained',
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
