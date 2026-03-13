# DICOM Tools

DICOM Tools provides medical imaging anonymization for privacy-compliant handling of DICOM files.

---

## What It Does

- **Anonymize DICOM files** — Remove Protected Health Information (PHI)
- **Regenerate UIDs** — Create new unique identifiers for studies, series, and instances
- **Remove private tags** — Strip manufacturer-specific metadata
- **Export mapping** — Save anonymization mapping as CSV for reference

---

## Why It Matters

Medical imaging files (DICOM) contain sensitive patient information. Sharing these files for:

- Research collaboration
- Teaching and presentations
- Second opinions
- Publications

...requires removing identifiable information to comply with HIPAA, GDPR, and other privacy regulations.

---

## Accessing DICOM Tools

1. Open HALO Core
2. Navigate to **DICOM Tools** in the sidebar
3. The page displays anonymization options

---

## Anonymization Options

### What Gets Anonymized

By default, HIPAA Safe Harbor identifiers are removed:

| Category | Tags Anonymized |
|----------|-----------------|
| **Patient Data** | Name, ID, Birth Date, Sex, Age, Address, Weight, Phone, Other IDs |
| **Institution Data** | Name, Address, Referring Physician |
| **Physician Data** | Performing Physician, Operators |
| **Study Data** | Study ID, Accession Number, Dates, Times |
| **Series Data** | Series Date/Time, Acquisition Date/Time |

### UID Regeneration

When enabled (default), new UIDs are generated for:

- Study Instance UID
- Series Instance UID
- SOP Instance UID
- Frame of Reference UID

This ensures anonymized files don't link back to original studies.

### Private Tags

Private tags are manufacturer-specific and may contain identifying information. They are removed by default.

---

## Using DICOM Tools

### Step 1: Upload Files

1. Click **Dateien hochladen**
2. Select DICOM files (`.dcm`, `.dicom`, or files without extension)
3. Multiple files can be uploaded at once

### Step 2: Configure Options

Select what to anonymize:

- **UIDs neu generieren** — Regenerate unique identifiers (recommended)
- **Private Tags entfernen** — Remove manufacturer-specific tags (recommended)
- **Patientendaten** — Patient name, ID, birth date, etc.
- **Institutionsdaten** — Hospital/clinic information
- **Studiendaten** — Study ID, accession number
- **Datumsangaben** — All date/time fields

### Step 3: Anonymize

1. Click **Anonymisieren**
2. Wait for processing to complete
3. Review results in the output section

### Step 4: Download

1. Download anonymized files as ZIP
2. Optionally download the anonymization mapping CSV

---

## Expected Results

After anonymization:

- All selected tags are cleared or replaced with placeholder values
- New UIDs are generated (if enabled)
- Private tags are removed (if enabled)
- Files are functionally identical for clinical review
- Files can be shared without exposing patient identity

---

## Anonymization Mapping

The mapping CSV contains:

| Column | Description |
|--------|-------------|
| Original Filename | Original file name |
| Anonymized Filename | New file name |
| Original Patient ID | Original patient identifier |
| Anonymized ID | New anonymized identifier |
| Tags Anonymized | List of cleared tags |
| UIDs Regenerated | List of regenerated UIDs |

Keep this mapping secure — it links anonymized files to original patients.

---

## Auto-Anonymization on Upload

When enabled in configuration, DICOM files uploaded to Sources are automatically anonymized.

### Enable in `.env`:

```bash
DICOM_ANONYMIZE_ON_UPLOAD=true
```

### Behavior

- Files are anonymized before being added to Sources
- Original files are not stored
- Mapping is saved for reference

---

## Troubleshooting

### "File not recognized as DICOM"

Possible causes:

- File is not a valid DICOM file
- File is corrupted
- Unsupported DICOM format

Try this:

1. Verify file is a valid DICOM file
2. Try opening in a DICOM viewer first
3. Check file integrity

### "Anonymization fails"

Possible causes:

- File is write-protected
- Missing dependencies
- Invalid DICOM structure

Try this:

1. Check file permissions
2. Verify `pydicom` is installed
3. Try a different DICOM file

### "Download fails"

Possible causes:

- Browser blocking download
- Large file size
- Disk space issue

Try this:

1. Enable pop-ups/downloads for the site
2. Process fewer files at once
3. Check available disk space

---

## Best Practices

### Before Anonymizing

- Verify files are correct DICOM format
- Note any critical metadata that may be needed later
- Consider which tags are necessary for your use case

### After Anonymizing

- Verify anonymized files open correctly
- Check that clinical utility is preserved
- Securely store mapping file if patient linkage is needed
- Delete original files if no longer needed

### For Research

- Document anonymization process for IRB compliance
- Store mapping separately from anonymized files
- Consider de-identification beyond HIPAA Safe Harbor if needed

---

## Next Steps

- [Sources](sources.md) — Upload anonymized files to your library
- [DICOM Configuration](../admin/dicom-configuration.md) — Admin setup
