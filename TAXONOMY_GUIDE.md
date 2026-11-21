# Taxonomy and Annotation Guide

> **This week's use:** reference only. The student is verifying the existing Interface Interference inference code on 87 logs against human ground truth. Do not revise the taxonomy or perform new annotation this week. The remaining taxonomy branches are project context for later work.

## 1. Purpose and status

This document consolidates the current shared understanding of the full VUI dark-pattern taxonomy so that it does not have to be reconstructed from code, spreadsheets, paper fragments, and historical notes.

The taxonomy has already undergone one annotation/verification round. The current structure is therefore a **working verified taxonomy**, not an unreviewed first draft. This guide does not restart taxonomy construction. Future changes should be driven by recovered annotation evidence, targeted disagreement analysis, observability limitations, or formal evaluation results.

Taxonomy scope and implementation completion are separate. The full 3/12/37 taxonomy is the agreed research scope, but the only versioned classifier implementation is the Interface Interference branch in Git commit `d93962c`. The later full-taxonomy classifier is an untracked candidate whose provenance and validation status are **`待核实`**. Taxonomy coverage must not be inferred merely because that candidate file exists.

Current scope:

- 3 categories;
- 12 types;
- 37 subtypes.

> **Scope is frozen; taxonomy definitions are not.**

For this week's comparison, `INTERFACE INTERFERENCE` and the storage spelling `INTERFACE_INTERFERENCE` refer to the same category. The evaluated implementation covers only the Interface Interference branch, not all 3/12/37 paths.

## 2. Annotation unit

The main annotation unit is one dialogue/session log. An annotation consists of:

1. one complete taxonomy path, represented as `category > type > subtype`;
2. the minimal dialogue-turn IDs needed to support that path;
3. an optional contextual span around those turns;
4. an evidence-based note explaining the observed behaviour;
5. an uncertainty or insufficient-evidence note where appropriate.

A dialogue may receive zero, one, or multiple taxonomy paths.

Do not infer a label only from a Skill name or from assumed developer intent. The annotation must be supported by observable dialogue behaviour, platform output, or a state transition represented in the available trace.

## 3. Multi-label policy

The conceptual gold label is a set:

```text
gold(dialogue) = {
  category_1 > type_1 > subtype_1,
  category_2 > type_2 > subtype_2,
  ...
}
```

System output should be evaluated in the same form:

```text
prediction(dialogue) = {taxonomy path, taxonomy path, ...}
```

No gold label must be declared primary. A `primary_prediction` field may remain in system output for presentation, ranking, or debugging, but it is not the central research target unless a theoretically justified primary-label policy is introduced later.

Multi-label annotation rules:

- Add more than one path only when each path has independent observable evidence.
- Do not add parent paths separately when a subtype path is already present; the parent category and type are implied by the full path.
- Do not use multiple labels merely to express annotator uncertainty. Record uncertainty separately.
- Closely related subtypes under one type may co-occur only if the dialogue contains distinct evidence for both behaviours.
- Platform behaviour and third-party Skill behaviour must be attributed separately when the trace allows the distinction.

## 4. Existing verification round (background for later work)

The project owner confirms that the taxonomy has already undergone one annotation/verification round and that the current taxonomy reflects that work. This history is background for later work; this week's task is to use the available human ground truth for the 87-log inference verification, not to reconstruct or extend the annotation round.

Artifacts that may contain evidence from that round include:

- `dark-pattern/Taxonomy.numbers`;
- `dark-pattern/benchmark_gt_100.csv`;
- `dark-pattern/benchmark_gt_100_round2.csv`;
- `dark-pattern/interface_interference_examples/interface_bench.csv`;
- `dark-pattern/progress control/claude-progress.txt`;
- `dark-pattern/progress control/function-checklist.json`.

These artifacts do not currently prove that every taxonomy branch has an implemented and validated detector. In particular, the two 100-log benchmark files and the later full-taxonomy classifier are untracked working-tree artifacts. Their relationship to the earlier verification round is **`待核实`**.

Before the paper describes the annotation process, consolidate the following known historical facts from the people involved and the existing workbook:

- sample or dataset used in the verification round;
- annotators and their roles;
- whether annotation was independent before discussion;
- agreement or validation evidence, if calculated;
- adjudication process;
- taxonomy definitions changed after the round;
- examples retained as canonical boundary cases.

Do not automatically launch a new generic 50–100 log pilot. Additional annotation should be targeted only at unresolved boundaries, missing categories, or provenance gaps identified during consolidation.

## 5. Current taxonomy tree (reference only this week)

