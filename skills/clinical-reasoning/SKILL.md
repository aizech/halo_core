---
name: clinical-reasoning
description: Evidence-based clinical reasoning, clinical guideline application, and clinical decision-making methodology
metadata:
  version: "1.0.0"
  author: "HALO Core"
  tags: ["medical", "clinical-reasoning", "evidence-based", "guidelines"]
---

# Clinical Reasoning Skill

Use this skill when applying clinical reasoning, evaluating evidence, or making evidence-based clinical decisions.

## When to Use

- Applying clinical guidelines to patient cases
- Evaluating clinical evidence quality
- Translating research to practice
- Clinical decision-making under uncertainty
- Case-based clinical discussions

## Clinical Reasoning Framework

### 1. Problem Definition

- Identify the clinical question
- Define patient context (demographics, comorbidities)
- Determine urgency and stakes

### 2. Information Synthesis

- Gather relevant clinical findings
- Organize symptoms and signs
- Identify key data points

### 3. Hypothesis Generation

Generate clinical hypotheses considering:

- Pattern recognition (classic presentations)
- Anatomical/physiological reasoning
- Epidemiologic likelihood
- Pre-test probability

### 4. Evidence Evaluation

Assess available evidence:

- Study type (RCT, observational, case series)
- Sample size and power
- Risk of bias
- Applicability to patient

### 5. Decision Integration

Combine:

- Best available evidence
- Clinical expertise
- Patient values and preferences
- Resource considerations

## Evidence Hierarchy

| Level | Type |
|-------|------|
| 1a | Systematic review of RCTs |
| 1b | Individual RCT |
| 2a | Systematic review of cohort studies |
| 2b | Individual cohort study |
| 3a | Systematic review of case-control |
| 3b | Individual case-control |
| 4 | Case series |
| 5 | Expert opinion |

## Clinical Guidelines

Reference established guidelines:

- ACC/AHA (Cardiovascular)
- ESC (European Cardiology)
- IDSA (Infectious Disease)
- ADA (Diabetes)
- WHO guidelines

## Uncertainty Handling

When evidence is limited:

- Acknowledge uncertainty explicitly
- Present options with pros/cons
- Recommend shared decision-making
- Suggest monitoring/ reassessment

## Output Structure

```
Clinical Reasoning:
Problem: [clinical question]

Hypotheses Generated:
1. [Most likely] - supporting evidence
2. [Alternative] - supporting evidence

Evidence Synthesis:
- [Relevant guideline/ study]
- [Applicability to this patient]

Recommendation:
- [Primary recommendation]
- [Strength of recommendation]
- [Alternative options]

Monitoring/Follow-up:
- [Parameters to track]
- [When to reassess]
```

## Best Practices

- Start with clear problem definition
- Consider multiple hypotheses
- Cite evidence quality
- Apply guidelines appropriately
- Individualize to patient context
- Acknowledge limitations
- Plan for reassessment
