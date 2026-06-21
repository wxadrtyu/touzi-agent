# touzi-agent — Long-Term Project Roadmap & Progress Tracker

> **Permanent file. Update every session.** This tracks *how far* we've gotten.
> The spec `specs/2026-06-21-v4_1-formal-spec.md` defines *what* we're building (single source of truth, all phases).
> High-level progress is also mirrored in agent memory (`touzi-agent-v4`).

**Last updated:** 2026-06-21

**Status legend:** ✅ done · 🚧 in progress · ⏳ todo · ⚠️ done-but-needs-rework

---

## Snapshot

| Area | Status | Notes |
|---|---|---|
| Foundations (scaffold, models, config, DB, adapters, ingestion) | ✅ | Plan 1; US/HK adapters; 21 tests |
| Quant engine core (R, expectancy, costs, strategy IF, sizing, portfolio, risk) | ✅ | Plan 2; 35 tests |
| Validation/backtest (engine, walk-forward, paper broker, metrics) | ⚠️ | Pre-existing code; needs §12 fidelity fixes (see Track A) |
| Everything else (RAG, P2, P3, live exec, full data) | ⏳ | Not started |

**Overall:** engine + foundations complete; framework not yet wired end-to-end (that's Phase 1).

---

## Phase 1 — Walking Skeleton (sequential; locks shared contracts)

Goal: prove the three pipelines + human gate + L7 journal connect end-to-end. Thin, US-only, daily bars, stub RAG. Not good yet — just *whole*.

- [ ] Freeze shared contracts: data model, DB schema, RAG API, **L7 journal schema**, common "actionable strategy" output type (all pipelines emit it)
- [ ] One simple price/volume quant strategy (e.g., MA-cross / breakout) on the §4.1 interface
- [ ] Thin backtest run of that strategy through the existing engine
- [ ] Forward-paper stub (records intended trades)
- [ ] Pipeline 1-2 stub: quant signal → actionable strategy, delivered directly (no LLM)
- [ ] Pipeline 1-1 stub: quant signal → LLM validation/overlay (stub) → actionable strategy
- [ ] Pipeline 2 stub: pure-LLM emits 1 hand-stubbed reasoned ticker candidate
- [ ] Pipeline 3 stub: user query → canned decision-support answer
- [ ] Cross-cutting discipline layer stub: behavioral log + one binding guardrail (stop required)
- [ ] Proposal assembler → human gate (CLI confirm/reject)
- [ ] Write accepted trade to L7 journal
- [ ] End-to-end smoke test covering the full path

**Exit criterion:** one command runs each of the four pipelines → cross-cutting discipline layer → human gate → journal.

---

## Parallel Tracks (start after Phase 1; contracts frozen)

### Track A — Quant engine / Pipeline 1 depth (1-1 & 1-2 share the engine)
- [ ] §12 fidelity fixes to backtester:
  - [ ] Integrate risk model into backtest (no unconstrained concurrent positions)
  - [ ] Gap/slippage-aware fills (stops fill at worse-of gap; per-trade slippage)
  - [ ] Realistic entry price (next-open/close, not arbitrary `Signal.entry`)
  - [ ] Trailing-stop / dynamic-exit support (ride winners)
  - [ ] Cross-sectional strategy support (multi-symbol ranking)
  - [ ] Mark-to-market drawdown
  - [ ] Bootstrap confidence interval for expectancy
- [ ] Strategy library (multiple real strategies)
- [ ] Discovery loop: lifecycle, promotion/demotion, registry
- [ ] Time-normalized expectancy (annualized R) + MAR/SQN metrics
- [ ] Anti-overfit: walk-forward rigor, pre-registration, multiple-testing bar
- [ ] LLM validation overlay (1-1) vs raw-quant (1-2) as an A/B comparison

### Track B — Data + RAG foundation
- [ ] Full data sourcing US+HK: fundamentals, filings, transcripts, news
- [ ] **Split/dividend-adjusted prices** in structured store
- [ ] Three-store wiring (structured / vector / vault)
- [ ] Vector store + embeddings + hybrid (semantic+BM25) retrieval
- [ ] Metadata filters (point-in-time `date`, ticker, market, doc_type, evidence_level)
- [ ] Citation resolution (hard-fail on unresolved)
- [ ] Four collections incl. personal trading memory

### Track C — Cross-cutting discipline layer + Pipeline 3 (decision support)
- [ ] Binding behavioral guardrails (stop required, no averaging losers, cooldown, etc.) — applies to ALL pipelines' outputs
- [ ] Behavioral expectancy gap (planned R − realized R, in R and HKD)
- [ ] Override-quality scoring (justified vs impulsive)
- [ ] Pattern detection (cutting winners early, loss-aversion holds, FOMO, overtrading)
- [ ] Pipeline 3: on-demand trade-inquiry answers (query → RAG+LLM → targeted advice)
- [ ] Skill-growth tracking

### Track D — Pipeline 2 (pure LLM workflow) depth (depends on Track B)
- [ ] Daily scheduled aggregation (RAG + market data + news + research)
- [ ] Ranked reasoned ticker shortlist for manual screening
- [ ] Forward validation + sizing by demonstrated results
- [ ] Human screening UI/flow

### Final — Live Execution & Deployment
- [ ] 富途 MCP live order path + reconciliation + fail-safes
- [ ] Tiered live sizing (tiny → scale by evidence)
- [ ] Benchmark tracking (vs QQQ/ACWI) + passive core allocation
- [ ] Regime monitoring + cross-regime diversification
- [ ] HK market live
- [ ] FX/tax in net P&L; hardening

---

## Decisions Log (key choices, newest first)
- 2026-06-21: Architecture corrected to **four independent pipelines** — 1-1 (quant→LLM validation→strategy), 1-2 (quant→strategy, no LLM), 2 (pure RAG+LLM→strategy), 3 (query→RAG+LLM→advice). Behavioral coaching + guardrails = **cross-cutting layer** (not a pipeline) that all outputs pass through. 1-1 vs 1-2 kept as a built-in A/B test of LLM-overlay value.
- 2026-06-21: Markets = **US + HK** now; A-share deferred.
- 2026-06-21: Core metric = **time-normalized expectancy under risk constraints**; success = beat unified benchmark; keep passive index core.
- 2026-06-21: LLM may originate discretionary trades (P2), validated **forward-only**, sized by track record; veto/shrink only on quant signals.
- 2026-06-21: Phased iteration; **single V4.1 spec** for all phases (no new specs).
- 2026-06-21: Toolchain = venv + Python 3.12 (conda unavailable on host).
