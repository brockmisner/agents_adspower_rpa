# Business Truth Legibility Auditor

## Honest Assessment

This framework is more than a critique of implementation details: it reframes the product from a crawler diagnostic into business infrastructure.

- **AI Crawler Checker** positions as a technical diagnostic (likely commoditized).
- **Business Truth Legibility Auditor** positions as an ongoing operational system (defensible, retainer-friendly).

## Core Product Question

> Can AI systems find, extract, verify, cite, and act on the key facts about this business better than they can for competitors?

## The Insight That Changes the Product

The central outcome metric is:

**Can AI confidently answer real customer questions from what it found?**

This converts technical crawl findings into business outcomes clients immediately understand.

## Evidence-Backed Answer Quality

A passing answer test must include a reproducible evidence chain.

```json
{
  "question": "How much does drain cleaning cost?",
  "answer": "$150-$300",
  "status": "answered",
  "confidence": 0.94,
  "evidence": {
    "url": "/services/drain-cleaning",
    "selector": "section.quick-facts table",
    "raw_text": "Starting price: $150. Common range: $150-$300"
  },
  "warnings": []
}
```

Without evidence, evaluators can hallucinate pass conditions. With evidence, audits are defensible and repeatable.

## Architecture: Business Facts Registry

The registry acts as canonical truth and powers every downstream check.

```text
                    ┌─────────────────┐
                    │  Business Facts │
                    │    Registry     │
                    │ canonical truth │
                    └────────┬────────┘
                             │
Fetch → Extract → Compare → Answer Test → Score → Fix
                             │
                    HTML / Schema / GBP /
                    Apple / Bing / llms.txt
```

Value shift:
- Without registry: “Page says X.”
- With registry: “Page says X, canonical says Y, GBP says Z — contradiction lowers AI confidence.”

## Contradiction Severity Levels

- **Critical**: Phone mismatch, pricing contradiction, address mismatch, hours contradiction.
  - Action: Fix immediately.
- **Medium**: Missing diagnostic fee, stale review count, service naming mismatch.
  - Action: Fix this sprint.
- **Low**: Missing social profile, minor wording drift.
  - Action: Fix opportunistically.

## Three-Layer Content Analysis

1. **Raw HTML** — what many AI crawlers ingest.
2. **Rendered DOM** — what JS-executing crawlers can see.
3. **Extracted Text** — what retrieval pipelines actually consume.

Facts can appear in one layer and disappear in another. All three are required to diagnose answer failures.

## Vertical-Specific Question Banks

Generic prompts are insufficient. Each vertical requires domain-specific intent coverage.

- **Plumber**: “Do they charge a diagnostic fee?”
- **Dentist**: “Do they accept Delta Dental?”
- **Attorney**: “Do they offer free consultations?”
- **Med spa**: “Who performs treatments?”

## Answer Extractability vs Agent Actionability

Two independent scores are required:

- **Answer Extractability**: Can AI find and cite key facts?
- **Agent Actionability**: Can AI complete tasks (book, quote, availability checks)?

This future-proofs the platform for agent-driven workflows.

## Delivery Phases

### Phase 1 — Ship & Validate
- Bot taxonomy + robots checker
- Field extractor + diff table
- Basic answerability test
- Prioritized fix list

**Goal:** Acquire paying clients, validate demand.

### Phase 2 — Differentiate
- Evidence-backed answer quality
- WAF/challenge detection
- Log verification (starting with high-adoption connectors)
- Vertical question banks

**Goal:** Build defensibility.

### Phase 3 — Become Infrastructure
- Full Business Facts Registry
- Multi-surface consistency checks
- Competitor benchmarking
- Auto-generated fix patches

**Goal:** Create hard-to-replicate data moat.

## Practical Adjustment: Log Verification

Recommendation:
- **Phase 1**: Simulation mode only (clearly labeled).
- **Phase 2**: Cloudflare log connector first.
- **Phase 3**: Full IP/log verification suite.

This avoids delaying launch with integration-heavy requirements.

## Missing but High-Impact Additions

### 1) Competitive Benchmarking

The strongest report format:

“Your score is 61/100; top 3 competitors average 74/100. Here’s what they expose that you do not.”

### 2) Call Script Integration

Reuse extracted facts to generate front-desk scripts for AI-caller interactions.

One data pipeline, two business outcomes.

## Bottom Line

Phase 1 should be built now. The market gap is immediate, and the architecture creates a path from tool to infrastructure.
