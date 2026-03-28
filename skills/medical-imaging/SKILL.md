---
name: medical-imaging
description: Medical imaging interpretation including X-ray, CT, MRI, ultrasound, and DICOM analysis for radiology diagnostics
metadata:
  version: "1.0.0"
  author: "HALO Core"
  tags: ["medical", "imaging", "radiology", "DICOM", "diagnostics"]
---

# Medical Imaging Skill

Use this skill when analyzing medical images, DICOM files, or imaging findings for clinical diagnosis.

## When to Use

- User provides medical images (X-ray, CT, MRI, ultrasound)
- Analyzing DICOM files for diagnostic purposes
- Interpreting imaging reports
- Comparing current and prior studies
- Providing follow-up imaging recommendations

## Imaging Modalities

### X-Ray (Radiography)

- Chest X-ray: lungs, heart, mediastinum, bones
- Abdominal X-ray: bowel patterns, free air, calcifications
- Extremity X-ray: fractures, dislocations, joints

### CT (Computed Tomography)

- Head CT: intracranial hemorrhage, stroke, masses
- Chest CT: pulmonary embolism, nodules, interstitial disease
- Abdominal CT: organ injury, masses, appendicitis
- CT Angiography: vessel stenosis, aneurysm, dissection

### MRI (Magnetic Resonance Imaging)

- Brain MRI: demyelination, tumors, vascular
- Spine MRI: disc herniation, stenosis, cord compression
- Joint MRI: ligament, meniscus, tendon injury
- Body MRI: organ masses, liver, pancreas

### Ultrasound

- Abdominal: gallbladder, liver, kidney, pancreas
- Vascular: DVT, aneurysm, stenosis
- Cardiac: EF, valves, pericardium
- Obstetric: fetal assessment

## Analysis Framework

### 1. Technical Assessment

- Modality and technique used
- Anatomical region visualized
- Image quality (contrast, motion, artifacts)
- Comparison with prior studies

### 2. Systematic Review

Review anatomically:

- Location and extent of findings
- Size, shape, density/signal characteristics
- Margins, borders, infiltration
- Associated findings

### 3. Clinical Interpretation

Structure findings:

```
Findings:
- [Primary finding with measurements]
- [Secondary findings]
- [Incidental findings]

Impression:
1. [Most likely diagnosis] - confidence %
2. [Differential diagnoses] - likelihood

Critical Findings:
- [Urgent findings requiring immediate action]
```

## Standardized Reporting

Use appropriate scoring systems:

- **BI-RADS**: Breast imaging (0-6)
- **LI-RADS**: Liver imaging
- **PI-RADS**: Prostate imaging
- **TI-RADS**: Thyroid imaging
- **Lung-RADS**: Lung cancer screening

## Critical Findings

Always flag:

- Pneumothorax
- Intracranial hemorrhage
- Pulmonary embolism
- Bowel perforation
- Appendicitis with complications
- Fractures with neurovascular compromise

## DICOM Handling

When working with DICOM files:

- Extract metadata (patient, study date, series)
- Apply appropriate window/level settings
- Measure densities and distances
- Compare with prior studies when available

## Best Practices

- Provide both technical and clinical language
- Include differential diagnoses
- Suggest follow-up imaging when appropriate
- Add appropriate disclaimers
- Reference relevant literature for rare findings
