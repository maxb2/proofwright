# LLM Wiki Deterministic Tooling — Coding Session Handoff

## Purpose of this document

This is a build brief for a coding session. The goal is to build **reusable, mostly-deterministic tooling** for a research-synthesis LLM wiki (the "Karpathy LLM Wiki" pattern) running in a work setting. It captures (1) the pattern and its landscape, (2) what works and what fails, (3) the deterministic-vs-LLM boundary that should drive the architecture, and (4) a concrete recommendation for packaging.

**Existing setup (assumed context):** a research-synthesis knowledge base built on the vanilla pattern, already grading sources by reliability and enforcing citations on claims. Those two disciplines are load-bearing below — several proposed deterministic checks depend on them.

> All factual claims are cited with bracketed reference numbers `[n]` mapping to the **References** section at the end.

---

## 1. The pattern in one screen

The LLM Wiki is a knowledge-base **pattern**, not a tool — Karpathy published it as an abstract "idea file" gist meant to be pasted into a coding agent [1][14]. It has three layers and three operations [10][13]:

- **Layers:** `raw/` (immutable sources), `wiki/` (LLM-owned markdown pages), and a schema file such as `CLAUDE.md` / `AGENTS.md` (conventions the agent follows) [10][13].
- **Operations:** **ingest** (read a source, extract entities/concepts, integrate into pages, cross-reference), **query** (answer from the wiki, not the raw sources), **lint** (periodic health check) [10][12].

The mental model is a **compiler**: `raw/` is source code, the LLM is the compiler, `wiki/` is the executable output, lint is the test suite, and queries are runtime [13]. The core value claim vs. RAG: RAG re-retrieves and re-synthesizes on every query and never accumulates, whereas the wiki is compiled once and kept current, so knowledge compounds and cross-references already exist at query time [1][9].

Note on provenance: Karpathy joined Anthropic's pre-training team in mid-2026, but the pattern stands independently of him [12].

---

## 2. Landscape — what people are building

Within ~2 weeks of the gist, dozens of implementations appeared [5]. They cluster into three forms:

- **Drop-in agent skills.** The pattern packaged as Claude Code / Codex / Cursor slash-command skills. Notable: `SamurAIGPT/llm-wiki-agent` (multi-platform; detects contradictions at ingest rather than at a later lint pass) and `Astro-Han/karpathy-llm-wiki` (Agent Skills standard, citations + linting) [5][6].
- **Obsidian-centric builds.** Wiring into Obsidian for the graph view and local-first markdown. A polished community plugin (`karpathywiki`) does entity/concept page generation, zero-embedding graph retrieval, and contradiction flags; `AgriciDaniel/claude-obsidian` adds a "hot cache" session-resume layer [5][7].
- **Fully automated "second-brain" pipelines.** Claude Code lifecycle hooks (`PreCompact`, `SessionEnd`) plus sync, so sessions are harvested into the vault automatically [6].

**Version lineage (useful for framing decisions):**
- **v1** — Karpathy gist: append-only ingest, manual lint, human-readable notes [3].
- **v2** — rohitg00: adds confidence scoring, supersession of stale claims, contradiction detection, and hybrid retrieval [2][3].
- **v3** — Ghelbur (`obsidian-second-brain`): adds scheduled agents, automatic synthesis, and AI-first note structure [3][4].

---

## 3. Success modes (refinements that work)

- **Contradiction *resolution*, not just flagging.** v1 only surfaces contradictions; the improvement is having the model propose which claim wins by source recency, source authority, and confidence, archiving the loser with a reason [2][3].
- **Self-healing lint.** Lint should auto-fix what it safely can (link orphans, mark stale claims, repair cross-references) rather than only advising [2].
- **Quality scoring on write.** Score each generated page (structured? cites sources? consistent?); flag or rewrite anything below threshold [2].
- **Rewrite-not-append ingest.** Append-only pages go stale invisibly; rewriting forces each page to carry the current best answer at the top, with the prior version preserved as a dated entry below [3].
- **Unsolicited cross-source synthesis.** The high-value payoff for research KBs: the system surfaces recurring unnamed themes and cross-source connections without being asked. Field data point: applying the pattern to three business books (~155K words) at chapter granularity produced ~210 concept pages and ~4,600 cross-references with genuine cross-book synthesis [13].
- **Session context resume ("hot cache").** End-of-session summary so the next session resumes with full context [5].
- **AI-first notes (contrarian; conditional).** Notes optimized for LLM retrieval rather than human reading — machine-readable frontmatter, a `## For future Claude` triage preamble, mandatory wikilinks, per-claim recency markers, verbatim source URLs, confidence levels, self-contained context [3]. Speedup mechanism is **triage and reduced reconstruction**, not raw token speed: frontmatter + preamble let the agent decide in ~6 lines whether to read a page's body, and explicit recency/confidence/source markers save the model from inferring (and hedging) [3]. **Caveat:** the author concedes these pages are harder for humans to scan — only adopt fully where the LLM does essentially all the reading [3].

