# Scientific-Editor-AI-Protocol


**Author:** Rigjita Baldanova, Ph.D.  
**Domain:** AI-Assisted Scientific Documentation | Clinical & Biotech Documentation Optimization | Bilingual Scientific Editing (EN/RU)

---

## Executive Summary
In regulated clinical laboratories (FDA, CLIA, CAP, GLP/GMP) and academic research environments, documentation accuracy is non-negotiable. Standard LLM prompting often introduces subtle factual drift, unverified claims, or regulatory non-compliance.

This repository outlines a structured, multi-stage **Prompt Engineering & Audit Protocol** designed to accelerate scientific writing, diagnostic test directory creation, technical reports, and manuscript preparation—reducing documentation turnaround time while enforcing a strict **Hallucination-Mitigation Policy**.

---

## 1. Core Architecture: The 4-Stage Verification Pipeline


```text
[Stage 1: Source Grounding] ---> [Stage 2: Structural Audit] ---> [Stage 3: Fact & Metric Verification] ---> [Stage 4: Regulatory & Venue Polish]

Stage 1: Strict Source Grounding (Anti-Hallucination Guardrail)
 * Constraint: The AI agent is strictly prohibited from extrapolating numerical data, p-values, Z-factors, assay sensitivity metrics, or citations not explicitly present in the primary laboratory notebook (ELN/LIMS) or source dataset.
 * Mechanism: Any missing experimental parameter triggers a [DATA_REQUIRED] flag rather than speculative text generation.
Stage 2: Methodological & Statistical Coherence Audit
 * Evaluates alignment between the Materials & Methods section and reported Results:
   * Verifies that every assay mentioned in Results (e.g., ELISA, Western Blot, FRET-HTS, PCR, HPLC, Fluorescence Microscopy) has corresponding reagent, instrument calibration, and control parameters defined in Methods.
   * Checks statistical reporting consistency (e.g., SD vs. SEM, replicate count n, GraphPad Prism / STATISTICA model specifications).
Stage 3: Clinical & Laboratory Compliance Check (CLIA / CAP / GLP)
 * Designed for clinical reference laboratories and diagnostic product rollouts:
   * Pre-Analytical Clarity: Audits specimen collection instructions, transport constraints, and test utilization guidance for clinical test directories.
   * Project & Validation Documentation: Standardizes structure for analytical method validation summaries, turnaround time (TAT) workflows, and cross-departmental scientific communications.
Stage 4: Bilingual Academic & Executive Calibration (EN / RU)
 * Eliminates machine-translation artifacts ("AI-ese") in cross-border scientific collaborations.
 * Enforces precise domain terminology across English and Russian scientific standards (peer-reviewed journals, NIH-NCATS progress reports, and international environmental biotechnology specifications).
```
2. Production Prompt Template: Hallucination-Mitigation Scientific Auditor
Below is the core system prompt template used to audit technical reports and research manuscripts:
### ROLE
You are a Senior Scientific Auditor and Lead Editor specializing in Microbiology, Molecular Biology, Clinical Diagnostics, and Aquatic & Environmental Sciences.

### HARD CONSTRAINTS (HALLUCINATION-MITIGATION PROTOCOL)
1. NEVER invent, extrapolate, or modify experimental numbers, concentrations, p-values, sample sizes, or literature citations.
2. Flag any claim lacking direct evidence in the provided source text with: `[UNVERIFIED CLAIM: Requires Source Data]`.
3. Cross-check all assay descriptions (PCR, ELISA, FRET, MIC50, HPLC, Microscopy) for internal consistency between Methods and Results.

### AUDIT RUBRIC (Score 1-10 per category)
1. Scientific & Mechanistic Rigor: Are biological pathways and ecological/assay principles stated accurately?
2. Methodological Reproducibility: Are controls (positive, negative, sterility), reagents, and statistical tests clearly defined?
3. Regulatory & Data Integrity (GLP/CLIA): Does the terminology adhere to Good Documentation Practices?
4. Clarity & Conciseness: Remove redundant prose while preserving technical precision.

### OUTPUT FORMAT
- Section 1: Quantitative Audit Score & Critical Red Flags
- Section 2: Line-by-Line Fact & Consistency Verification Table
- Section 3: Polished, Publication-Ready Text

3. Proven Impact in Research & Clinical Operations
 * Faster Documentation Turnaround: Deployed during antibacterial drug discovery research (Rutgers University) to streamline data synthesis and NIH-NCATS collaborator reporting.
 * Cross-Functional Clinical Alignment: Applied principles derived from managing 150+ clinical diagnostic assay launches and 200+ physician/biotech accounts in CLIA/CAP-regulated reference laboratories.
## 4. Data Governance for Clinical & Regulated Inputs

This protocol assumes it runs **only** on data the operator is authorized to process. Before any document enters the pipeline:

- **De-identification first.** No protected health information (PHI), patient identifiers, or site-identifying details enter the model context. De-identify per HIPAA Safe Harbor / Expert Determination (or the applicable local regime) *before* Stage 1.
- **No training on inputs.** Use enterprise / zero-retention API instances only — endpoints contractually excluded from model training. Consumer chatbots are not acceptable for regulated or unpublished material.
- **Unpublished data & IP.** Manuscripts, ELN/LIMS extracts, and assay validation data are processed only with the data owner's written authorization; employer and collaborator agreements govern what may leave the institutional boundary.
- **Audit trail.** Every run logs: source document hash, model ID and version, the prompt template version, and the [DATA_REQUIRED] / [UNVERIFIED CLAIM] flags raised. The log — not the chat history — is the record of what was checked.

## 5. Worked Example (illustrative excerpt)

*The passage below is a synthetic illustration of the audit format, not a real document.*

**Input (Methods excerpt, flawed):**
> "MICs were determined by broth microdilution. Briefly, bacteria were grown overnight and diluted to an appropriate density. Compound X was tested at various concentrations and growth inhibition was measured at OD600."

**Audit output:**
- **Score: 4/10.** Critical red flags: no medium specified (CAMHB required per CLSI M07); "appropriate density" is not a specification — final inoculum must be ~5×10⁵ CFU/mL per well; endpoint defined as OD600 reduction instead of absence of visible growth; no controls mentioned.
- **[UNVERIFIED CLAIM: Requires Source Data]** — "various concentrations" (exact range not stated); "measured at OD600" (no wavelength/time given).
- **Polished rewrite:** "MICs were determined by broth microdilution per CLSI M07. E. coli ATCC 25922 was grown overnight on non-selective agar; colonies were suspended to 0.5 McFarland (~1.5×10⁸ CFU/mL) and diluted 1:100 in cation-adjusted Mueller-Hinton broth (CAMHB). Compound X was serially diluted 2-fold in CAMHB (final range [DATA_REQUIRED] µg/mL); wells were inoculated to a final density of ~5×10⁵ CFU/mL, incubated at 35 ± 2 °C for 16–20 h, and read as the lowest concentration with no visible growth. Sterility (medium-only) and growth (compound-free) controls were included on each plate."

Author
Rigjita Baldanova, Ph.D.
Ph.D. Biologist & Scientific Project Manager | AI Systems Evaluator
LinkedIn | b2b@genesis-agency.com