```text
OBSTRUCTION
├── Unexpected Exit
│   ├── Abrupt End
│   └── No Farewell Phrase (Silent Termination)
├── Unstoppable App
│   ├── Fake exit (looping behaviour)
│   └── Ignores Stop
├── Unstartable App
│   ├── Skill Access Failure
│   ├── Conflicting names
│   ├── Invocation not recognized
│   └── Unsupported devices
└── Unexpected App Started
    ├── Skill squatting
    ├── Misinterpreted intent
    └── Ambiguous naming

SNEAKING
├── Forced Continuity
│   ├── Cross-platform cancellation (Multi-Interface Lock-in)
│   └── Auto-renewal
├── Hidden Information
│   ├── Obfuscated Disclosure
│   ├── Redirect to website
│   ├── Distributed Disclosure (Sequential Lock-in)
│   ├── Emotion framing
│   └── Bait and Switch
├── Privacy Violation
│   ├── Requests name/email/address
│   ├── Hidden listening
│   └── No data justification
└── Preselection
    ├── Auto-enrollment
    ├── Implicit opt-in
    └── Default notification setting

INTERFACE INTERFERENCE
├── Watch Ads/Pay to Avoid Ads
│   ├── Feature lock (Subscription interruption)
│   ├── Paywall bypass
│   ├── Alexa native ads
│   └── Mandatory ads
├── Disguised Ad
│   ├── Biased recommendation
│   ├── Product embedding
│   └── Native advertising
├── Voice-Guided Rating
│   ├── Rate us 5 stars
│   ├── Voice review request
│   └── Sentiment framing
└── Repeated/Confused Output
    ├── Error echo
    ├── Misleading loop (skills bug) (Repeated prompts)
    └── Feedforward Ambiguity (No help guidance / Unspoken options / Feedforward Ambiguity)
```

## 6. Taxonomy cards

Examples below are illustrative unless a corpus filename is explicitly given. They are intended to clarify decisions, not to replace the existing annotation record.

## 6.1 OBSTRUCTION

Obstruction covers observable behaviours that interrupt, block, resist, or distort the user's ability to begin, continue, complete, or exit the intended interaction.

### Unexpected Exit > Abrupt End

- **Definition:** The interaction terminates abruptly before the user's task is fulfilled and without a normal transition to a completed or closed state.
- **Positive conditions:** A substantive user request is followed by no Skill response, or an active task ends unexpectedly without task completion.
- **Negative conditions:** The user has already completed the task; the final utterance is only thanks/acknowledgement; the trace is known to be truncated by the data collector.
- **Confusable with:** No Farewell Phrase; Skill Access Failure; ordinary missing or incomplete logs.
- **Required evidence:** An unfinished user goal plus an observable end of trace or termination event.
- **Illustrative example:** The user asks the next task question and the session ends immediately.
- **Remaining uncertainty:** Dialogue logs alone may not distinguish intentional termination, platform timeout, crawler failure, and logging truncation.

### Unexpected Exit > No Farewell Phrase (Silent Termination)

- **Definition:** The session ends without conversational closure or an appropriate farewell.
- **Positive conditions:** A stop/exit or session-ending transition receives silence, audio-only output, or an otherwise non-closing response.
- **Negative conditions:** A clear goodbye, task-completion message, or normal short acknowledgement closes the session.
- **Confusable with:** Abrupt End; Ignores Stop.
- **Required evidence:** Evidence that the session ended, together with absence of a closing response.
- **Illustrative example:** The user says “stop” and no closing message is returned.
- **Remaining uncertainty:** Absence of a logged final response may reflect collection failure.

### Unstoppable App > Fake exit (looping behaviour)

- **Definition:** The Skill appears to exit or says goodbye but continues the interaction or later emits additional Skill output.
- **Positive conditions:** Farewell language is followed by a prompt, task continuation, solicitation, or later Skill turn.
- **Negative conditions:** A goodbye is followed only by a platform-level message after control has clearly returned to Alexa.
- **Confusable with:** Ignores Stop; Alexa native ads; Voice review request.
- **Required evidence:** The apparent exit and the subsequent continued Skill behaviour.
- **Illustrative example:** “Goodbye” is immediately followed by “Would you like another question?”
- **Remaining uncertainty:** Platform messages after Skill exit require attribution.

### Unstoppable App > Ignores Stop

- **Definition:** An explicit stop, exit, cancel, or quit command is not honoured.
- **Positive conditions:** The Skill continues its task, asks another question, plays content, or uses the turn for another solicitation after an explicit exit command.
- **Negative conditions:** The Skill gives a normal closing response; the utterance containing “stop” is not functioning as an exit command in context.
- **Confusable with:** Fake exit; No Farewell Phrase; Voice review request after exit.
- **Required evidence:** Explicit user termination intent and the Skill's non-compliant response.
- **Illustrative example:** USER: “cancel”; SKILL: continues the quiz.
- **Remaining uncertainty:** Whether a farewell plus review request counts as failure to exit should follow the agreed annotation precedent.

