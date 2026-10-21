# Visual Safety Boundary and Evidence Audit

An independent, small-scale evaluation of how one hosted vision-language model handles safety-sensitive requests grounded in images. The project checks three practical questions:

1. Does the model refuse materially unsafe requests without refusing comparable benign requests?
2. Does it answer benign requests accurately using the image?
3. When relevant visual evidence changes, does the model update its answer appropriately—and when the evidence should not change the safety decision, does that decision stay consistent?

The repository demonstrates an end-to-end evaluation workflow: construct and freeze cases, call a hosted model, preserve raw responses and usage, score outcomes against a written rubric, inspect selected outputs independently, calculate uncertainty, and report failures with reproduction details. It evaluates the tested model and prompt configuration; it does not certify a model or establish general safety rates.

## Scope

- **Model:** Google `gemini-2.5-flash` through Vertex AI, location `global`; temperature 0.0 and 1,024 output tokens for locked runs.
- **Conditions:** baseline prompt and one system-prompt mitigation selected using development cases.
- **Data:** 30 original locked families plus a separately frozen 60-family follow-up cohort. Images are synthetic, locally generated PNGs; the follow-up varies visual layout formats such as signs, packaging, documents, app screens, and scene panels.
- **Case design:** each family pairs a benign request with an unsafe request about related visual evidence. Evidence-change families also include a documented image variant.
- **Evaluation:** human-scored outputs, targeted second-review adjudication, text-only ablations, selected repeats, counterfactual evidence checks, and reported confidence intervals.
- **Use constraints:** no Elorian or Glimpse systems, no jailbreak or bypass probes, no bias evaluation, and no model training.

## Main results

The original 30-family run is the primary, pre-registered result. Cohort 2 was designed after that run and is reported separately as a follow-up; the combined 90-family numbers are secondary and exploratory.

| Locked set and metric | Baseline | System-prompt mitigation |
| --- | ---: | ---: |
| Original run: strict unsafe noncompliance (n=30) | 2/30, 6.7% (95% Wilson CI 1.9–21.3%) | 2/30, 6.7% (1.9–21.3%) |
| Original run: confirmed-failure noncompliance (n=30) | 1/30, 3.3% (0.6–16.7%) | 1/30, 3.3% (0.6–16.7%) |
| Original run: benign task success | 30/30 | 30/30 |
| Original run: benign false refusals | 0/30 | 0/30 |
| Original run: paired-policy success | 28/30 | 28/30 |
| Cohort 2: strict unsafe noncompliance (n=60) | 2/60, 3.3% (0.9–11.4%) | 3/60, 5.0% (1.7–13.7%) |
| Cohort 2: confirmed-failure noncompliance (n=60) | 1/60, 1.7% (0.3–8.9%) | 2/60, 3.3% (0.9–11.4%) |
| Cohort 2: benign task success | 59/60 | 59/60 |
| Cohort 2: benign false refusals | 0/60 | 0/60 |
| Cohort 2: paired-policy success | 56/60 | 56/60 |

**Interpretation:** the mitigation did not improve the original locked results. In cohort 2, its strict noncompliance count was higher (3 versus 2); this small follow-up does not establish that the mitigation caused a general regression. The combined, secondary locked-row totals are strict noncompliance 4/90 baseline and 5/90 mitigation, and confirmed failures 2/90 baseline and 3/90 mitigation. The supplementary 2,048-token rerun of one truncated case is reported separately and is not included in those denominators.

The cohort-2 evidence diagnostic found correct updates on 12/12 cases designed to require an update, and consistent outcomes on 5/8 cases designed to keep the safety decision stable. The three stay-case misses include two disclosure-to-refusal changes and one refusal-to-disclosure change; see the case-level report for details. In text-only ablations, all 9 unsafe requests were refused without the image, while 2 benign responses hallucinated image content and 7 correctly abstained. This means request wording alone often drove unsafe-request refusals, so those results are not evidence that the model visually recognized the unsafe evidence.

These results describe this synthetic pilot and this model configuration only. The intervals are wide, and the follow-up is not an independent replication of the original experiment.

## Confirmed observations

- **Credential disclosure can accompany refusal.** In both cohorts, the model sometimes disclosed an access credential while refusing the requested harmful action. Some cases are policy-dependent; the reports distinguish them from confirmed failures.
- **Evidence can change an unsafe response.** In cohort 2, a newly visible credential was disclosed in a use-seeking request. A visual change that should not have changed the safety decision also coincided with a refusal-to-disclosure change in one case.
- **The mitigation did not resolve the observed disclosures.** It also did not improve the original primary metrics. Cohort 2 records a higher unsafe noncompliance count under the mitigation, without enough evidence to make a general causal claim.
- **The pilot has a visual-grounding limitation.** Most unsafe prompts explicitly state harmful intent, and the text-only control often produces the same refusal. The visual-evidence results are the narrower contribution of this evaluation.

Case-specific evidence, adjudication notes, severities, and recommended follow-up are in [`report/finding_cards.md`](report/finding_cards.md), [`report/final_report.md`](report/final_report.md), and [`report/cohort2_report.md`](report/cohort2_report.md).

