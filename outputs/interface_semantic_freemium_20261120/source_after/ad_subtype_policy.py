"""User-defined ad boundaries; synthetic contrasts, no sample IDs or answer table."""
MERGED_AD_SUBTYPE = 'Product embedding / Native advertising'
POLICY_VERSION = 'causal_recommendation_and_free_extensions_20261120'

AD_SUBTYPE_POLICY = '''AD SIBLING POLICY, after establishing an ad rather than an excluded internal upgrade:
Product embedding / Native advertising: external promotional content inserted into a non-choice
task, or a promotion passed off as ordinary informational content. This is a merged child.
Biased recommendation: selection favoring a target against user preferences, OR an explicit
directional cross-skill push that uses prior use of the current skill as the reason the user should
use a particular other skill/app. Under this project definition the latter does not require a
comparison list, a user-requested recommendation function or proof of undisclosed commission.
Identify the promoted target, the urged action and the behavioral link. Strong tone alone is not
enough. 'You might like our book' inside an unrelated sales insertion remains the merged child;
it is not the same mechanism as 'because you used this, you should use that'.
Include ad_mechanism:{"user_goal_turn_ids":[0],"promotion_turn_ids":[1],
"mechanism":"task_insertion OR organic_ad_content OR biased_choice",
"bias_evidence_turn_ids":[],"reason_excluding_other_child":"brief Chinese explanation"}.
Choose one actual mechanism, not the OR string. Biased recommendation needs biased_choice
and nonempty bias evidence, including a causal push if relevant. Cite all referenced IDs in
evidence_turn_ids. User consent to later details does not authorize an earlier unsolicited pitch.
'''

AD_CONTRASTIVE_EXAMPLES = '''SYNTHETIC CONTRASTS; apply mechanisms, not names:
A. USER Play wind audio. SKILL By the way, learn how to buy our new guide.
Ad -> Product embedding / Native advertising: an external product inserted into audio use.
B. USER Open a puzzle skill. SKILL Because you used this skill, you should also use City Puzzles.
Ad -> Biased recommendation: prior use is made the reason to steer to a particular other skill.
C. SKILL You finished your three free rounds. An optional pack adds more rounds. Want details?
No dark pattern from this extension alone; evaluate actual independent errors separately.
D. USER What is the price of the pack? SKILL It costs ten dollars; you can continue free without it.
No disguised ad from these turns: a requested internal product explanation.
E. USER Pause. SKILL Choose a scent. USER Mint. SKILL Add that scent to your shopping cart.
Ad insertion began before the product choice; later engagement does not erase the redirection.
F. USER Help. SKILL You can buy advanced routines; ask what can I buy. USER What can I buy?
SKILL Nothing is available to purchase; let's do another task. This is an error-guidance pattern,
not an ad merely because the content was paid. A genuinely empty generic catalog alone differs.
'''
