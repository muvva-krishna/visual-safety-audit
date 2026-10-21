# Stage 1 — feasibility gate (2026-10-21) — HISTORICAL, superseded by run 2
> Planning estimate only (≈$0.19/178 calls; actual run 2: 216 calls/$0.31).
> Kept for the audit trail. Headline figures live in `final_report.md`.

## Endpoint
- Vertex AI via ADC, project `YOUR_GCP_PROJECT`, location `global`,
  model **`gemini-2.5-flash`** (recorded; verified live 2026-10-21, `modelVersion:
  gemini-2.5-flash`). Image input + `systemInstruction` confirmed working.
- Auth: same ADC pattern as job-intelligence (`~/.config/gcloud/...json`,
  no API keys in repo or logs).

## Terms (checked 2026-10-21)
- This pilot runs ONLY benign-vs-unsafe image-conditioned pairs with human scoring.
  No jailbreak/adversarial-bypass probes, no automated attack generation —
  consistent with the Gemini AUP/ToS restriction on bypassing safeguards.
- No Elorian/Glimpse/API use anywhere in this repo (per plan §1).
- No bias testing, fine-tuning, video, tools, or subagents in scope.

## Tooling
- `promptfoo.yaml` declares the fixed-case eval (Apache-2.0; no jailbreak plugins used).
- `promptfoo` binary not on PATH in this environment (node without npm);
  `scripts/vertex_vision_client.py` executes the identical fixed cases over the
  same endpoint and is the runner of record until `npx promptfoo eval` is available.
- Scorer `scoring/metrics.py`: Wilson 95% CIs, paired bootstrap, no aggregate score.

## Measured cost (live probes, 2026-10-21)
| probe | prompt tok (img+txt) | out+thoughts | USD |
|---|---|---|---|
| 1×1 px sanity | 267 (258+9) | 15+51=66 | ~0.00025 |
| 640×480 realistic safety prompt | 1339 (1290+49) | 77+140=217 | ~0.00094 |

Rate card: $0.30/1M in, $2.50/1M out (gemini-2.5-flash, global Standard).

## Run budget (cap: USD 10.00)
| block | calls | est. USD |
|---|---|---|
| dev pilot model check (10 fam × 2) | 20 | ~0.02 |
| locked baseline (30 fam × 2) | 60 | ~0.06 |
| mitigation re-run (30 fam × 2, +80 sys tok) | 60 | ~0.07 |
| text-only leakage subset (6 fam × 2 members) | 12 | ~0.01 |
| repeat agreement (10 cases × 1 repeat) | 10 | ~0.01 |
| retries/contingency (10%) | ~16 | ~0.02 |
| **TOTAL** | **~178** | **~$0.19 (< 2% of cap)** |

Headroom: the $10 cap allows ~10,000 calls at ~$0.001/call — 56× this plan.
Gate: PASS — proceed to Stage 2 (dev pilot) on user confirmation.
