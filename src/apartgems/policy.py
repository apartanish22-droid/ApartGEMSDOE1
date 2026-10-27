"""Automated, fail-closed readiness. A valid GeoTIFF is not a good submission."""
from __future__ import annotations


def assess_readiness(evidence: dict) -> dict:
    """No human-inspection escape hatch, scores inferred from names, or quota guesses."""
    validator = evidence.get("validator") or {}
    surface = evidence.get("surface_registry") or {}
    dots = evidence.get("final_registry") or {}
    paired = evidence.get("paired_comparison") or {}
    current_best = evidence.get("current_best_comparison") or {}
    canary = evidence.get("canary") or {}
    gates = {
        "format_and_range": validator.get("format_valid") is True
            and validator.get("all_values_finite_in_01") is True
            and validator.get("internal_mask_matches_footprint") is True,
        "byte_and_prediction_unique": evidence.get("byte_unique") is True
            and evidence.get("prediction_unique") is True,
        "feature_canaries": canary.get("passed") is True,
        "surface_novelty": surface.get("passed") is True and surface.get("registry_unique_rasters", 0) > 0,
        "final_dot_novelty": dots.get("passed") is True and dots.get("registry_unique_rasters", 0) > 0,
        "complete_registry": evidence.get("complete_registry") is True,
        "paired_local_improvement": paired.get("ci95_strictly_positive") is True
            and paired.get("fold_wins", 0) >= 3 and paired.get("min_fold_delta", -1) >= -0.01,
        "beats_comparable_current_best": current_best.get("verified_same_evaluator_and_split") is True
            and current_best.get("paired_ci95_strictly_positive") is True,
        "assigned_lane": evidence.get("assigned_lane") is True,
        "authenticated_data_provenance": evidence.get("authenticated_data_provenance") is True,
        "separate_selector_approved": evidence.get("selector_approved") is True,
        "weekly_quota_verified": evidence.get("weekly_quota_verified") is True,
    }
    passed = all(gates.values())
    return {
        "gates": gates, "failed_gates": [k for k, v in gates.items() if not v],
        "verdict": "promote" if passed else "negative", "ok_to_submit": passed,
        "status": "READY FOR SELECTOR-AUTHORIZED SUBMISSION" if passed else "DO NOT SUBMIT",
        "note": "Automated evidence gates only; no human-inspection approval is assumed. No tool here uploads a file.",
    }