---

## 4. Failure modes (design against these)

- **Hallucination baking / compounding.** Because ingest summarizes and compresses, an error can be written in as a "fact" and propagate across linked pages — turning random mistakes into *organized, persistent* mistakes that look trustworthy because they are well-formatted. RAG is more forgiving here because it re-reads the source each query [8][14].
- **Loss of provenance.** Answers come from a mix of generated pages, summaries, and links, making "where did this come from?" harder to answer than in RAG [8].
- **False coherence.** Lint that only checks internal consistency will pass a wiki whose pages agree around a belief that is simply wrong — coherence without truth-anchoring is only the *appearance* of health [10].
- **Cascade / consistency cost.** One update can require edits across many linked pages; keeping them consistent is hard, and this is what makes people abandon wikis [11].
- **Stale pages from routing misses.** If a page's schema description is vague, the ingest router may not recognize a new source as relevant, leaving the page stale; only regular lint / periodic full re-ingest catches it [9].
- **Append-only rot at scale.** Works for the first ~50–100 sources; past that, stale claims and unresolved contradictions accumulate invisibly [3].
- **Not for real-time data.** The pattern assumes deliberate human curation; it adds friction for streaming sources (feeds, prices, news) [9].

**Two cross-cutting mitigations that keep recurring:**
- The **lint step is load-bearing** — most "this is a bad idea" critiques are really critiques of skipping disciplined lint and spot-checking pages against raw sources [8][14].
- **Automate reversibly, not "always."** An auto-synthesis command silently wrote garbage into its author's vault on first run; the lesson was to log every automated change to a daily diff note and hold a 24-hour delay before it becomes permanent [3].

---

## 5. The deterministic / LLM-only boundary (core of the build)

Split operations by whether correctness is **structural** (one right answer, defined without reference to subject matter) or **semantic** (requires judgment). Structural work runs as code; semantic work stays with the LLM. This is not only cheaper but more robust: controlled studies of deterministic vs. LLM-controlled orchestration in structured workflows found up to **3.5× lower token use**, better worst-case robustness, and lower run-to-run variance, with no quality loss [18]. The governing principle is "blueprint first, model second": a deterministic engine owns the workflow path and invokes the LLM only for bounded sub-tasks [19].

### 5a. Fully deterministic — NO LLM
- **Structural lint:** orphan pages, missing pages (schema slug with no file), broken `[[wikilinks]]`, stale index/embedding entries, missing source provenance [9]. Ship as a zero-LLM pre-flight integrity check [17].
- **Index / TOC regeneration** [9].
- **Frontmatter validation** (types, required keys, allowed tag/grade vocabularies).
- **Format normalization.**
- **Source preprocessing:** PDF → markdown before ingest (e.g., `marker`, `pypdf`) [20].
- **Versioning / rollback:** git for diffs and reverting bad changes [20].
- **Retrieval candidate generation:** BM25 (exact terms) and graph traversal (structural links) [2].
- **[Depends on your citation discipline] Citation/provenance integrity:** assert every claim line has a citation and every citation resolves to a file in `raw/`; flag unbacked claims. This is the deterministic structural defense against hallucination-baking — catch it *before* it propagates, rather than hoping an LLM lint pass notices [8][9].
- **[Depends on your grading discipline] Source-grade consistency:** every referenced source has a grade, grades come from the fixed vocabulary, and pages surface the grade relied on.
- **Freshness triage:** scan dates/recency markers, emit a candidate list of stale pages (code lists candidates; it does not judge staleness of meaning).

### 5b. Two-pass hybrid — deterministic first, LLM only on the residue
- **Knowledge graph:** pass 1 extracts explicit wikilinks deterministically; pass 2 uses the LLM for semantic/implied links. Graph-aware lint then flags phantom hubs, hub stubs, fragile bridges [17].
- **Retrieval:** deterministic BM25 + vector + graph streams fused with reciprocal rank fusion for candidates; LLM only reranks/synthesizes the top slice. Do **not** rely on `index.md` as the LLM's primary search past ~100 pages [2].