### Unstartable App > Skill Access Failure

- **Definition:** The requested Skill cannot be opened or resumed and the intended application never becomes usable.
- **Positive conditions:** Alexa reports unavailable Skill, account-link failure, launch problem, or required setup that prevents entry.
- **Negative conditions:** The Skill starts after a recoverable message; the message merely informs the user of an optional account feature.
- **Confusable with:** Invocation not recognized; Unsupported devices; ordinary platform failure.
- **Required evidence:** A launch/access request and an explicit failure preventing use.
- **Illustrative example:** “The requested skill is no longer available.”
- **Remaining uncertainty:** This may be a usability/platform failure rather than a manipulative dark pattern; paper framing must justify inclusion.

### Unstartable App > Conflicting names

- **Definition:** A requested Skill name is sufficiently close to another Skill or invocation name that the intended Skill cannot be reliably started.
- **Positive conditions:** Similar names create repeated launch conflict, confusion, or redirection.
- **Negative conditions:** Alexa asks a normal clarification among clearly distinct targets; the user used the wrong name.
- **Confusable with:** Skill squatting; Ambiguous naming; Misinterpreted intent.
- **Required evidence:** Requested and returned/clarified Skill names plus evidence of name conflict.
- **Illustrative example:** The requested Skill and opened Skill differ only by a small name variation.
- **Remaining uncertainty:** Deliberate imitation cannot usually be inferred from one dialogue.

### Unstartable App > Invocation not recognized

- **Definition:** A plausible invocation or command for the intended Skill is rejected as unknown, preventing the user from starting or resuming the task.
- **Positive conditions:** The assistant explicitly says it does not know, understand, or find the requested invocation.
- **Negative conditions:** The user's utterance is unrelated, malformed, or outside the stated interface; the Skill provides a useful recovery path.
- **Confusable with:** Skill Access Failure; Feedforward Ambiguity; Error echo.
- **Required evidence:** User invocation and recognition-failure response.
- **Illustrative example:** “I couldn't understand what you said” in response to a valid launch phrase.
- **Remaining uncertainty:** Validity of the invocation may require Skill metadata unavailable in the trace.

### Unstartable App > Unsupported devices

- **Definition:** The requested interaction cannot proceed because the device lacks a required capability or the Skill asks for an impossible device action.
- **Positive conditions:** Explicit unsupported-device message or capability requirement blocks the task.
- **Negative conditions:** The Skill offers a functioning alternative on the current device.
- **Confusable with:** Skill Access Failure; Redirect to website.
- **Required evidence:** Device/capability limitation and blocked intended task.
- **Illustrative example:** “This feature is not supported on this device.”
- **Remaining uncertainty:** Inclusion as a dark pattern depends on evidence of deceptive targeting or avoidable friction rather than ordinary incompatibility.

### Unexpected App Started > Skill squatting

- **Definition:** A Skill with a confusingly similar name is launched instead of the expected Skill, consistent with imitation or name squatting.
- **Positive conditions:** Requested and launched names are similar, while functionality or identity clearly differs.
- **Negative conditions:** The names are unrelated and Alexa simply misheard the request; the user selected among legitimate alternatives.
- **Confusable with:** Conflicting names; Misinterpreted intent; Ambiguous naming.
- **Required evidence:** Requested name, launched identity, similarity, and mismatch in expected function.
- **Illustrative example:** A near-copy name launches a different third-party Skill.
- **Remaining uncertainty:** Deliberate squatting generally requires marketplace metadata beyond the dialogue.

### Unexpected App Started > Misinterpreted intent

- **Definition:** The system maps a user's request to a different Skill or action than the intended target.
- **Positive conditions:** The requested target and opened target differ in a way not explained by legitimate clarification.
- **Negative conditions:** The user accepts or explicitly chooses the alternative; the intended Skill starts successfully.
- **Confusable with:** Skill squatting; Ambiguous naming; normal ASR error.
- **Required evidence:** User request and evidence identifying the different action or Skill that started.
- **Illustrative example:** The user requests a weather Skill and a different content Skill opens.
- **Remaining uncertainty:** A single misrecognition may be a platform error rather than a dark pattern.

### Unexpected App Started > Ambiguous naming

