# LLM Wiki — semantic layer (skill stub)

Proofwright owns the **deterministic** layer (structure, citations, grades, index, graph).
This file is where the **semantic** layer lives — the irreducibly LLM work. It ships as
markdown conventions, deliberately *not* as Python, so it can be pasted into a coding
agent and tuned per wiki.

## Operations for the agent

- **Ingest.** Read a source in `raw/`, extract entities/concepts, and *rewrite* (not
  append) the affected pages so the current best answer sits at the top, prior version
  preserved as a dated entry below. Add cross-references. Cite every claim.
- **Query.** Answer from `wiki/`, not from `raw/`.
- **Reconcile.** When two claims conflict, propose which wins by source recency, source
  grade, and confidence; archive the loser with a reason. (Meaning-level — not Proofwright.)

## Guardrail

Run `proofwright check` after every ingest. It is the zero-LLM pre-flight that catches
broken structure, unbacked claims, and out-of-vocabulary grades *before* they propagate.
Never let an automated rewrite become permanent without logging the diff and a review hold
(deferred milestone 6).
