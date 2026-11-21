import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'dark-pattern'))
from verified_failure_rules import noncommercial_notice_exclusion,apply_verified_fallback,unsolicited_sales_certificates

def turns(*text):return [{'idx':i,'role':'USER' if i%2==0 else 'SKILL','text':t} for i,t in enumerate(text)]
notice='You currently do not have our tracking product. If you wish to hear more about it say, tell me about tracking. '
answer='Your selected setting has been saved and the requested measurement is available in the current session. Everything required for this task has completed. You can say next or stop. What can I help you with.'
progress='The next requested task has completed successfully and the new measurement is now available. The previous setting remains active and you can continue with another measurement or stop.'
class Boundaries(unittest.TestCase):
    def test_notice_with_real_progress(self):
        self.assertEqual(noncommercial_notice_exclusion(turns('measure',notice+answer,'next',progress))['rule_id'],'OPTIONAL_NONPURCHASE_NOTICE_WITH_TASK_COMPLETION')
    def test_notice_without_answer_or_later_progress(self):
        for ts in [turns('measure',notice+'What next?','next',progress),turns('measure',notice+answer)]:self.assertIsNone(noncommercial_notice_exclusion(ts))
    def test_other_commercial_evidence_vetoes_notice(self):
        for offer in ['Buy our book now.','Visit our website dot com.','You must subscribe to continue.','This costs five dollars.']:
            self.assertIsNone(noncommercial_notice_exclusion(turns('measure',notice+answer,'next',progress+offer)))
    def test_task_continuation_does_not_erase_external_ad(self):
        self.assertIsNone(noncommercial_notice_exclusion(turns('measure','Buy our latest book. '+answer,'next',progress)))
    def test_short_terminal_social_goodbye(self):
        self.assertEqual(noncommercial_notice_exclusion(turns('open ideas','Ask for help.','stop','Thanks for using this skill. Check us out on instagram at Our Journal. Goodbye.'))['rule_id'],'TERMINAL_SOCIAL_SIGNOFF_ONLY')
    def test_social_vetoes_offer_prior_ad_and_nonterminal(self):
        bye='Thanks. Check us out on instagram at Our Journal. Goodbye.'
        cases=[turns('open','Buy our book.','stop',bye),turns('stop',bye+' Buy a pass.'),turns('next',bye),turns('stop',bye,'next','More ideas.'),turns('stop','Thanks. Check us out on instagram at Our Discount Shop. Bye.')]
        for ts in cases:self.assertIsNone(noncommercial_notice_exclusion(ts))
    def test_preserve_other_parent_and_disabled_rule(self):
        ts=turns('stop','Thanks. Check us out on instagram at Our Journal. Goodbye.')
        for parent in ['Voice-Guided Rating','Repeated/Confused Output','Watch Ads/Pay to Avoid Ads']:
            source={'primary_type_prediction':{'type':parent},'joint_subtype_predictions':{}}
            self.assertEqual(apply_verified_fallback(source,ts)['primary_type_prediction']['type'],parent)
        source={'primary_type_prediction':{'type':'Disguised Ad'},'joint_subtype_predictions':{}}
        self.assertEqual(apply_verified_fallback(source,ts,enabled=False)['primary_type_prediction']['type'],'Disguised Ad')

    def test_named_product_opening_not_generic_menu(self):
        self.assertTrue(unsolicited_sales_certificates(turns('open travel guide','Welcome. You can buy City Explorer or buy Country Explorer.')))
        for request,response in [('open guide',"To hear about purchase options say what can I buy."),('buy City Explorer','You can buy City Explorer.'),('open guide','You can buy products.')]:
            self.assertEqual(unsolicited_sales_certificates(turns(request,response)),[])

    def test_three_distinct_answers_with_same_unsolicited_upsell(self):
        reply='Here is the detailed response to the question you asked today. If you want to know more about this topic, you can buy GUIDE PREMIUM.'
        ts=turns('topic one',reply,'topic two',reply,'topic three',reply)
        self.assertTrue(any(p['rule_id']=='REPEATED_UNREQUESTED_SAME_PRODUCT_UPSELL' for p in unsolicited_sales_certificates(ts)))
        self.assertEqual(unsolicited_sales_certificates(ts[:4]),[])
        self.assertEqual(unsolicited_sales_certificates(turns('repeat',reply,'repeat',reply,'repeat',reply)),[])

    def test_requested_upgrade_and_different_products_do_not_form_run(self):
        reply='Here is the detailed response to the question you asked today. If you want to know more about this topic, you can buy GUIDE PREMIUM.'
        self.assertEqual(unsolicited_sales_certificates(turns('topic one',reply,'about premium',reply,'topic three',reply)),[])
        self.assertEqual(unsolicited_sales_certificates(turns('topic one',reply,'topic two',reply.replace('GUIDE PREMIUM','MAP PREMIUM'),'topic three',reply)),[])

    def test_conditional_purchase_instruction_keeps_proven_scoring_fault(self):
        ts=turns('open quiz','If at any time you want to buy the expert package, say, Buy Expert. Let us start. Drill or Quiz.',
                 'Paris','Wrong. The correct answer is Paris.','eight','Incorrect. Correct answer is 8.')
        self.assertEqual(unsolicited_sales_certificates(ts),[])
        source={'primary_type_prediction':{'type':'ABSTAIN'},'joint_subtype_predictions':{}}
        self.assertEqual(apply_verified_fallback(source,ts)['primary_type_prediction']['type'],'Repeated/Confused Output')

if __name__=='__main__':unittest.main(verbosity=2)