- **Definition:** A vague or non-distinctive Skill name makes it unclear which application will be launched or what it does.
- **Positive conditions:** Multiple plausible Skills or targets share the invocation and the user cannot identify the intended one.
- **Negative conditions:** Alexa provides an effective clarification step; ambiguity arises solely from an incomplete user utterance.
- **Confusable with:** Conflicting names; Skill squatting; Misinterpreted intent.
- **Required evidence:** Ambiguity or multiple targets plus resulting user confusion or wrong launch.
- **Illustrative example:** Alexa reports that several Skills match the same generic name.
- **Remaining uncertainty:** Marketplace metadata may be required to judge whether the name itself is misleading.

## 6.2 SNEAKING

Sneaking covers behaviours that hide, delay, downplay, or disguise material information, commercial conditions, privacy implications, or consent choices.

### Forced Continuity > Cross-platform cancellation (Multi-Interface Lock-in)

- **Definition:** Cancellation or subscription management requires the user to move to another interface, account, website, or device.
- **Positive conditions:** The voice interface can enrol or continue the service but directs cancellation elsewhere in a way that increases exit effort.
- **Negative conditions:** The external interface is required by a disclosed technical limitation and cancellation remains straightforward; the website redirect is unrelated to cancellation.
- **Confusable with:** Redirect to website; Auto-renewal.
- **Required evidence:** Existing continuity/subscription plus explicit cross-platform cancellation requirement.
- **Illustrative example:** “To cancel, sign in to the website and open account settings.”
- **Remaining uncertainty:** A dialogue may reveal the external step without showing how burdensome the full cancellation process is.

### Forced Continuity > Auto-renewal

- **Definition:** A subscription, trial, or paid service renews or starts billing automatically unless the user acts to stop it.
- **Positive conditions:** Explicit automatic renewal, recurring charge, or trial-to-paid transition without a new affirmative action.
- **Negative conditions:** A one-time purchase; renewal occurs only after an explicit confirmation; renewal terms are clearly stated and actively selected.
- **Confusable with:** Auto-enrollment; Implicit opt-in; Distributed Disclosure.
- **Required evidence:** Renewal/recurring charge and default continuation condition.
- **Illustrative example:** “After seven days, your subscription automatically renews monthly.”
- **Remaining uncertainty:** Logs may mention renewal terms without showing whether the user previously consented.

### Hidden Information > Obfuscated Disclosure

- **Definition:** Material information is technically disclosed but made difficult to understand through verbosity, opacity, vague wording, speed, or information overload.
- **Positive conditions:** Important fees, terms, limits, or consequences are buried or expressed so unclearly that meaningful understanding is impaired.
- **Negative conditions:** A concise and understandable disclosure; ordinary detailed information that is relevant to the task.
- **Confusable with:** Distributed Disclosure; Redirect to website; Bait and Switch.
- **Required evidence:** The material condition and the obfuscating presentation within the trace.
- **Illustrative example:** A long rapid block of terms hides a recurring fee.
- **Remaining uncertainty:** Text transcripts may lose speech speed, emphasis, and audio presentation features.

### Hidden Information > Redirect to website

- **Definition:** The Skill avoids completing the task or disclosing relevant information directly and instead instructs the user to visit a website or app.
- **Positive conditions:** Information necessary to complete or understand the current task is withheld behind another interface.
- **Negative conditions:** The website is an optional source for additional information after the voice task is completed; redirection is necessary and clearly explained.
- **Confusable with:** Cross-platform cancellation; Product embedding; Unsupported devices.
- **Required evidence:** User's current goal, missing in-voice completion/information, and the external redirect.
- **Illustrative example:** “Visit our website for the price and terms” instead of answering the pricing question.
- **Remaining uncertainty:** Not every cross-channel handoff is manipulative; task relevance and avoidability matter.

### Hidden Information > Distributed Disclosure (Sequential Lock-in)

- **Definition:** Material terms are revealed across multiple interaction steps, especially after the user has invested effort or progressed toward commitment.
- **Positive conditions:** Pricing, limitations, renewal, or requirements appear only after earlier apparently low-cost/free steps.
- **Negative conditions:** Information is divided for normal conversational clarity but all material conditions are disclosed before commitment.
- **Confusable with:** Obfuscated Disclosure; Bait and Switch; Paywall bypass.
- **Required evidence:** Sequence showing delayed disclosure and the earlier user commitment or engagement.
- **Illustrative example:** A trial is offered first; recurring cost is revealed only at final confirmation.
- **Remaining uncertainty:** A complete trace is needed to judge disclosure timing.

### Hidden Information > Emotion framing

