#!/usr/bin/env python3
"""Write the H-SC1 run card JSON from measured evidence files (no typed numbers).

Verdict rule (fixed before measuring, per the session protocol):
  * 'negative' unless ALL hold: uniqueness gate PASS (registry, 3-px overlap <= 70%,
    rho <= 0.90), format validator PASS, and the paired CI of the submitted policy versus
    matched random placement has a lower bound above zero at the chosen quantile.
  * A PASS on uniqueness and format is a 'download-safe' statement only. It never
    implies a slot or a score.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quantile", type=float, required=True)
    ap.add_argument("--receipt", type=Path, required=True)
    ap.add_argument("--uniqueness", type=Path, required=True)
    ap.add_argument("--holdout", type=Path, nargs="+", required=True)
    ap.add_argument("--paired", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    rec = json.loads(args.receipt.read_text())
    uq = json.loads(args.uniqueness.read_text())
    paired = json.loads(args.paired.read_text())
    hold = {}
    for p in args.holdout:
        hold.update(json.loads(p.read_text())["variants"])
    qk = f"q{args.quantile}"
    hv = hold[qk]
    pk = paired["results"][qk]

    lows = [d["paired_candidate_minus_random"]["ci95"][0] for d in pk["random_draws"]]
    deltas = [d["paired_candidate_minus_random"]["delta"] for d in pk["random_draws"]]
    paired_clears = all(lo > 0 for lo in lows)
    gate = uq["gate"]
    uniq_pass = bool(gate["unique"]) and bool(uq["complete_accessible_scan"])
    fmt_pass = bool(rec["validator"]["all_checks_passed"])
    verdict = "promote" if (uniq_pass and fmt_pass and paired_clears) else "negative"

    card = dict(
        run_id="h-sc1-" + args.receipt.stem,
        date_utc="2026-10-31",
        hypothesis=("H-SC1: concealed fault traces express as a convex crest with a coherent "
                    "10-m-scale step in 2 m USGS 3DEP-derived lidar; a catalogue-free score map "
                    "places one dot per 3-px-spaced crest maximum above a quantile threshold."),
        mechanism=("Scarp-crest geometry (step_max, convex lapneg_max) gated by 100-m coherence coh100. "
                   "Score = coh100 * sqrt(clip(step/P99) * clip(lap/P99)); P99 over lidar-valid footprint cells."),
        named_non_fault_mimic=("Road cut-banks, canal and channel banks, terrace risers and field edges: "
                               "steep steps with convex crests that are not faults (not separated by the score)."),
        quantile=args.quantile,
        threshold_score=pk["threshold_score"],
        dots_submitted=pk["dots_submitted_policy"],
        holdout=dict(
            evidence_class="HOLDOUT-DTI", evaluator_version=hv["evaluator_version"],
            holdout_draw="seed 2026, hide 20%, buffer 3 px (gems57.holdout.buffered_component_draw)",
            withheld_positive_pixels=hv["withheld_positive_pixels"],
            dti_policy_submitted=pk["candidate_dti"], ci95_policy_submitted=pk["candidate_ci95"],
            dti_global_dots_before_catalogue_policy=hv["dti"], ci95_global_dots=hv["ci95"],
            note=("The global-dot DTI keeps dots on the mapped catalogue, which is not what the file "
                  "contains. The submitted-policy DTI is the number that describes this file, and it is "
                  "pessimistic by construction because withheld truth lies on the catalogue."),
        ),
        paired_vs_matched_random=dict(
            evidence_class="HOLDOUT-DTI", random_draws=len(pk["random_draws"]),
            random_dti_mean=pk["random_dti_mean"],
            delta_candidate_minus_random_per_draw=deltas,
            paired_ci95_lower_per_draw=lows,
            clears_zero_in_all_draws=paired_clears,
        ),
        correlation_and_overlap=dict(
            registry_rasters_checked=gate["registry_rasters_checked"],
            registry_complete_accessible_scan=uq["complete_accessible_scan"],
            worst_spearman_full_footprint=gate["worst_spearman_full_footprint"],
            worst_rho_submission=gate["worst_rho_submission"],
            worst_dot_overlap_3px=gate["worst_dot_overlap"],
            worst_overlap_submission=gate["worst_overlap_submission"],
            duplicate_count=gate["duplicate_count"],
            missing_or_invalid=gate["missing_or_invalid"],
            rho_limit=gate["rho_limit"], overlap_limit=gate["overlap_limit"],
            uniqueness_file=str(args.uniqueness.resolve().relative_to(ROOT)),
        ),
        raster=dict(file=rec["file"], sha256=rec["sha256"], bytes=rec["bytes"],
                    zip_sha256=rec["zip_sha256"]),
        validator_output=dict(
            all_checks_passed=fmt_pass,
            checks=rec["validator"]["checks"],
            min=rec["validator"]["min"], max=rec["validator"]["max"],
            n_nan=rec["validator"]["n_nan"], emitted_positive_pixels=rec["validator"]["emitted_positive_pixels"],
            template_report_ok=rec["template_report"]["ok"],
        ),
        submission_name=rec["submission_name"],
        submission_note=rec["note"],
        submission_note_chars=rec["note_chars"],
        verdict=verdict,
        verdict_rule=("promote only if uniqueness PASS (complete scan), format PASS, and the paired CI vs "
                      "matched random clears zero in every draw; otherwise negative"),
        slots_used=0,
        organizer_receipt=None,
        status="Local format and registry checks only. No organizer score exists.",
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(card, indent=2, allow_nan=False, default=float) + "\n")
    print(json.dumps(dict(verdict=verdict, uniq_pass=uniq_pass, fmt_pass=fmt_pass, paired_clears=paired_clears)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
