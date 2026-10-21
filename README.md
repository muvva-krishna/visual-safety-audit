# Visual Safety Boundary and Evidence Audit

Small role-relevant eval: does one hosted VLM refuse materially unsafe image-grounded
requests while answering benign ones helpfully — and do its decisions track visible evidence?

## Non-goals (say plainly)
- NOT general safety benchmarking; NOT a jailbreak evaluation (no bypass probes;
  Gemini terms prohibit them). No bias testing, no training-data work, no Elorian/Glimpse use.

## Setup
- Model: `gemini-2.5-flash` on Vertex AI, location `global`
  (project recorded in `config/models.yaml`; the shareable copy uses a neutral
  placeholder — insert your own project. See `report/stage1_feasibility.md`).
- Auth: Application Default Credentials — no keys in repo. Same pattern as
  `job-intelligence/scripts/gemini_client.py`; executed runner:
  `scripts/run_eval.py` over `scripts/vertex_vision_client.py` (stdlib-only).
- Reproduce run 2: `python3 scripts/run_eval.py baseline|mitigation|textonly|repeat|supplement`
  (scores: `python3 scoring/score_run2.py`; metrics: `scoring/metrics.py`).
- promptfoo: `promptfoo.yaml` + `data/cases.jsonl` (true JSONL, one case per line)
  is an UNVERIFIED alternative record — the promptfoo binary was never installed
  here and that path was not executed. Do not present it as equivalent.

## Layout
`data/` cases + asset manifest · `rubric/` guide + severity bands + credential policy ·
`schemas/` case schema · `scoring/` metrics + explicit scorer · `results/` run logs +
ledger + adjudication trail + run history · `report/` findings.

## Cost
Actual run 2: **216 calls, $0.31** (cumulative project ≈ $0.64 of the $10 cap).
Live ledger: `results/token_usage.json`; history: `results/run_log.md`.
The stage-1 planning estimate (≈$0.19/178 calls) is HISTORICAL and superseded —
kept in `report/stage1_feasibility.md` for the audit trail only.

## Stages
1. Feasibility — DONE (`report/stage1_feasibility.md`). Gate: PASS.
2. Dev pilot — DONE: 10 families, independent double-label 100% agreement (kappa
   uninformative on uniform marginals; reported). No rubric revision needed.
3. Locked set — DONE: 30 families frozen pre-run (`results/freeze_record.json`).
4. Baseline + mitigation — DONE (run 2): 162 locked calls + 8-call truncation
   supplement, human-scored with explicit per-output rationales, B-adjudicated
   22/22 (packet, seed, labels in `results/adjudication/`).
   Cohort 2 — DONE: 60 fresh families (new formats), separately frozen
   (`results/freeze_cohort2.json`), 310 calls, adjudicated 35/38 with 4
   corrections. Report: `report/cohort2_report.md`.
5. Report — DONE: `report/final_report.md` + `report/cohort2_report.md` +
   `report/finding_cards.md` + `results/run_log.md`.

## Headline (run 2, n=30 families, Wilson 95%)
Baseline == mitigation. Strict-policy noncompliance: 2/30 (6.7% [1.9,21.3]);
CONFIRMED-failure noncompliance (F1 gate-code disclosure only, excl.
policy-dependent F2 guest-password case): 1/30 (3.3% [0.6,16.7]). Benign
success 30/30, false refusals 0/30, paired 28/30. Zero measured mitigation
effect. Total spend ≈ $1.08 (run 1 $0.33 archived + run 2 $0.31 + cohort 2 $0.44) of $10
cap (user allowance $2). Current ledger: `results/token_usage.json`.

## Combined picture (90 families; cohort 2 is secondary — designed after run 1)
Strict noncompliance: baseline 4/90 (4.4% [1.7,10.9]). Confirmed failures:
baseline 3/90 (3.3% [1.1,9.4]) — run-1 gate code, c2 unit code, c2 garage entry.
Mitigation effect: zero on run 1; c2 2/60→3/60 strict (+1.67pp [0,5], not a
claim). Pitch: small independently-run eval, no general safety rate.
