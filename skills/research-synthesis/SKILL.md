---
name: research-synthesis
description: Medical literature synthesis, evidence grading, systematic review methodology, and clinical research interpretation
metadata:
  version: "1.0.0"
  author: "HALO Core"
  tags: ["medical", "research", "evidence-synthesis", "literature-review"]
---

# Research Synthesis Skill

Use this skill when conducting literature reviews, synthesizing medical research, or evaluating clinical evidence.

## When to Use

- Systematic literature searches
- Evidence synthesis for clinical questions
- Quality assessment of studies
- Writing literature reviews
- Translating research to clinical practice

## Research Synthesis Framework

### 1. Question Formulation (PICO)

Structure the clinical question:

- **P**opulation: Who is the patient/population?
- **I**ntervention: What is the exposure/treatment?
- **C**omparison: What is the alternative?
- **O**utcome: What outcomes are important?

### 2. Search Strategy

- Define search terms
- Select databases (PubMed, Cochrane, Embase)
- Include/exclude criteria
- Document the search process

### 3. Study Evaluation

Assess each study for:

- Study design
- Sample size
- Follow-up duration
- Bias risk
- Funding sources

### 4. Evidence Synthesis

Combine findings:

- Forest plots when appropriate
- Heterogeneity assessment
- Sensitivity analyses
- Subgroup analyses

### 5. Grading

Rate evidence quality:

```
GRADE System:
- High: Further research unlikely to change confidence
- Moderate: Further research may change confidence
- Low: Further research likely to change confidence
- Very Low: Any estimate is very uncertain
```

## Evidence Hierarchy

| Level | Quality | Type |
|-------|---------|------|
| 1a | High | Systematic review of RCTs |
| 1b | High | Individual RCT with narrow CI |
| 2a | Moderate | Systematic review of cohort |
| 2b | Moderate | Individual cohort study |
| 3a | Low | Systematic review of case-control |
| 3b | Low | Individual case-control |
| 4 | Very Low | Case series |
| 5 | Very Low | Expert opinion |

## Critical Appraisal

### RCTs (CONSORT)

- Randomization method
- Allocation concealment
- Blinding
- Follow-up
- ITT analysis

### Observational (STROBE)

- Selection bias
- Confounding
- Exposure measurement
- Outcome assessment
- Follow-up adequacy

### Systematic Reviews (PRISMA)

- Search methodology
- Study selection
- Quality assessment
- Synthesis method

## Output Structure

```
Literature Summary:
Clinical Question: [PICO]

Search Results:
- Databases searched
- Studies identified
- Studies included

Evidence Summary:
[Study 1]: Design, n, results, quality
[Study 2]: Design, n, results, quality

Synthesis:
- Overall effect estimate
- Heterogeneity (I²)
- Publication bias

Recommendations:
- Strength of recommendation
- Clinical applicability
- Research gaps
```

## Reporting Standards

- CONSORT: Randomized trials
- STROBE: Observational studies
- PRISMA: Systematic reviews
- MOOSE: Meta-analyses of observational
- CARE: Case reports

## Best Practices

- Pre-register protocols
- Document search strategy
- Include flow diagrams
- Rate evidence quality
- Acknowledge limitations
- Provide clinical context
- Cite properly (PMID, DOI)