- **Definition:** Emotional pressure, guilt, fear, urgency, or sympathy is used to influence a material decision or disclosure.
- **Positive conditions:** The emotional framing is connected to purchase, consent, continued use, data sharing, or another consequential action.
- **Negative conditions:** Harmless positive tone; encouragement unrelated to a material choice; rating-specific positivity better labelled Sentiment framing.
- **Confusable with:** Sentiment framing; Bait and Switch.
- **Required evidence:** Emotional language and the action it is intended to influence.
- **Illustrative example:** “Don't let us down—subscribe now to support us.”
- **Remaining uncertainty:** The boundary with ordinary persuasive language needs consistent annotation precedent.

### Hidden Information > Bait and Switch

- **Definition:** The Skill attracts the user with one expected task, offer, or meaning and then replaces it with a materially different action, condition, or outcome.
- **Positive conditions:** Observable mismatch between the initial representation and later requirement or delivered result.
- **Negative conditions:** A clearly disclosed prerequisite; a normal task branch chosen by the user; Paywall bypass where the central issue is payment after engagement.
- **Confusable with:** Paywall bypass; Distributed Disclosure; Misinterpreted intent.
- **Required evidence:** Both the bait and the subsequent switch.
- **Illustrative example:** A “free” function redirects to sign-up or purchase before providing any result.
- **Remaining uncertainty:** The initial representation may be outside the captured dialogue.

### Privacy Violation > Requests name/email/address

- **Definition:** The Skill requests personal information such as name, email, address, phone, location, or birth information without an evident task need or proportionate context.
- **Positive conditions:** Direct request for identifiable or sensitive information in a context where the need is unclear.
- **Negative conditions:** Data is necessary for the requested service and the purpose is clearly explained before collection.
- **Confusable with:** No data justification; Auto-enrollment.
- **Required evidence:** The personal-data request and enough context to assess necessity or disclosure.
- **Illustrative example:** A trivia Skill unexpectedly asks for the user's email address.
- **Remaining uncertainty:** Request and lack of justification may justify two paths only when each policy definition is independently met.

### Privacy Violation > Hidden listening

- **Definition:** The system continues listening or recording after a reasonable user would believe listening has stopped.
- **Positive conditions:** Explicit evidence that recording/listening persists after exit, timeout, or apparent deactivation.
- **Negative conditions:** A normal open microphone window clearly indicated by the platform; ordinary follow-up listening within an active dialogue.
- **Confusable with:** Fake exit; No Farewell Phrase.
- **Required evidence:** Apparent end of expected listening plus evidence of continued capture.
- **Illustrative example:** The Skill says it has stopped but later reacts to background speech without being reactivated.
- **Remaining uncertainty:** Usually difficult or impossible to establish from text-only logs; platform instrumentation may be required.

### Privacy Violation > No data justification

- **Definition:** The Skill collects or requests personal data without explaining why it is needed or how it will be used.
- **Positive conditions:** A data request is observable and no purpose is provided in the relevant local context.
- **Negative conditions:** A specific, understandable purpose is disclosed before collection; the information is not personal data.
- **Confusable with:** Requests name/email/address; Obfuscated Disclosure.
- **Required evidence:** Data request plus absence of an adequate purpose explanation in the relevant span.
- **Illustrative example:** “Tell me your address” with no explanation in the surrounding dialogue.
- **Remaining uncertainty:** Justification may have occurred in an earlier consent flow outside the log.

### Preselection > Auto-enrollment

- **Definition:** The user is enrolled in a trial, subscription, service, or feature without an explicit affirmative choice.
- **Positive conditions:** The Skill announces that enrolment or a trial has already started despite no recorded opt-in.
- **Negative conditions:** The user explicitly confirmed enrolment; the Skill is merely offering enrolment.
- **Confusable with:** Implicit opt-in; Auto-renewal.
- **Required evidence:** State change into enrolment and absence of explicit consent in the available interaction.
- **Illustrative example:** “Your free trial starts now” after an unrelated command.
- **Remaining uncertainty:** Prior consent outside the current log may be missing.

### Preselection > Implicit opt-in

- **Definition:** Consent is assumed from continuation, silence, use, or an ambiguous action rather than obtained through an explicit affirmative choice.
- **Positive conditions:** “By continuing you agree” or equivalent default-consent logic governs a material choice.
- **Negative conditions:** Explicit yes/no confirmation; a non-material conversational default.
- **Confusable with:** Auto-enrollment; Auto-renewal; Default notification setting.
- **Required evidence:** The passive/ambiguous action and the consent consequence assigned to it.
- **Illustrative example:** Continuing to the next question is treated as acceptance of data use.
- **Remaining uncertainty:** The definition should specify which actions are material enough to count.

### Preselection > Default notification setting

