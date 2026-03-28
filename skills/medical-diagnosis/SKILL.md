---
name: medical-diagnosis
description: Diagnostic reasoning, differential diagnosis, and clinical decision-making expertise for medical professionals
metadata:
  version: "1.0.0"
  author: "HALO Core"
  tags: ["medical", "diagnosis", "clinical-reasoning", "healthcare"]
---

# Medical Diagnosis Skill

Use this skill when analyzing clinical cases, evaluating symptoms, or providing diagnostic recommendations.

## When to Use

- User presents symptoms, clinical findings, or patient data
- Need to develop differential diagnoses
- Evaluating diagnostic test results
- Providing clinical recommendations
- Case-based clinical reasoning

## Diagnostic Process

### 1. Information Gathering

- Collect relevant patient history
- Identify presenting symptoms and duration
- Review available diagnostic findings
- Note risk factors and comorbidities

### 2. Clinical Analysis

- Identify key clinical findings
- Correlate symptoms with possible conditions
- Consider anatomical and physiological relationships
- Evaluate severity and urgency

### 3. Differential Diagnosis

Generate ranked differential diagnoses considering:

- **Likelihood**: Based on prevalence and presenting features
- **Severity**: Urgent vs. chronic conditions
- **Treatability**: Modifiable vs. static conditions
- **Classic presentations**: Typical vs. atypical features

### 4. Diagnostic Recommendations

Recommend appropriate next steps:

- Additional tests or imaging
- Specialist consultations
- Treatment trials
- Monitoring parameters

## Output Structure

For each diagnosis, provide:

```
Primary Diagnosis:
- Condition: [name]
- Confidence: [High/Medium/Low]
- Rationale: [key supporting evidence]

Differential Diagnoses:
1. [Condition] - likelihood %, supporting findings
2. [Condition] - likelihood %, supporting findings

Recommended Next Steps:
- [Specific recommendation with rationale]
```

## Best Practices

- Always acknowledge uncertainty explicitly
- Cite medical literature when available (PubMed, guidelines)
- Flag urgent findings requiring immediate attention
- Consider patient-specific factors (age, comorbidities, medications)
- Prefer evidence-based recommendations
- Include appropriate medical disclaimers

## Red Flags

Always highlight:

- Signs of sepsis or systemic infection
- Cardiac emergencies (ACS, dissection, PE)
- Neurological emergencies (stroke, meningitis)
- Oncologic emergencies
- Metabolic emergencies (DKA, thyroid storm)

## References

- UpToDate (when available)
- PubMed clinical guidelines
- ACC/AHA, ESC cardiovascular guidelines
- WHO diagnostic criteria