### 5c. LLM-only — irreducibly semantic
- Synthesis across sources; summarization at ingest; **meaning-level** contradiction detection; supersession decisions (which conflicting claim wins) [2][3].

### 5d. Reference points on the spectrum
- **Pure-Python compiler** (`Emmimal/wiki-compiler`): zero LLM calls, zero external APIs — proves how much lint/link/index work is deterministic, but deliberately drops synthesis. Its own author frames LLMs as the wrong tool for the *mechanical* work, not for the wiki as a whole [15][16].
- **Hermes skill** (`Robs87/llm-wiki`): explicit zero-LLM health check + two-pass graph — a concrete model of the hybrid split [17].
- **Linters-as-guardrails**: encoding invariants as lint rules so agents self-heal against them is an established agent-native technique worth mirroring [21].

> **For a research-synthesis KB specifically:** do NOT go pure-compiler — synthesis is the payoff. Target the hybrid: deterministic tooling for everything with a single correct answer; LLM reserved for synthesis and judgment. The deterministic layer is also the part safe to run unattended without the diff-log/24h-delay guardrail [3][15].

---

## 6. Packaging vs. vendoring — does this generalize?

**Recommendation: build a reusable package for the deterministic layer; ship the semantic layer separately as a template/skill.**

**Why it generalizes:** the determinism split *is* the package/vendor seam. Deterministic operations are content-agnostic by construction — a broken link, an orphan, an unbacked claim fail identically whether the domain is immunology or case law. What actually varies across wikis is **data, not logic**: schema/page templates, tag taxonomy, grade vocabulary, thresholds, domain page types, and the semantic-layer prompts. Data variance is a reason to **parameterize**, not to fork.

**Architecture:** library-not-framework. Package the invariant functions (markdown parsing, link graph, orphan/broken detection, index regen, git helpers, BM25/graph retrieval primitives, citation-integrity and grade-consistency checks). Inject per-wiki config (a config object). Keep schema, prompts, and `CLAUDE.md` living with each wiki, never inside the package.

**Custom checks:** expose a plugin/hook so a wiki can register its own checks. A truly general invariant (every claim needs a source) belongs in the package core; a wiki-specific rule registers via the hook. The hook boundary is the honest test of generality — anything expressible as a registered check generalizes; anything that won't fit the hook shape is genuinely bespoke.