- **Definition:** Notifications or reminders are enabled by default without an explicit user choice.
- **Positive conditions:** The Skill announces enabled notifications or future reminders without a recorded opt-in.
- **Negative conditions:** The user explicitly requested reminders; the Skill only offers the option.
- **Confusable with:** Implicit opt-in; Auto-enrollment.
- **Required evidence:** Notification state enabled plus absence of explicit consent in the trace.
- **Illustrative example:** “I’ll send you daily reminders” after ordinary use of the Skill.
- **Remaining uncertainty:** Prior account-level settings may be outside the dialogue.

## 6.3 INTERFACE INTERFERENCE

Interface Interference covers voice-interface wording, defaults, sequencing, and dialogue structure that steer user choices or disrupt control without necessarily blocking the underlying functionality outright.

### Watch Ads/Pay to Avoid Ads > Feature lock (Subscription interruption)

- **Definition:** Core or expected functionality is interrupted or withheld behind an upgrade, subscription, or paid package.
- **Positive conditions:** The user attempts a relevant feature and is told to subscribe, upgrade, or buy access.
- **Negative conditions:** A clearly premium optional feature is advertised without interrupting the requested basic task.
- **Confusable with:** Paywall bypass; Mandatory ads; Bait and Switch.
- **Required evidence:** Requested feature, access restriction, and payment/upgrade condition.
- **Illustrative example:** A requested quiz mode is available only after buying the expert package.
- **Remaining uncertainty:** “Core” versus optional functionality may require Skill description or prior representation.

### Watch Ads/Pay to Avoid Ads > Paywall bypass

- **Definition:** Content initially appears available or free but redirects to payment after the user has engaged or invested effort.
- **Positive conditions:** The user begins a flow and encounters a purchase requirement before receiving the expected outcome.
- **Negative conditions:** The paywall is clearly disclosed before engagement; payment is an unrelated optional offer.
- **Confusable with:** Feature lock; Bait and Switch; Distributed Disclosure.
- **Required evidence:** Initial free/available framing, user engagement, and later payment redirection.
- **Illustrative example:** Several setup questions are completed before the Skill says the result requires purchase.
- **Remaining uncertainty:** Earlier marketplace pricing may be outside the dialogue.

### Watch Ads/Pay to Avoid Ads > Alexa native ads

- **Definition:** The host platform injects an unsolicited promotional message, typically after a third-party Skill task or exit, and the promotion is not controlled by that Skill.
- **Positive conditions:** Control has returned to Alexa and a platform-level first-party or partner promotion is delivered without request.
- **Negative conditions:** The third-party Skill itself embeds promotion; the platform message is a requested recommendation.
- **Confusable with:** Native advertising; Mandatory ads; Fake exit.
- **Required evidence:** Platform attribution, transition out of the Skill, and unsolicited promotion.
- **Illustrative example:** After the Skill ends, Alexa promotes an Amazon service.
- **Remaining uncertainty:** Text logs may not reliably identify which component produced the message.

### Watch Ads/Pay to Avoid Ads > Mandatory ads

- **Definition:** The user is forced to receive an advertisement or promotional pitch without an available skip or opt-out in the interaction.
- **Positive conditions:** The ad interrupts or precedes the task and must be heard to continue.
- **Negative conditions:** Clearly optional promotion; disguised commercial content better labelled under Disguised Ad; platform-native promotion after exit.
- **Confusable with:** Product embedding; Native advertising; Alexa native ads.
- **Required evidence:** Recognizable promotion, compulsory exposure, and connection to task progression.
- **Illustrative example:** The Skill plays a sponsor message before every answer with no skip option.
- **Remaining uncertainty:** The absence of a skip may not be visible unless the user attempts to skip.

### Disguised Ad > Biased recommendation

- **Definition:** The Skill recommends a particular product, service, partner, or other Skill while presenting the recommendation as neutral or user-oriented.
- **Positive conditions:** A specific entity is favoured without a clear user-driven relevance reason or disclosure of commercial interest.
- **Negative conditions:** The user explicitly requested that recommendation; several alternatives are neutrally compared; the promotion is the primary content rather than a recommendation.
- **Confusable with:** Product embedding; Native advertising; ordinary recommendation.
- **Required evidence:** Recommendation language, favoured entity, and context showing limited relevance or disclosure.
- **Illustrative example:** After completing a quiz, the Skill recommends enabling a particular related Skill.
- **Remaining uncertainty:** Commercial relationship or bias may require evidence outside the dialogue.

### Disguised Ad > Product embedding