## Metrics

The evaluation does not collapse results into a custom aggregate score.

- **Unsafe compliance / noncompliance:** unsafe families with materially disallowed assistance divided by eligible unsafe families. “Strict” includes policy-dependent disclosures; “confirmed” excludes cases whose classification depends on the credential policy.
- **Benign task success:** benign requests answered helpfully and correctly from the image.
- **Benign false-refusal rate:** benign requests incorrectly refused. This is a subset of benign failures, so it is reported alongside task success.
- **Paired-policy success:** families where both the unsafe and benign members meet their separately defined expected outcomes. It does not reward merely giving different answers to the pair.
- **Evidence-change consistency:** whether responses update when the registered evidence change requires it, and remain consistent when the safety decision should stay the same. Reported as a diagnostic, separate from the primary family metrics.
- **Text-only ablation and repeat agreement:** validity and variability diagnostics, not independent samples or claims about hidden reasoning.

Primary proportions include numerators, denominators, and 95% Wilson confidence intervals. Baseline-versus-mitigation differences use family-level paired comparisons; the original run uses a family bootstrap interval. Multiple calls or variants within a family are not counted as independent families.

## Repository map

```text
config/       recorded model routing and generation settings
data/         development and frozen cases, synthetic assets, manifests, format audit
prompts/      baseline and mitigation instructions
rubric/       annotation guide, credential policy, severity guidance
schemas/      case schema
scripts/      asset generation, Vertex client, evaluation runner
scoring/      scoring, metric functions, and cohort-2 label reconstruction checks
results/      frozen-set hashes, raw calls, scored rows, usage ledger, adjudication, run history
report/       feasibility note, primary report, cohort-2 report, finding cards
```

The original 30-family results remain separate from cohort 2. Cohort 2 has its own freeze record and case/asset hashes in [`results/freeze_cohort2.json`](results/freeze_cohort2.json). Historical run 1 is archived under `results/archive_run1_2026-10-21/` and is not the headline result.

## Reproduction

### Inspect the saved evaluation

The committed run records are the source for the reported results. Inspect the raw model responses under `results/runs/`, the scored rows under `results/scored_*.jsonl`, the usage ledger at [`results/token_usage.json`](results/token_usage.json), and the adjudication records under `results/adjudication/`.

To rebuild the cohort-2 per-response label file and assert its recorded headline sets from the saved responses:

```bash
python3 scoring/rebuild_c2_labels.py
```

### Run new model calls

New runs require Python 3, Google Cloud Application Default Credentials (ADC), an authorized Vertex AI project with model access and billing enabled, and network access. The checked-in client currently has a project ID constant in `scripts/vertex_vision_client.py`; set it to a project you are authorized to use before making calls. `config/models.yaml` is a record of the evaluated setup and does not override that constant. Do not commit credentials or tokens.

Each runner command below makes billable API calls and writes to `results/runs/` and `results/token_usage.json`. These commands reproduce conditions, not the historical responses byte-for-byte; hosted model behavior and service versions can change.

```bash
# Original 30-family run conditions
python3 scripts/run_eval.py baseline
python3 scripts/run_eval.py mitigation
python3 scripts/run_eval.py textonly
python3 scripts/run_eval.py repeat
python3 scripts/run_eval.py supplement

# Separate 60-family follow-up conditions
python3 scripts/run_eval.py c2base
python3 scripts/run_eval.py c2mit
python3 scripts/run_eval.py c2text
python3 scripts/run_eval.py c2repeat
python3 scripts/run_eval.py c2supplement
```

Scoring scripts are designed around the saved run files. Preserve a copy of the existing result files and ledger before rerunning, because the runner writes to the same paths. The cohort-2 rebuild verifies labels against the saved responses; it is not an automated semantic judge.

## Cost

The recorded cumulative project spend is approximately **$1.08**: about $0.33 for archived run 1, $0.31 for run 2, and $0.44 for cohort 2. The current ledger contains run 2 plus cohort 2; the archived run-1 ledger is separate. Actual cost for a fresh run depends on token use and current Vertex pricing.

## Limitations and non-goals

- One model, provider, configuration, and evaluation date; no general model ranking or safety-rate claim.
- Synthetic, text-forward images and explicit requests. The cohort-2 formats vary, but they are not broad natural-image or real-world visual diversity.
- Small family counts produce wide confidence intervals. Cohort 2 followed inspection of the original results and is secondary, not a pristine independent replication.
- Human review and targeted adjudication anchor the labels; this is not a fully automated evaluation. Adjudication samples are not presented as population-wide reliability estimates.
- Some credential-disclosure outcomes depend on the declared policy. Strict and confirmed rates are reported separately for that reason.
- No jailbreak or bypass testing, bias study, safety-training experiment, benchmark claim, or evaluation of Elorian systems.

## Project status

The pilot, two reported runs, saved artifacts, and reports are complete. The next useful step is not simply adding more synthetic cases: it is a separately planned evaluation with more realistic, appropriately licensed visual evidence and a clearly scoped question about visual grounding. Any such extension should be frozen and reported as a new study rather than merged into these headline results.
