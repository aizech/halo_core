---
name: pharmacology
description: Pharmacotherapy expertise including drug interactions, dosing optimization, medication safety, and therapeutic decision-making
metadata:
  version: "1.0.0"
  author: "HALO Core"
  tags: ["medical", "pharmacology", "drug-interactions", "medication-safety"]
---

# Pharmacology Skill

Use this skill when evaluating medications, assessing drug interactions, or making pharmacotherapy recommendations.

## When to Use

- Reviewing prescription medications
- Assessing drug-drug or drug-disease interactions
- Dosing recommendations (renal/hepatic impairment)
- Therapeutic drug monitoring
- Medication reconciliation
- Alternative therapy suggestions

## Medication Review Framework

### 1. Indication Assessment

- Is each medication appropriately indicated?
- Is there evidence-based support for use?
- Are there more effective alternatives?

### 2. Dosing Evaluation

- Is the dose appropriate for the patient?
- Renal function adjustment (creatinine clearance)
- Hepatic function consideration
- Weight-based dosing where applicable

### 3. Interaction Analysis

Check for:

- **Contraindicated**: Never use together
- **Major**: Significant clinical impact
- **Moderate**: May require monitoring
- **Minor**: Minimal clinical significance

Categories:
- Pharmacodynamic (additive/synergistic/antagonistic)
- Pharmacokinetic (absorption, distribution, metabolism, excretion)

### 4. Adverse Effects

- Common and serious adverse effects
- Monitoring parameters
- Preventive measures

### 5. Patient Factors

Consider:
- Age (geriatric/pediatric)
- Renal/hepatic function
- Pregnancy/lactation
- allergies
- Comorbidities

## Output Structure

```
Medication Review:
[Medication 1]
- Indication: [appropriate?]
- Dose: [appropriate?] - adjustments needed?
- Interactions: [list with severity]
- Monitoring: [recommended parameters]

Recommendations:
1. [Continue/Modify/Discontinue] - rationale
2. [Add alternative] - rationale
3. [Monitoring plan]
```

## Common Interaction Categories

### Cardiovascular

- QT prolongation combinations
- Anticoagulant interactions
- Beta-blocker + CYP interactions

### CNS

- Sedative combinations
- Serotonergic drugs (SSRI, SNRI, triptans)
- Anticholinergic burden

### Metabolic

- Statin interactions (CYP3A4)
- Sulfonylurea interactions
- Metformin contraindications

### Anti-infective

- Antibiotic interactions
- Antifungal/viral interactions
- QT prolongation

## Dosing Resources

Reference standard dosing guides:

- FDA labeling
- Lexicomp/Micromedex
- UpToDate
- Nejm grug information

## Best Practices

- Always verify current guidelines
- Consider patient-specific factors
- Provide alternatives when issues identified
- Include monitoring recommendations
- Add appropriate disclaimers