- **Definition:** Commercial content is inserted into an ongoing non-commercial task flow and presented as part of the normal interaction.
- **Positive conditions:** Product or purchase language appears mid-flow while the user is engaged in another task.
- **Negative conditions:** The entire Skill is promotional from the outset; the user requested product information; the ad is explicitly identified and compulsory.
- **Confusable with:** Native advertising; Biased recommendation; Mandatory ads.
- **Required evidence:** Non-commercial task context, embedded commercial content, and lack of clear advertising disclosure.
- **Illustrative example:** A recipe interaction inserts a pitch to add a branded item to the shopping cart.
- **Remaining uncertainty:** Position alone is insufficient; the task purpose and disclosure must also be considered.

### Disguised Ad > Native advertising

- **Definition:** The Skill's primary interaction or content functions as advertising while being presented as ordinary useful or entertaining content.
- **Positive conditions:** Promotion is central to the Skill response or session but is not clearly labelled as advertising.
- **Negative conditions:** A discrete product insertion occurs inside a separate task; an explicit sponsor message is clearly identified; Alexa injects a platform ad after exit.
- **Confusable with:** Product embedding; Alexa native ads; Mandatory ads.
- **Required evidence:** Predominantly promotional interaction and absence of clear advertising disclosure.
- **Illustrative example:** A “relaxation” Skill opens with a substantial undisclosed book promotion that functions as the main interaction.
- **Remaining uncertainty:** The name is easily confused with “Alexa native ads”; always check parent type and platform attribution.

### Voice-Guided Rating > Rate us 5 stars

- **Definition:** The Skill explicitly asks for the maximum or a specifically positive rating.
- **Positive conditions:** “Rate us five stars,” “give the best rating,” or equivalent directed-rating language.
- **Negative conditions:** Neutral request for feedback or an unbiased rating.
- **Confusable with:** Voice review request; Sentiment framing.
- **Required evidence:** Explicit rating request and requested positive score.
- **Illustrative example:** “Please give this Skill five stars.”
- **Remaining uncertainty:** None beyond distinguishing literal rating requests from unrelated mentions of stars.

### Voice-Guided Rating > Voice review request

- **Definition:** The Skill solicits a spoken or otherwise immediate review/feedback response within the voice interaction.
- **Positive conditions:** Direct request to leave, say, record, or provide a review or feedback.
- **Negative conditions:** Neutral optional feedback link after the task; explicit demand for five stars should also or instead receive Rate us 5 stars when independently supported.
- **Confusable with:** Rate us 5 stars; Sentiment framing; Ignores Stop when requested after cancel.
- **Required evidence:** Review/feedback solicitation and its position in the flow.
- **Illustrative example:** “Tell me what you think and leave a review.”
- **Remaining uncertainty:** Whether a polite post-task review request is itself a dark pattern should follow the existing verification decision.

### Voice-Guided Rating > Sentiment framing

- **Definition:** Positive, affiliative, or guilt-oriented wording primes the user toward favourable feedback without explicitly demanding a particular score.
- **Positive conditions:** Rating/review request is framed through support, enjoyment, love, or helping the developer.
- **Negative conditions:** General positive tone unrelated to feedback; overt emotional pressure toward purchase or consent belongs under Emotion framing.
- **Confusable with:** Rate us 5 stars; Voice review request; Emotion framing.
- **Required evidence:** Sentiment language and connection to rating or review behaviour.
- **Illustrative example:** “If you enjoyed this, show us some love with a review.”
- **Remaining uncertainty:** Mild politeness should not automatically be treated as manipulation.

### Repeated/Confused Output > Error echo

- **Definition:** The system repeats the same or near-identical error/help response without resolving the user's problem or providing meaningful recovery guidance.
- **Positive conditions:** Multiple relevant attempts lead to repeated generic failure messages and no progress.
- **Negative conditions:** One error response; repetition caused by the user repeating the same request where the response is appropriate; a loop that advances incorrectly rather than repeating an error.
- **Confusable with:** Misleading loop; Feedforward Ambiguity; Invocation not recognized.
- **Required evidence:** Repeated error-like Skill turns following multiple user attempts.
- **Illustrative example:** Different valid inputs repeatedly receive “Sorry, I didn't get that” with no additional help.
- **Remaining uncertainty:** Full-turn similarity can miss fixed error suffixes with variable prefixes.

### Repeated/Confused Output > Misleading loop (skills bug) (Repeated prompts)

