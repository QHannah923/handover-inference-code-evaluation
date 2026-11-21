"""验证用户指定的严格门槛，不调用模型、不计算样本成功率。"""
import os, sys, unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dark-pattern'))
os.environ.setdefault('OPENAI_API_KEY', 'test-no-network')
from repetition_policy import exact_repetition_windows, apply_repetition_gate, REPEATED_TYPE
import interface_interference_prompt_v2 as joint
from test_prompt_v2 import result, fake_client


def dialogue(commands, replies):
    turns = []
    for command, reply in zip(commands, replies):
        turns.extend([{'idx':len(turns),'role':'USER','text':command},
                      {'idx':len(turns)+1,'role':'SKILL','text':reply}])
    return turns


def vote(label=REPEATED_TYPE):
    return {'type':label, 'subtype':'Error echo' if label==REPEATED_TYPE else 'Product embedding',
            'confidence':.99,'evidence_turn_ids':[0,1,2,3,4,5],'reason':'synthetic fixture'}


class StrictRepetitionTests(unittest.TestCase):
    def test_three_equal_replies_distinct_commands_qualify(self):
        turns=dialogue(['help','show choices','continue'],['No result.']*3)
        self.assertEqual(exact_repetition_windows(turns),[{'user_turn_ids':[0,2,4],'skill_turn_ids':[1,3,5]}])

    def test_two_replies_do_not_qualify(self):
        self.assertEqual(exact_repetition_windows(dialogue(['a','b'],['x','x'])),[])

    def test_near_match_and_punctuation_do_not_qualify(self):
        for replies in (['Error.','Error!','Error.'],['Error.','error.','Error.'],['No result.','No  result.','No result.']):
            with self.subTest(replies=replies):
                self.assertEqual(exact_repetition_windows(dialogue(['a','b','c'],replies)),[])

    def test_repeated_commands_excluded(self):
        for commands in (['help','help','continue'],[' Help! ','help','continue'],['next item','NEXT   ITEM.','continue']):
            with self.subTest(commands=commands):
                self.assertEqual(exact_repetition_windows(dialogue(commands,['x']*3)),[])

    def test_other_reply_between_matches_breaks_consecutiveness(self):
        self.assertEqual(exact_repetition_windows(dialogue(['a','b','c','d'],['x','different','x','x'])),[])

    def test_later_qualifying_window_is_found(self):
        self.assertEqual(exact_repetition_windows(dialogue(['a','b','c','d'],['different','x','x','x']))[0]['skill_turn_ids'],[3,5,7])

    def test_missing_user_and_other_turns_break_windows(self):
        turns=dialogue(['a','b','c'],['x']*3)
        turns[2]['role']='OTHER'
        self.assertEqual(exact_repetition_windows(turns),[])
        turns=dialogue(['a','b','c'],['x']*3)
        turns[2]['role']='SKILL'
        self.assertEqual(exact_repetition_windows(turns),[])

    def test_ambiguous_multiple_users_and_empty_replies_do_not_qualify(self):
        turns=dialogue(['a','b','c'],['x']*3)
        turns.insert(3,{'idx':99,'role':'USER','text':'extra'})
        self.assertEqual(exact_repetition_windows(turns),[])
        self.assertEqual(exact_repetition_windows(dialogue(['a','b','c'],['','', ''])),[])

    def test_model_cannot_bypass_gate_and_other_votes_preserved(self):
        turns=dialogue(['a','b','c'],['x','different','x'])
        raw=result(vote()); raw['candidates'].append(vote('Disguised Ad'))
        kept,rules,audit=apply_repetition_gate(raw,[{'type':REPEATED_TYPE,'confidence':.93}],turns)
        self.assertEqual([c['type'] for c in kept],['Disguised Ad'])
        self.assertEqual(rules,[])
        self.assertFalse(audit['eligible'])
        self.assertEqual(len(raw['candidates']),2)

    def test_candidate_must_cite_qualifying_replies(self):
        turns=dialogue(['a','b','c'],['x']*3)
        candidate=vote();candidate['evidence_turn_ids']=[0,1]
        self.assertEqual(apply_repetition_gate(result(candidate),[],turns)[0],[])

    def test_joint_classifier_enforces_gate_instead_of_only_prompt(self):
        turns=dialogue(['a','b','c'],['x','different','x'])
        first=joint.classify_joint(turns,[],[],fake_client(result(vote())))
        self.assertEqual(first['primary_type_prediction']['type'],'ABSTAIN')
        self.assertTrue(first['decision_audit']['repetition_gate']['excluded_candidates'])
        self.assertEqual(first['decision_audit']['joint_model_result']['candidates'][0]['type'],REPEATED_TYPE)

    def test_gate_does_not_force_positive_when_model_says_normal(self):
        turns=dialogue(['a','b','c'],['x']*3)
        first=joint.classify_joint(turns,[],[],fake_client(result()))
        self.assertEqual(first['primary_type_prediction']['type'],'ABSTAIN')

    def test_qualifying_model_vote_keeps_original_weights(self):
        turns=dialogue(['a','b','c'],['x']*3)
        first=joint.classify_joint(turns,[],[],fake_client(result(vote())))
        self.assertEqual(first['primary_type_prediction']['type'],REPEATED_TYPE)
        self.assertEqual(first['primary_type_prediction']['ranking_score'],.978)
        self.assertEqual(joint.subtype_from_joint(first)['subtype'],'Error echo')

if __name__=='__main__': unittest.main(verbosity=2)
