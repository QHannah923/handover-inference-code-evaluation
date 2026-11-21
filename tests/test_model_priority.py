"""Verify routing and frozen prompts without making any API requests."""
import ast
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dark-pattern'))
os.environ.setdefault('OPENAI_API_KEY', 'routing-test-no-network')
import decision_policy as policy
import interface_interference_type as types
import interface_interference_subtype as subtypes


def pred(label, confidence, method='llm'):
    return {'type': label, 'confidence': confidence, 'method': method}


class RoutingTests(unittest.TestCase):
    def setUp(self):
        for module in (types, subtypes):
            change = patch.object(module, "PROFILE", "model_priority")
            change.start()
            self.addCleanup(change.stop)

    def test_gpt6_compatible_parameters(self):
        from experiment_config import completion_parameters
        self.assertEqual(completion_parameters('gpt-6-astra'), {'reasoning_effort': 'low'})
        self.assertEqual(completion_parameters('gpt-4o'), {'temperature': 0})

    def test_keyword_rule_does_not_skip_models(self):
        turns = [{'role': 'SKILL', 'text': 'Upgrade to premium.', 'idx': 0}]
        with patch.object(types, 'detect_repeated_output_llm', return_value=[]) as repeat, \
             patch.object(types, 'detect_disguised_ad_llm', return_value=[pred('Disguised Ad', .85)]) as ad:
            result = types.classify_interface_interference_type(turns)
        repeat.assert_called_once()
        ad.assert_called_once()
        self.assertEqual(result['primary_type_prediction']['type'], 'Disguised Ad')
        self.assertTrue(result['decision_audit']['rule_candidates'])

    def test_weak_rules_do_not_turn_model_abstention_into_positive(self):
        self.assertEqual(policy.rank_candidates([], [pred('Watch Ads/Pay to Avoid Ads', .99, 'rule')], [], 'type'), [])

    def test_high_rating_score_requires_direct_evidence(self):
        self.assertEqual(policy.rank_candidates([], [pred('Voice-Guided Rating', .95, 'rule')], [], 'type'), [])

    def test_explicit_strong_rule_can_override(self):
        turns = [{'role': 'SKILL', 'text': 'Please give us five stars.'}]
        ranked = policy.rank_candidates([pred('Disguised Ad', .99)], [pred('Voice-Guided Rating', .95, 'rule')], turns, 'type')
        self.assertEqual(ranked[0]['type'], 'Voice-Guided Rating')
        self.assertTrue(ranked[0]['strong_rule_override'])

    def test_subtype_model_runs_despite_rule(self):
        turns = [{'role': 'SKILL', 'text': 'Premium subscription upgrade', 'idx': 0}]
        model = {'subtype': 'Mandatory ads', 'confidence': .85, 'method': 'llm'}
        step2 = {'primary_type_prediction': {'type': 'Watch Ads/Pay to Avoid Ads', 'evidence_span': [0, 0]}}
        with patch.object(subtypes, '_llm_pick_watch_ads_subtype', return_value=model) as pick:
            result = subtypes.classify_interface_interference_subtype(turns, step2)
        pick.assert_called_once()
        self.assertEqual(result['subtype'], 'Mandatory ads')
        self.assertTrue(result['decision_audit']['rule_candidates'])

    def test_low_confidence_model_still_abstains(self):
        with patch.object(types, 'detect_repeated_output_llm', return_value=[pred('Repeated/Confused Output', .7)]), \
             patch.object(types, 'detect_disguised_ad_llm', return_value=[]):
            self.assertEqual(types.classify_interface_interference_type([])['primary_type_prediction']['type'], 'ABSTAIN')

    def test_original_prompts_unchanged(self):
        def prompts(path):
            tree = ast.parse(path.read_text())
            return [ast.dump(n.value, include_attributes=False) for n in ast.walk(tree)
                    if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'prompt' for t in n.targets)]
        for name in ('interface_interference_type.py', 'interface_interference_subtype.py'):
            before = ROOT / 'tests/fixtures/legacy_prompts' / name
            self.assertEqual(prompts(before), prompts(ROOT / 'dark-pattern' / name))

    def test_legacy_profile_retains_short_circuit(self):
        turns = [{'role': 'SKILL', 'text': 'Upgrade to premium.', 'idx': 0}]
        with patch.object(types, 'PROFILE', 'legacy'), patch.object(types, 'detect_disguised_ad_llm') as ad:
            result = types.classify_interface_interference_type(turns)
        ad.assert_not_called()
        self.assertEqual(result['primary_type_prediction']['type'], 'Watch Ads/Pay to Avoid Ads')

if __name__ == '__main__':
    unittest.main(verbosity=2)