**When vendoring is actually correct:** (1) only one wiki exists today (extracting a package now risks baking this wiki's accidental specifics into the interface); (2) the tooling is small enough (a few hundred lines) that release/versioning overhead exceeds the copy cost; (3) two wikis diverge in the *logic* of an operation, not just config (rare for structural ops).

**The decisive argument against sloppy vendoring:** drift. Copying a correctness check (e.g., the citation validator) into N wikis means N bug-fixes and silent divergence — the wrong property for a check run unattended on a work KB. A versioned package with per-wiki pinning gives both the isolation vendoring is wanted for and controlled propagation.

**Semantic layer distribution:** synthesis conventions, ingest prompts, and schema shape also generalize, but as a shared **template / SKILL.md**, not as Python. The community has already sorted this way — mechanical tooling ships as repos/packages; the pattern ships as copy-paste idea files and skill conventions [1][6]. Forcing prompts/schema into the Python package is the mistake that turns a clean library into an unadoptable framework.

**Practical path if only one wiki exists now:** inline the tooling but write it *as if* it were already a package — wiki-specific bits behind a config object from day one, no subject-matter knowledge in the functions. That keeps later extraction to an afternoon, and you pay packaging overhead only once a second real wiki reveals which parts of the interface were accidental.

---

## 7. Recommended build order for the coding session

1. **Deterministic lint core (no LLM):** structural checks (orphans, missing pages, broken links, stale index, missing provenance) + a machine-readable report. Model it on the zero-LLM pre-flight health check [17].
2. **Citation-integrity + grade-consistency checks** (leverages existing disciplines; primary hallucination-propagation defense) [8][9].
3. **Config object + plugin/hook interface** for per-wiki vocabularies, templates, thresholds, and custom checks.
4. **Index regeneration + graph pass 1** (deterministic wikilink extraction) [17].
5. **Retrieval primitives:** BM25 + graph candidate generation, RRF fusion, LLM rerank as a bounded call [2].
6. **git-based reversibility harness:** every automated write logs to a daily diff note; enforce a hold/confirm before permanence for any auto-rewrite or reconciliation [3].
7. **LLM steps as callable tools inside deterministic pipelines** (synthesis, summarization, meaning-level contradiction, supersession) — never as the workflow controller [19].

**Note on AI-first notes for this KB:** if teammates read wiki pages directly, adopt the parts that help both audiences (frontmatter, confidence, recency markers) but keep human-readable prose bodies; only go full AI-first if the LLM does essentially all the reading [3].

---

## References

1. Karpathy, "LLM Wiki" (original gist). https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
2. rohitg00, "LLM Wiki v2." https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2
3. Ghelbur, E. "I rebuilt Karpathy's LLM Wiki gist: what's missing" (The AI Operator). https://theaioperator.io/p/i-rebuilt-karpathys-llm-wiki-heres
4. eugeniughelbur/obsidian-second-brain. https://github.com/eugeniughelbur/obsidian-second-brain
5. denser.ai, "LLM Wiki: Karpathy's Idea for AI Knowledge Bases" (ranked implementations). https://denser.ai/blog/llm-wiki-karpathy-knowledge-base/
6. Astro-Han/karpathy-llm-wiki. https://github.com/Astro-Han/karpathy-llm-wiki
7. Obsidian community plugin, "Karpathy LLM Wiki" (karpathywiki). https://community.obsidian.md/plugins/karpathywiki
8. Gupta, M. "Andrej Karpathy's LLM Wiki is a Bad Idea." https://medium.com/data-science-in-your-pocket/andrej-karpathys-llm-wiki-is-a-bad-idea-8c7e8953c618
9. Nayak, P. "Beyond RAG: How Andrej Karpathy's LLM Wiki Pattern Builds Knowledge That Actually Compounds" (Level Up Coding). https://levelup.gitconnected.com/beyond-rag-how-andrej-karpathys-llm-wiki-pattern-builds-knowledge-that-actually-compounds-31a08528665e
10. "The Wiki That Thinks: Ingest, Lint, and the Question of What Knowledge Is For" (Extended Brain). https://extendedbrain.substack.com/p/the-wiki-that-thinks-ingest-lint
11. Genc, M. "Your LLM Has Been Forgetting Everything — Karpathy's Wiki Pattern Is the Fix." https://medium.com/@mustafa.gencc94/your-llm-has-been-forgetting-everything-karpathys-wiki-pattern-is-the-fix-6931ad90017b
12. AI Builder Club, "Karpathy's LLM Wiki: A Knowledge Base That Compounds." https://www.aibuilderclub.com/blog/karpathy-llm-wiki
13. Starmorph, "How to Build Karpathy's LLM Wiki: The Complete Guide." https://blog.starmorph.com/blog/karpathy-llm-wiki-knowledge-base-guide
14. Joshi, U. "Andrej Karpathy's LLM Wiki: Create your own knowledge base." https://medium.com/@urvvil08/andrej-karpathys-llm-wiki-create-your-own-knowledge-base-8779014accd5
15. Emmimal, "LLM Wikis Are Over-Engineered — I Replaced Mine With a Pure Python Compiler" (Towards Data Science). https://towardsdatascience.com/llm-wikis-are-over-engineered-i-replaced-mine-with-a-pure-python-compiler/
16. Emmimal/wiki-compiler. https://github.com/Emmimal/wiki-compiler
17. Robs87/llm-wiki (Hermes Agent skill, v2.1.0). https://github.com/Robs87/llm-wiki
18. Lwin, N.O. & Kumar, R. "Deterministic vs. LLM-Controlled Orchestration for COBOL-to-Python Modernization" (arXiv). https://arxiv.org/pdf/2605.09894
19. "Blueprint First, Model Second: A Framework for Deterministic LLM Workflow" (arXiv). https://arxiv.org/pdf/2508.02721
20. Tahir, "What is LLM Wiki Pattern? Persistent Knowledge with LLM Wikis." https://medium.com/@tahirbalarabe2/what-is-llm-wiki-pattern-persistent-knowledge-with-llm-wikis-3227f561abc1
21. Factory.ai, "Using Linters to Direct Agents." https://factory.ai/news/using-linters-to-direct-agents
22. Penfield Labs, "What Karpathy's LLM Wiki Is Missing (and How to Fix It)" (dev.to). https://dev.to/penfieldlabs/what-karpathys-llm-wiki-is-missing-and-how-to-fix-it-1988

---

*Citations point to community write-ups, repositories, and two arXiv papers gathered mid-2026. Repos and blog posts evolve; verify current APIs and star counts before relying on specifics. Reference [22] is included as further reading on typed-link extensions, referenced but not quoted above.*
