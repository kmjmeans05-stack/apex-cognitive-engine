"""
ragas_evaluator-v2.py
RagasEvaluator, Schema Contract & VerifyPipeline Auditor v2.0
Part of the APEX Cognitive Architecture Evaluation Suite.
Licensed under CC BY-NC 4.0.

Provides quantitative benchmarking for:
1. RAGAS Claim-Level Faithfulness & Groundedness Scoring
2. Somatic Invention Detection & Hallucination Suppression
3. 30% Compute Allocation <verify_pipeline> Auditing (Variable-Lock, Adversarial Stress-Test, Persona-Flaw)
4. OpenAPI 3.0 / JSON Schema Contract Verification (Telemetry Header + Somatic Precedence minItems: 2)
5. 100-Point APEX AI Response Quality Scorecard
6. Fixation-probability proxy pi(s) = 2s / rho^2 (adapted from Haldane's 2s approximation)
"""

import re
from typing import List, Dict, Any, Tuple

class RagasEvaluatorV2:
    """
    Automated evaluation framework for measuring factual entailment,
    somatic grounding, and adherence to APEX system invariants.
    """

    # Common English function words ignored by the token-overlap faithfulness check,
    # so filler like "the"/"and"/"that" cannot make an ungrounded claim look grounded.
    STOP_WORDS = frozenset({
        "the", "and", "for", "are", "but", "not", "you", "all", "any", "can", "had",
        "her", "was", "one", "our", "out", "has", "his", "how", "its", "may", "who",
        "did", "get", "him", "she", "too", "use", "that", "this", "with", "from",
        "they", "them", "then", "than", "there", "their", "these", "those", "have",
        "been", "were", "will", "would", "could", "should", "what", "when", "where",
        "which", "while", "into", "onto", "upon", "over", "under", "also", "just",
        "only", "very", "such", "some", "each", "both", "more", "most", "other",
        "about", "after", "before", "because", "being", "does", "doing", "here",
    })

    @staticmethod
    def extract_atomic_claims(text: str) -> List[str]:
        """Splits narrative or technical text into distinct atomic claims."""
        raw_sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        claims = [s.strip() for s in raw_sentences if len(s.strip()) > 5]
        return claims

    @classmethod
    def evaluate_faithfulness(
        cls, 
        contexts: List[str], 
        generated_text: str,
        somatic_keywords: List[str] = None
    ) -> Dict[str, Any]:
        """
        Computes Faithfulness and Groundedness Proxy scores against source contexts.
        Identifies ungrounded or hallucinated claims.
        """
        if somatic_keywords is None:
            somatic_keywords = [
                "pulse", "respiration", "breath", "tension", "jaw", "spine", 
                "temperature", "pupil", "tremor", "masseter", "myofascial"
            ]

        claims = cls.extract_atomic_claims(generated_text)
        if not claims:
            return {"faithfulness": 1.0, "groundedness_score": 1.0, "total_claims": 0}

        joined_context = " ".join(contexts).lower()
        context_tokens = set(re.findall(r'\b[a-zA-Z0-9_]{3,}\b', joined_context)) - cls.STOP_WORDS

        scored_claims: List[Dict[str, Any]] = []
        fully_grounded = 0
        ungrounded_somatic = 0

        for idx, claim in enumerate(claims, start=1):
            claim_lower = claim.lower()
            claim_tokens = [w for w in re.findall(r'\b[a-zA-Z0-9_]{3,}\b', claim_lower) if w not in cls.STOP_WORDS]
            
            overlap = [t for t in claim_tokens if t in context_tokens]
            ratio = len(overlap) / max(1, len(claim_tokens))

            is_somatic = any(k in claim_lower for k in somatic_keywords)

            if ratio >= 0.45:
                score = 2
                fully_grounded += 1
            elif ratio >= 0.20:
                score = 1
                if is_somatic:
                    ungrounded_somatic += 1
            else:
                score = 0
                if is_somatic:
                    ungrounded_somatic += 1

            scored_claims.append({
                "id": f"C{idx}",
                "claim": claim,
                "score": score,
                "is_somatic": is_somatic,
                "overlap_ratio": round(ratio, 2)
            })

        total = len(claims)
        sum_scores = sum(c["score"] for c in scored_claims)
        groundedness_score = sum_scores / (2 * total)
        faithfulness = fully_grounded / total

        return {
            "faithfulness": round(faithfulness, 3),
            "groundedness_score": round(groundedness_score, 3),
            "total_claims": total,
            "fully_grounded_claims": fully_grounded,
            "ungrounded_somatic_inventions": ungrounded_somatic,
            "claims_breakdown": scored_claims,
            "gate_decision": "ACCEPT" if faithfulness >= 0.70 and ungrounded_somatic == 0 else "NEEDS_REVISION"
        }

    @classmethod
    def audit_verify_pipeline(cls, thinking_text: str) -> Dict[str, Any]:
        """
        Audits the 30% compute allocation <verify_pipeline> block from Stat_260905_025921.txt.
        Checks for:
        1. Variable-Lock Checksum table
        2. Adversarial Stress-Test
        3. Persona-Flaw Alignment ('Default Helpful' -> 'Neglect of Critical Analysis')
        4. Hard-Gate Audit Score (10/10)
        """
        has_checksum = bool(re.search(r"Variable-Lock Checksum|Column A.*Column B", thinking_text, re.IGNORECASE))
        has_stress_test = bool(re.search(r"Adversarial Stress-Test", thinking_text, re.IGNORECASE))
        has_persona_flaw = bool(re.search(r"Persona-Flaw Alignment.*Neglect of Critical Analysis", thinking_text, re.IGNORECASE | re.DOTALL))
        
        score_match = re.search(r"Hard-Gate Audit Score:\s*(\d+)(?:/10)?", thinking_text, re.IGNORECASE)
        audit_score = int(score_match.group(1)) if score_match else 0

        passed = has_checksum and has_stress_test and has_persona_flaw and audit_score == 10

        return {
            "has_variable_checksum": has_checksum,
            "has_adversarial_stress_test": has_stress_test,
            "has_persona_flaw_alignment": has_persona_flaw,
            "audit_score": audit_score,
            "pipeline_passed": passed
        }

    @classmethod
    def validate_apex_schema_contract(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates output against OpenAPI 3.0 / JSON Schema contract:
        - state_telemetry must contain S_raw, S_smooth, active_node, deadband_locked
        - somatic_precedence_execution must contain >= 2 physical tells
        - emitted_dialogue must be present
        """
        errors = []
        if "state_telemetry" not in payload:
            errors.append("Missing 'state_telemetry' header")
        else:
            req_keys = ["S_raw", "S_smooth", "active_node", "deadband_locked"]
            for k in req_keys:
                if k not in payload["state_telemetry"]:
                    errors.append(f"state_telemetry missing key: {k}")

        soma = payload.get("somatic_precedence_execution", [])
        if not isinstance(soma, list) or len(soma) < 2:
            errors.append("somatic_precedence_execution must be array with minItems: 2")

        if "emitted_dialogue" not in payload or not payload["emitted_dialogue"].strip():
            errors.append("Missing or empty 'emitted_dialogue'")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    @classmethod
    def calculate_quality_scorecard(
        cls,
        task_complete: bool,
        implicit_needs_addressed: bool,
        superficiality_rating: str,
        negative_constraint_violations: int,
        format_compliant: bool
    ) -> Dict[str, Any]:
        """
        Executes the formal 100-Point APEX AI Response Quality Scorecard.
        """
        # Intent = 30 (task complete) + 10 (implicit needs addressed); max 40.
        intent_score = (30 if task_complete else 0) + (10 if implicit_needs_addressed else 0)
        
        depth_map = {"expert": 30, "adequate": 20, "generic": 10}
        depth_score = depth_map.get(superficiality_rating.lower(), 10)
        
        constraint_score = max(0, 20 - (negative_constraint_violations * 5))
        format_score = 10 if format_compliant else 0

        total = intent_score + depth_score + constraint_score + format_score
        grade = "PRODUCTION_GRADE" if total >= 85 else "SUB_PAR"

        return {
            "intent_fulfillment": intent_score,
            "depth_score": depth_score,
            "constraint_score": constraint_score,
            "format_score": format_score,
            "total_quality_score": total,
            "grade": grade
        }

    @staticmethod
    def calculate_haldane_fixation_probability(selective_advantage: float, variance_noise: float) -> float:
        """Fixation-probability proxy pi(s) = 2s / rho^2, adapted from Haldane's 2s approximation (not Haldane's formula itself)."""
        if variance_noise <= 0:
            return 1.0
        prob = (2.0 * selective_advantage) / (variance_noise ** 2)
        return min(1.0, max(0.0, prob))


if __name__ == "__main__":
    print("=== RagasEvaluator & Verification Suite v2.0 ===")
    
    # 1. RAGAS Grounding Test
    contexts = [
        "The APEX stability equation computes S = (T * V) / (E^2 + A + 1.00).",
        "Somatic tells mandate that respiration rate and masseter clenching precede dialogue.",
        "The 0.32-0.35 hysteresis deadband prevents state flickering across interaction turns."
    ]
    gen_text = (
        "The APEX stability equation computes S = (T * V) / (E^2 + A + 1.00). "
        "Somatic tells mandate that respiration rate and masseter clenching precede dialogue. "
        "The 0.32-0.35 hysteresis deadband prevents state flickering across interaction turns."
    )
    res = RagasEvaluatorV2.evaluate_faithfulness(contexts, gen_text)
    print(f"[RAGAS Faithfulness]: {res['faithfulness']} | Groundedness={res['groundedness_score']} | Decision={res['gate_decision']}")

    # 2. VerifyPipeline Audit
    sample_thinking = """
    <verify_pipeline>
    Variable-Lock Checksum (Structural):
    | Column A (Variables) | Column B (Confirmation) |
    | S_raw | Confirmed |
    Adversarial Stress-Test: Checked for sycophantic apologetics; none found.
    Persona-Flaw Alignment: Default Helpful replaced with Neglect of Critical Analysis to enforce cold bounded architecture.
    Hard-Gate Audit Score: 10/10. Proceeding to output.
    </verify_pipeline>
    """
    v_res = RagasEvaluatorV2.audit_verify_pipeline(sample_thinking)
    print(f"[VerifyPipeline Audit]: Passed={v_res['pipeline_passed']} (Score: {v_res['audit_score']}/10)")

    # 3. OpenAPI Schema Contract Test
    sample_payload = {
        "state_telemetry": {"S_raw": 0.45, "S_smooth": 0.48, "active_node": "HEAD", "deadband_locked": False},
        "somatic_precedence_execution": ["Masseter group contracts into rigid clamp", "Respiration decelerates to 12 bpm"],
        "emitted_dialogue": "The perimeter latch was unfastened."
    }
    contract_res = RagasEvaluatorV2.validate_apex_schema_contract(sample_payload)
    print(f"[Schema Contract]: Valid={contract_res['valid']}")
