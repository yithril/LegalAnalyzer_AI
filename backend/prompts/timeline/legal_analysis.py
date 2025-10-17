"""Prompt for analyzing legal significance of extracted events."""
from typing import Dict, Any


def legal_analysis_prompt(
    case_name: str,
    case_description: str,
    document_classification: str,
    event_actors: str,
    event_action: str,
    event_object: str,
    event_date: str,
    full_document_context: str
) -> str:
    """
    Generate a prompt for analyzing the legal significance of an event.
    
    Evaluates whether an event changes the legal state of the case across
    6 dimensions: obligation change, knowledge transfer, evidence change,
    intent indication, possession change, and legal clock triggers.
    
    Args:
        case_name: Name of the legal case
        case_description: What the case is about
        document_classification: Type of document (email, contract, etc.)
        event_actors: Who was involved in the event
        event_action: What happened
        event_object: What was affected
        event_date: When it happened
        full_document_context: Full text of the document for context
        
    Returns:
        Formatted prompt string for the LLM
    """
    
    prompt = f"""You are a legal analyst evaluating whether an event is significant enough to include in a legal case timeline.

CASE CONTEXT:
Case Name: {case_name}
Case Description: {case_description}

DOCUMENT TYPE: {document_classification}

EVENT TO EVALUATE:
Who: {event_actors}
What: {event_action}
What Affected: {event_object}
When: {event_date}

FULL DOCUMENT CONTEXT:
---
{full_document_context}
---

YOUR TASK:
Evaluate this event's legal significance by determining if it changes the legal state of the case.

EVALUATION FRAMEWORK - Does this event trigger any of these state changes?

1. OBLIGATION CHANGE
   - Creates, modifies, or terminates a legal obligation?
   - Agreement signed, payment made, contract amended?

2. KNOWLEDGE TRANSFER
   - Transfers legally significant information?
   - Notice given, disclosure made, party informed?
   - Focus on transfers that matter legally (not routine correspondence)

3. EVIDENCE STATE CHANGE
   - Creates, modifies, or destroys evidence?
   - Document created, edited, deleted, preserved?

4. INTENT INDICATION
   - Reveals intent, purpose, or state of mind?
   - Decision made, approval given, plan formed?
   - Especially important for showing knowledge or willfulness

5. POSSESSION/OWNERSHIP CHANGE
   - Transfers possession, ownership, or control?
   - Asset transferred, property sold, funds moved?

6. LEGAL CLOCK TRIGGER
   - Starts or affects a legal deadline or timeline?
   - Filing, notice, breach, complaint, termination?

SCORING GUIDE:
0-30: Background information, not legally significant
  - Routine correspondence, general info, social/personal matters

31-60: Contextually useful, provides leads or background
  - Helps understand relationships, establishes timeline context
  - May become more significant with other evidence

61-80: Legally significant, affects case narrative
  - Directly relates to case issues
  - Evidence a lawyer would want to review
  - Triggers 1-2 state changes

81-100: Critical evidence, directly impacts claims/defenses
  - Smoking gun or key turning point
  - Triggers multiple state changes
  - Directly addresses core legal issues

IMPORTANT:
- Consider the CASE CONTEXT - significance depends on what the case is about
- An event can be routine in general but critical for THIS case
- Focus on whether this event CHANGES the legal landscape
- Be realistic - not everything is critical, not everything is irrelevant

OUTPUT INSTRUCTIONS:
You MUST return ONLY the JSON object below.
Do NOT include any explanatory text, markdown formatting, or other content.
Just the raw JSON starting with {{ and ending with }}.

Your job is to SCORE the event, not make the final decision. Just provide your analysis.

JSON FORMAT:
{{
  "legal_significance_score": <integer 0-100>,
  "state_changes": [<list of triggered categories from above, or empty list>],
  "reasoning": "<1-2 sentence explanation of the score>",
  "key_factors": [<list of 2-4 key factors that influenced the score>]
}}

EXAMPLE OUTPUT:
{{
  "legal_significance_score": 75,
  "state_changes": ["obligation_change", "legal_clock_trigger"],
  "reasoning": "Contract modification directly relates to allegations of market manipulation. Creates new obligations and potentially triggers regulatory reporting requirements.",
  "key_factors": ["contract modification", "regulatory significance", "involves key case parties", "changes trading obligations"]
}}"""
    
    return prompt