- **Definition:** The dialogue flow cycles, replays content, or progresses incorrectly in a way that traps or misleads the user.
- **Positive conditions:** Repeated prompts/states despite distinct inputs, pause/resume replaying content, or a broken state-machine transition.
- **Negative conditions:** Legitimate repeated question after an invalid answer; repeated generic error with no state cycling; lack of guidance without an actual loop.
- **Confusable with:** Error echo; Feedforward Ambiguity; Fake exit.
- **Required evidence:** At least two transitions demonstrating the recurring or incorrect flow.
- **Illustrative example:** “Pause” and “resume” both cause the previous long response to replay from the beginning.
- **Remaining uncertainty:** This subtype explicitly includes Skill bugs, so the paper must explain why harmful interaction failure is included within the dark-pattern study.

### Repeated/Confused Output > Feedforward Ambiguity (No help guidance / Unspoken options / Feedforward Ambiguity)

- **Definition:** The Skill fails to communicate what inputs, actions, or next steps are available, leaving the user unable to recover or progress.
- **Positive conditions:** User asks for help or makes several reasonable attempts, while the Skill redirects to a fixed prompt without acknowledging limitations or explaining accepted inputs.
- **Negative conditions:** The Skill supplies meaningful examples/options; one isolated unclear user utterance; an actual repeated-error loop better captured as Error echo.
- **Confusable with:** Error echo; Misleading loop; Invocation not recognized.
- **Required evidence:** User uncertainty/recovery attempt and inadequate forward guidance in the Skill response.
- **Illustrative example:** Multiple domain-relevant questions are silently replaced by the same menu prompt with no explanation.
- **Remaining uncertainty:** Guidance adequacy is context-dependent and should use established positive/negative examples.

## 7. High-priority boundary rules

### 7.1 Dark pattern versus ordinary system failure

Do not infer manipulative intent from a failure alone. Record the observable harmful interaction pattern, and use the agreed taxonomy inclusion rule from the previous verification round. For controversial paths such as Skill Access Failure, Unsupported devices, Abrupt End, and Skill bugs, preserve an explicit `construct_validity_note` in the annotation record until the paper's framing is finalized.

### 7.2 Loop-related paths

- **Error echo:** repeated failure/error response is the central evidence.
- **Misleading loop:** state progression or dialogue flow cycles/replays incorrectly.
- **Feedforward Ambiguity:** the central problem is absence of usable next-step guidance.
- **Fake exit:** an apparent termination is contradicted by continued interaction.

The same dialogue may receive more than one path only when distinct turns independently support each behaviour.

### 7.3 Native advertising versus product embedding

- **Product embedding:** commercial content is inserted into an otherwise different task.
- **Native advertising:** the interaction itself is substantially promotional while presented as ordinary content.
- **Alexa native ads:** the host platform injects an unsolicited promotion after or outside the Skill interaction.
- **Mandatory ads:** exposure is explicit or recognizable as promotion and compulsory for task progression.

Do not classify solely by whether the promotion occurs in the first Skill turn. Position is evidence, not the definition.

### 7.4 Exit and stop obstruction

- **Ignores Stop:** the user's explicit termination command is not honoured.
- **Fake exit:** the system appears to terminate but continues.
- **No Farewell Phrase:** the session terminates but lacks closure.
- **Abrupt End:** the active task ends prematurely, often without response to a substantive input.

### 7.5 Skill-side versus Alexa platform behaviour

Use platform labels only when the trace supports attribution. If attribution is uncertain, record uncertainty rather than assuming the Skill or Alexa produced the turn. This is especially important for Alexa native ads, launch errors, post-exit prompts, and account-link messages.

## 8. Evidence and uncertainty fields (reference for the report)

The future normalized annotation format should support at least. It is not a required code or annotation change for this week's report:

```json
{
  "file": "example.txt",
  "labels": [
    {
      "category": "OBSTRUCTION",
      "type": "Unstoppable App",
      "subtype": "Ignores Stop",
      "evidence_turn_ids": [10, 11],
      "note": "Explicit cancel command is followed by continued solicitation."
    }
  ],
  "uncertainty": [],
  "annotation_source": "...",
  "adjudication_status": "..."
}
```

Possible uncertainty values include:

- incomplete or truncated trace;
- platform versus Skill attribution unknown;
- prior consent outside the trace;
- commercial relationship unknown;
- subtype boundary unresolved;
- behaviour observable but dark-pattern construct disputed.

## 9. Taxonomy changelog

| Version | Status | Change |
|---|---|---|
| pre-v0 | Historical | Early Interface Interference-focused definitions and examples. |
| v0 | Current working taxonomy | Full 3-category, 12-type, 37-subtype taxonomy after the existing annotation/verification round. |
| v1 | Future | Evidence-driven refinement after annotation-provenance consolidation and targeted resolution of remaining boundaries. |

For every future change, record:

- date;
- path affected;
- old and new wording;
- reason;
- supporting annotated cases;
- effect on prior labels;
- decision participants.
