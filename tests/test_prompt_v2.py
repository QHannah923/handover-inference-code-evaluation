"""验证语境完整性、父子类型契约、异常处理及新入口；不调用接口。"""
import copy, json, os, sys, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dark-pattern'))
os.environ.setdefault('OPENAI_API_KEY', 'test-no-network')
import interface_interference_prompt_v2 as joint
import interface_interference_type as types
import interface_interference_subtype as subtypes

TURNS = [{'idx': 0, 'role': 'USER', 'text': 'Tell me about the service I selected.'},
         {'idx': 1, 'role': 'SKILL', 'text': 'Here are the details.'}]


def result(candidate=None):
    return {'type_checks': [{'type': name, 'present': bool(candidate and candidate['type'] == name),
                             'reason': 'synthetic contract fixture'} for name in joint.taxonomy()['types']],
            'candidates': [candidate] if candidate else [], 'negative_reason': '用户主动请求的信息。', 'quality_notes': []}


def fake_client(value):
    create = Mock(return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(value)))]))
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


class JointContractTests(unittest.TestCase):
    def test_full_ordered_context_in_request(self):
        payload = json.loads(joint.build_messages(TURNS)[1]['content'])
        self.assertEqual(payload['transcript'], TURNS)
        self.assertEqual(len(payload['taxonomy']['types']), 4)

    def test_no_missing_type_checks(self):
        v = result(); v['type_checks'].pop()
        with self.assertRaises(ValueError): joint.validate_result(v, TURNS)

    def test_parent_child_mismatch_rejected(self):
        v = result({'type': 'Disguised Ad', 'subtype': 'Rate us 5 stars', 'confidence': .95,
                    'evidence_turn_ids': [1], 'reason': 'fixture'})
        with self.assertRaises(ValueError): joint.validate_result(v, TURNS)

    def test_invalid_evidence_rejected(self):
        v = result({'type': 'Disguised Ad', 'subtype': 'Product embedding / Native advertising', 'confidence': .95,
                    'evidence_turn_ids': [99], 'reason': 'fixture'})
        with self.assertRaises(ValueError): joint.validate_result(v, TURNS)

    def test_positive_checks_cannot_silently_be_negative(self):
        v = result(); v['type_checks'][0]['present'] = True
        with self.assertRaises(ValueError): joint.validate_result(v, TURNS)

    def test_primary_abstain_is_explicit_model_negative(self):
        client = fake_client(result())
        first = joint.classify_joint(TURNS, [], [], client)
        self.assertEqual(first['primary_type_prediction']['type'], 'ABSTAIN')
        self.assertEqual(joint.subtype_from_joint(first)['subtype'], 'ABSTAIN')
        client.chat.completions.create.assert_called_once()

    def test_subtype_abstain_keeps_positive_parent(self):
        c = {'type': 'Disguised Ad', 'subtype': 'ABSTAIN', 'confidence': .95,
             'evidence_turn_ids': [0, 1], 'reason': '父类型明确，子类型不确定。'}
        first = joint.classify_joint(TURNS, [], [], fake_client(result(c)))
        self.assertEqual(first['primary_type_prediction']['type'], 'Disguised Ad')
        self.assertEqual(joint.subtype_from_joint(first)['subtype'], 'ABSTAIN')

    def test_invalid_json_is_failure_not_abstain(self):
        client = fake_client(result())
        client.chat.completions.create.return_value.choices[0].message.content = '{bad'
        with self.assertRaises(json.JSONDecodeError): joint.classify_joint(TURNS, [], [], client)

    def test_new_profile_uses_joint_model_and_cached_child(self):
        first = {'primary_type_prediction': {'type': 'Disguised Ad'},
                 'joint_subtype_predictions': {'Disguised Ad': {'subtype': 'Product embedding / Native advertising'}}}
        with patch.object(types, 'PROFILE', 'model_priority_v2'), \
             patch.object(joint, 'classify_joint', return_value=first) as classify:
            self.assertIs(types.classify_interface_interference_type(TURNS), first)
        classify.assert_called_once()
        with patch.object(subtypes, 'PROFILE', 'model_priority_v2'), \
             patch.object(subtypes, '_classify_interface_interference_subtype_legacy') as old:
            self.assertEqual(subtypes.classify_interface_interference_subtype(TURNS, first)['subtype'], 'Product embedding / Native advertising')
        old.assert_not_called()

if __name__ == '__main__': unittest.main(verbosity=2)
