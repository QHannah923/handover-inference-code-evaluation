import os, sys, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import json

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'dark-pattern'))
os.environ.setdefault('OPENAI_API_KEY','test-no-network')
import repeated_output_only as target

def client(value):
    create=Mock(return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(value)))]))
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

def turns(reply='x'):
    return [{'idx':0,'role':'USER','text':'help'},{'idx':1,'role':'SKILL','text':'x'},
            {'idx':2,'role':'USER','text':'choices'},{'idx':3,'role':'SKILL','text':reply},
            {'idx':4,'role':'USER','text':'continue'},{'idx':5,'role':'SKILL','text':'x'}]

def positive():
    return {'type':target.REPEATED_TYPE,'subtype':'Error echo','confidence':.99,
            'evidence_turn_ids':[0,1,2,3,4,5],'reason':'synthetic fixture'}

class FocusedTests(unittest.TestCase):
    def test_positive_uses_existing_strict_gate(self):
        r=target.classify_repeated_only(turns(),client(positive()))
        self.assertTrue(r['target_type_prediction']['present'])
        self.assertEqual(r['target_type_prediction']['ranking_score'],.978)

    def test_near_repetition_cannot_be_positive(self):
        r=target.classify_repeated_only(turns('X'),client(positive()))
        self.assertFalse(r['target_type_prediction']['present'])
        self.assertEqual(r['target_type_prediction']['method'],'strict_gate')

    def test_negative_is_not_whole_dialogue_abstain(self):
        value={'type':target.NOT_TARGET,'subtype':'ABSTAIN','confidence':.99,'evidence_turn_ids':[], 'reason':'仅该分类阴性。'}
        r=target.classify_repeated_only(turns(),client(value))
        self.assertEqual(r['target_type_prediction']['type'],target.NOT_TARGET)
        self.assertFalse(r['decision_audit']['other_categories_reclassified'])

    def test_invalid_contract_raises(self):
        with self.assertRaises(ValueError):target.classify_repeated_only(turns(),client({'type':'Other'}))

if __name__=='__main__':unittest.main(verbosity=2)
