"""Synthetic counterexamples and production entry point, no network/gold labels."""
import copy
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dark-pattern'))
os.environ.setdefault('OPENAI_API_KEY', 'offline-test')
from verified_failure_rules import certificates, apply_verified_fallback, R, LOOP


def turns(*texts):
    return [{'idx': i, 'role': 'USER' if i % 2 == 0 else 'SKILL', 'text': t} for i, t in enumerate(texts)]


def empty():
    return {'primary_type_prediction': {'type': 'ABSTAIN'}, 'joint_subtype_predictions': {}, 'decision_audit': {}}


class CertificateTests(unittest.TestCase):
    def test_variable_word_errors(self):
        ts = turns('help', "Sorry, I can't understand the command. Please say again.", 'again',
                   "Sorry, I can't understand the command. Please say again.", 'search products',
                   "I'm sorry. I didn't understand. Could you please repeat that.")
        proofs = certificates(ts)
        self.assertEqual(proofs[0]['subtype'], 'Error echo')
        self.assertEqual(len(proofs[0]['witnesses']), 3)

    def test_user_repeated_command_not_diversity(self):
        ts = turns('help', "I didn't understand.", 'help', "I didn't understand.", 'repeat', "I didn't understand.")
        self.assertEqual(certificates(ts), [])

    def test_new_answer_or_help_breaks_run(self):
        for middle in ["The price is seven dollars.", 'Say fact or stop.', 'What day?', "I didn't understand. Say next fact or stop."]:
            ts = turns('help', "I didn't understand.", 'options', middle, 'start', "I didn't understand.")
            self.assertEqual(certificates(ts), [])

    def test_similarity_and_replay_are_not_failure(self):
        ts = turns('repeat', 'Fact one: rivers flow.', 'repeat', 'Fact one: rivers flow.', 'repeat', 'Fact one: rivers flow.')
        self.assertEqual(certificates(ts), [])
        ts = turns('next', 'Fact one: rivers flow.', 'more', 'Fact two: rivers erode.', 'again', 'Fact three: rivers meet oceans.')
        self.assertEqual(certificates(ts), [])

    def test_other_or_ambiguous_users_break_continuity(self):
        ts = turns('help', "I didn't understand.", 'options', "I didn't understand.", 'start', "I didn't understand.")
        for extra in [{'idx': 99, 'role': 'OTHER', 'text': 'system event'}, {'idx': 99, 'role': 'USER', 'text': 'another request'}]:
            changed = ts[:4] + [extra] + ts[4:]
            self.assertEqual(certificates(changed), [])

    def test_two_self_disclosed_scoring_failures(self):
        ts = turns('amendment 3', 'Incorrect. The Third Amendment prohibits something.',
                   'eighth amendment', 'Incorrect. The Eighth Amendment protects something.')
        proof = certificates(ts)[0]
        self.assertEqual(proof['subtype'], LOOP)
        self.assertEqual(proof['witnesses'][0]['normalized_equal_answer'], ['amendment', '3'])

    def test_generic_correct_answer_grammar(self):
        ts = turns('Paris', 'Wrong. The correct answer is Paris.', 'eight', 'Incorrect. Correct answer is 8.')
        self.assertEqual(certificates(ts)[0]['subtype'], LOOP)

    def test_one_failure_duplicate_or_wrong_answer_insufficient(self):
        cases = [turns('Paris', 'Wrong. The correct answer is Paris.'),
                 turns('Paris', 'Wrong. The correct answer is Paris.', 'Paris', 'Wrong. The correct answer is Paris.'),
                 turns('London', 'Wrong. The correct answer is Paris.', 'three', 'Incorrect. The Eighth Amendment protects something.')]
        for ts in cases:
            self.assertEqual(certificates(ts), [])

    def test_no_external_knowledge_and_no_quote_false_positive(self):
        ts = turns('Paris', 'Correct! Paris is the capital.', 'eight', 'A user once said incorrect. The correct answer is eight.')
        self.assertEqual(certificates(ts), [])

    def test_rule_only_fills_empty_model_and_keeps_source_immutable(self):
        ts = turns('Paris', 'Wrong. The correct answer is Paris.', 'eight', 'Incorrect. Correct answer is 8.')
        source = empty(); frozen = copy.deepcopy(source)
        out = apply_verified_fallback(source, ts)
        self.assertEqual(source, frozen)
        self.assertEqual(out['primary_type_prediction']['type'], R)
        self.assertIsNone(out['primary_type_prediction']['confidence'])
        self.assertEqual(apply_verified_fallback(source, ts, enabled=False)['primary_type_prediction']['type'], 'ABSTAIN')
        source['primary_type_prediction']['type'] = 'Disguised Ad'
        self.assertEqual(apply_verified_fallback(source, ts)['primary_type_prediction']['type'], 'Disguised Ad')

    def test_conflicting_certificates_do_not_fill(self):
        ts = turns('help', "I didn't understand.", 'options', "I didn't understand.", 'start', "I didn't understand.",
                   'Paris', 'Wrong. The correct answer is Paris.', 'eight', 'Incorrect. Correct answer is 8.')
        out = apply_verified_fallback(empty(), ts)
        self.assertEqual(out['primary_type_prediction']['type'], R)
        self.assertEqual(out['joint_subtype_predictions'][R]['subtype'], 'ABSTAIN')

    def test_production_calls_model_first_and_reuses_child(self):
        import interface_interference_type as types
        import interface_interference_subtype as children
        import interface_interference_prompt_v2 as joint
        ts = turns('Paris', 'Wrong. The correct answer is Paris.', 'eight', 'Incorrect. Correct answer is 8.')
        with patch.object(types, 'PROFILE', 'verified_failure_fallback'), \
             patch.object(joint, 'classify_joint', return_value=empty()) as model:
            out = types.classify_interface_interference_type(ts)
        model.assert_called_once()
        with patch.object(children, 'PROFILE', 'verified_failure_fallback'):
            self.assertEqual(children.classify_interface_interference_subtype(ts, out)['subtype'], LOOP)

    def test_two_different_questions_misrouted_to_purchase(self):
        ts = turns('start', 'Question 1. Guess the landmark.', 'a tower',
                   "I am sorry but we couldn't identify the product you want to purchase. Please try again.",
                   'next', 'Question 2. Answer with a city.', 'a port city',
                   "I am sorry but we couldn't identify the product you want to purchase. Please try again.")
        proof = next(p for p in certificates(ts) if p['rule_id'] == 'TWO_QUIZ_PURCHASE_MISROUTES')
        self.assertEqual([w['contract_turn_id'] for w in proof['witnesses']], [1, 5])
        out = apply_verified_fallback(empty(), ts)
        self.assertEqual(out['joint_subtype_predictions'][R]['subtype'], LOOP)
        self.assertEqual(out['primary_type_prediction']['evidence_turn_ids'], [1, 2, 3, 5, 6, 7])

    def test_purchase_misroute_requires_two_distinct_question_contracts(self):
        ts = turns('start', 'Question 1. Guess the landmark.', 'a tower',
                   "I am sorry but we couldn't identify the product you want to purchase.", 'a city',
                   "I am sorry but we couldn't identify the product you want to purchase.")
        self.assertFalse(any(p['rule_id'] == 'TWO_QUIZ_PURCHASE_MISROUTES' for p in certificates(ts)))

    def test_explicit_purchase_and_placeholders_do_not_count(self):
        for request in ['buy extra questions', 'what can I buy', '<answer placeholder>', '[previous statement]']:
            ts = turns('start', 'Question 1. Guess the landmark.', request,
                       "I am sorry but we couldn't identify the product you want to purchase.",
                       'next', 'Question 2. Answer with a city.', request,
                       "I am sorry but we couldn't identify the product you want to purchase.")
            self.assertFalse(any(p['rule_id'] == 'TWO_QUIZ_PURCHASE_MISROUTES' for p in certificates(ts)))

    def test_purchase_without_quiz_or_after_quiz_end_is_not_misroute(self):
        error = "I am sorry but we couldn't identify the product you want to purchase."
        for prompt in ['Which product do you want?', 'Thank you for playing. Would you like to buy extra questions?']:
            ts = turns('start', 'Question 1. Guess the landmark.', 'done', prompt, 'yes', error,
                       'next', 'Question 2. Answer with a city.', 'done', prompt, 'yes', error)
            self.assertFalse(any(p['rule_id'] == 'TWO_QUIZ_PURCHASE_MISROUTES' for p in certificates(ts)))

    def test_commercial_menu_resets_quiz_contract(self):
        error = "I am sorry but we couldn't identify the product you want to purchase."
        ts = turns('start', 'Question 1. Guess the landmark.', 'help', 'Here are our premium packs.', 'yes', error,
                   'next', 'Question 2. Answer with a city.', 'help', 'Here are our premium packs.', 'yes', error)
        self.assertFalse(any(p['rule_id'] == 'TWO_QUIZ_PURCHASE_MISROUTES' for p in certificates(ts)))

    def test_misroute_rejects_quoted_examples_and_keeps_existing_positive(self):
        ts = turns('start', 'Question 1. Guess the landmark.', 'a tower',
                   "Example error: I am sorry but we couldn't identify the product you want to purchase.",
                   'next', 'Question 2. Answer with a city.', 'a port city',
                   "Example error: I am sorry but we couldn't identify the product you want to purchase.")
        self.assertFalse(any(p['rule_id'] == 'TWO_QUIZ_PURCHASE_MISROUTES' for p in certificates(ts)))
        ts[3]['text'] = ts[3]['text'].removeprefix('Example error: ')
        ts[7]['text'] = ts[7]['text'].removeprefix('Example error: ')
        source = empty(); source['primary_type_prediction']['type'] = 'Disguised Ad'
        self.assertEqual(apply_verified_fallback(source, ts)['primary_type_prediction']['type'], 'Disguised Ad')

    def test_unsolicited_referrals_keep_child_unresolved(self):
        replies = ['Goodbye. Try out our sister skills.',
                   'Thank you for playing. For more questions check out the geography practice app.',
                   'Your result is blue. If you like this you might tryAlexa enable Color Wheel.']
        for response in replies:
            ts = turns('finish', response)
            out = apply_verified_fallback(empty(), ts)
            self.assertEqual(out['primary_type_prediction']['type'], 'Disguised Ad')
            self.assertEqual(out['joint_subtype_predictions']['Disguised Ad']['subtype'], 'ABSTAIN')

    def test_referrals_exclude_requested_help_and_recommendations(self):
        for request in ['help', 'recommend another app', 'suggest other skills', 'enable color wheel']:
            self.assertEqual(apply_verified_fallback(empty(), turns(request, 'Try out our sister skills.'))['primary_type_prediction']['type'], 'ABSTAIN')

    def test_referrals_exclude_platform_setup_and_generic_use(self):
        for response in ['Check out the Alexa app for account permissions.',
                         'You can say Alexa enable brief mode.',
                         'Because you used this skill you can ask for another fact.',
                         'Please open the app settings to grant permissions.']:
            self.assertEqual(apply_verified_fallback(empty(), turns('start', response))['primary_type_prediction']['type'], 'ABSTAIN')

    def test_referrals_do_not_override_existing_rating_or_ad(self):
        for parent in ['Voice-Guided Rating', 'Disguised Ad']:
            source = empty(); source['primary_type_prediction']['type'] = parent
            out = apply_verified_fallback(source, turns('finish', 'Try out our sister skills.'))
            self.assertEqual(out['primary_type_prediction']['type'], parent)

    def test_repeated_false_intent_retains_ad_as_secondary(self):
        ts = turns('what can you do', 'You requested what can I buy. Here are our products.',
                   'what can you do', 'You requested what can I buy. Here are our products.')
        source = empty(); source['primary_type_prediction'] = {'type': 'Disguised Ad', 'reason': 'Original sales evidence'}
        source['joint_subtype_predictions'] = {'Disguised Ad': {'subtype': 'Product embedding / Native advertising'}}
        out = apply_verified_fallback(source, ts)
        self.assertEqual(out['primary_type_prediction']['type'], R)
        self.assertEqual(out['secondary_type_predictions'][0], source['primary_type_prediction'])
        self.assertEqual(out['joint_subtype_predictions']['Disguised Ad'], source['joint_subtype_predictions']['Disguised Ad'])

    def test_single_false_intent_is_insufficient(self):
        ts = turns('what can you do', 'You requested what can I buy.')
        self.assertEqual(apply_verified_fallback(empty(), ts)['primary_type_prediction']['type'], 'ABSTAIN')

    def test_actual_purchase_and_quoted_examples_are_not_false_intent(self):
        for request,response in [('what can I buy', 'You requested what can I buy.'),
                                 ('what can you do', 'Example: You requested what can I buy.')]:
            ts = turns(request, response, request, response)
            self.assertFalse(any(p['rule_id'] == 'REPEATED_FALSE_PURCHASE_ATTRIBUTION' for p in certificates(ts)))

    def test_false_intent_does_not_replace_other_positive_parents(self):
        ts = turns('what can you do', 'You requested what can I buy.', 'how can you help me', 'You requested what can I buy.')
        for parent in ['Voice-Guided Rating', 'Watch Ads/Pay to Avoid Ads']:
            source = empty(); source['primary_type_prediction']['type'] = parent
            self.assertEqual(apply_verified_fallback(source, ts)['primary_type_prediction']['type'], parent)

    def test_false_intent_ablation_keeps_prior_ad(self):
        ts = turns('what can you do', 'You requested what can I buy.', 'how can you help me', 'You requested what can I buy.')
        source = empty(); source['primary_type_prediction']['type'] = 'Disguised Ad'
        self.assertEqual(apply_verified_fallback(source, ts, enabled=False)['primary_type_prediction']['type'], 'Disguised Ad')

    def test_causal_recommendation_is_directional_not_generic_topic(self):
        ts = turns('open facts', 'Because you used this skill you should also use Planet Facts.')
        out = apply_verified_fallback(empty(), ts)
        self.assertEqual(out['primary_type_prediction']['type'], 'Disguised Ad')
        self.assertEqual(out['joint_subtype_predictions']['Disguised Ad']['subtype'], 'Biased recommendation')
        self.assertFalse(any(p['rule_id']=='CAUSAL_CROSS_RECOMMENDATION' for p in certificates(turns('help', 'You should use the next button to continue.'))))

    def test_offer_query_denial_has_prior_offer_and_explicit_handoff(self):
        ts = turns('help', 'You can buy premium routines. Say what can I buy.', 'what can I buy',
                   "There isn't anything available for you to purchase. Resuming skill. Are you happy to continue?")
        out = apply_verified_fallback(empty(), ts)
        self.assertEqual(out['joint_subtype_predictions'][R]['subtype'], 'Feedforward Ambiguity (No help guidance / Unspoken options / Feedforward Ambiguity)')
        self.assertEqual(certificates(ts[2:]), [])
        self.assertEqual(certificates(turns('help', 'You can buy premium routines.', 'what can I buy', 'Products available for purchase at this time are . What can I help you with?')), [])

    def test_different_controls_same_unrelated_information(self):
        response='Training a model uses compute resources. The provider charges a fee for training and simulation depending on time and usage.'
        ts=turns('pause',response,'what is training','Training learns from examples.','resume',response)
        self.assertTrue(any(p['rule_id']=='CONTROL_INTENT_SUBSTITUTION' for p in certificates(ts)))
        for response in ['Standing by. Say resume to continue.', 'I cannot pause this task. You can say stop or ask a question.']:
            self.assertFalse(any(p['rule_id']=='CONTROL_INTENT_SUBSTITUTION' for p in certificates(turns('pause',response,'resume',response))))

    def test_control_menu_then_sales_requires_unsolicited_purchase(self):
        ts=turns('pause','We have blue, red and green. Which would you like?', 'blue','Ask me to add this item to your shopping cart.')
        self.assertTrue(any(p['rule_id']=='CONTROL_TO_SALES_MENU' for p in certificates(ts)))
        self.assertFalse(any(p['rule_id']=='CONTROL_TO_SALES_MENU' for p in certificates(turns('buy a colour','Which colour?',*['pause',ts[1]['text'],'blue',ts[3]['text']]))))

    def test_broken_question_replay_not_missing_audio(self):
        ts=turns('continue',"Player 1, here's your question again: s.",'repeat the question','.')
        self.assertTrue(any(p['rule_id']=='BROKEN_QUESTION_AND_REPLAY' for p in certificates(ts)))
        ts[3]['text']='<Short audio>'
        self.assertFalse(any(p['rule_id']=='BROKEN_QUESTION_AND_REPLAY' for p in certificates(ts)))

    def test_free_extension_decline_removes_sales_only(self):
        ts=turns('start','You may buy extra question packs. Are you interested?', 'no','Would you like to play the daily quiz?')
        source=empty();source['primary_type_prediction']={'type':'Disguised Ad','confidence':.97};source['step2_type_predictions']=[source['primary_type_prediction']]
        out=apply_verified_fallback(source,ts)
        self.assertEqual(out['primary_type_prediction']['type'],'ABSTAIN')
        self.assertEqual(out['primary_type_prediction']['method'],'rule_policy_exclusion')
        self.assertIsNotNone(out['decision_audit']['verified_failure_fallback']['exclusion'])

    def test_free_extension_does_not_remove_external_ad_or_repeated_sales(self):
        source=empty();source['primary_type_prediction']={'type':'Disguised Ad','confidence':.97};source['step2_type_predictions']=[source['primary_type_prediction']]
        for ts in [turns('start','Buy our new book. Would you like it?', 'no','No problem. Continue?'),
                   turns('start','Try premium packs. Would you like to buy?', 'no','What feature do you want?', 'timer','Try premium packs. Would you like to buy?'),
                   turns('next','To continue you must pay for the premium pack.', 'no','No problem. Continue?')]:
            self.assertEqual(apply_verified_fallback(source,ts)['primary_type_prediction']['type'],'Disguised Ad')

    def test_free_quota_requires_real_prior_progress(self):
        narrative='Your answer changes the state. The total score is 10 and a new stage starts. Here is enough actual narrative content to explain what happened and ask another question.'
        sale='Full versions access would let you play more than 3 games a day. Would you like to find out more?'
        source=empty();source['primary_type_prediction']={'type':'Disguised Ad','confidence':.97};source['step2_type_predictions']=[source['primary_type_prediction']]
        self.assertEqual(apply_verified_fallback(source,turns('yes',narrative,'yes',narrative,'next',sale))['primary_type_prediction']['type'],'ABSTAIN')
        self.assertEqual(apply_verified_fallback(source,turns('yes','s.','repeat','.', 'next',sale))['primary_type_prediction']['type'],'Disguised Ad')


if __name__ == '__main__':
    unittest.main(verbosity=2)
