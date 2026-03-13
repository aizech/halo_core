# Sources Library

The Sources library is where you import, manage, select, and remove content used by chat and studio generation.

---

## What It Does

- Import files from your computer
- Fetch content from connected systems (connectors)
- Select which sources the AI can use
- Organize, rename, download, and delete sources

---

## Why It Matters

Source selection controls what the AI can use for grounded responses. Without selected sources, HALO answers from general knowledge rather than your specific content.

---

## Supported File Types

| Category | Extensions |
|----------|------------|
| Documents | `.pdf`, `.docx`, `.txt`, `.md` |
| Spreadsheets | `.csv`, `.xlsx`, `.xls` |
| Presentations | `.pptx` |
| Images | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp` |
| Audio | `.mp3`, `.wav`, `.m4a`, `.ogg` |
| Video | `.mp4`, `.mov`, `.avi`, `.mkv` |

---

## Adding Sources

### Upload Files

1. In **Sources**, click **+ Quellen hinzufügen**
2. Select one or more files from your computer
3. Wait for upload and ingestion to complete
4. Imported items appear in the source list

### Expected Results

- Source appears with type icon and timestamp
- Content is parsed and indexed for search
- Source is available for selection

---

## Connector-Based Collection

Connectors fetch source suggestions from external systems.

### How to Use

1. In Sources, choose one or more connectors
2. Click **Quellen abrufen**
3. Review listed results
4. Click **Importieren** for items you want

### Expected Results

- Imported connector items appear in your source list
- They can be selected like uploaded files

!!! note
    Some connector behavior is MVP/mock-backed in this version. Treat it as a guided ingestion layer that can be extended in production.

---

## Selecting Sources

### Individual Selection

1. Click the checkbox next to each source
2. Selected sources are highlighted

### Bulk Selection

1. Use "select all" checkbox
2. Or use the dropdown menu for bulk actions

### What Selection Affects

- Chat queries use selected sources only
- Studio generation uses selected sources for context
- Source summary reflects selected sources

---

## Managing Sources

### Rename

1. Click the source menu (⋮)
2. Select **Rename**
3. Enter new name
4. Confirm

### Download

1. Click the source menu (⋮)
2. Select **Download**
3. File downloads to your computer

### Delete

1. Click the source menu (⋮)
2. Select **Delete**
3. Confirm deletion

!!! warning
    Deleting a source removes it from local project state. This cannot be undone.

---

## Source List View

The source list shows:

| Column | Description |
|--------|-------------|
| Checkbox | Selection state |
| Icon | File type indicator |
| Name | Source filename/title |
| Type | File extension |
| Date | Import timestamp |
| Menu | Actions dropdown |

---

## Troubleshooting

### "My file fails to import"

Possible causes:

- Unsupported file extension
- Corrupted file
- Missing parsing dependency

Try this:

1. Check supported file types above
2. For audio/video, verify FFmpeg is installed
3. Try a smaller or simpler file

### "Connector returns no results"

Possible causes:

- Connector not configured
- No matching content in connected system

Try this:

1. Verify connector credentials in configuration
2. Check connector-specific settings

---

## Next Steps

- [Chat](chat.md) — Use selected sources in conversations
- [Studio](studio.md) — Generate outputs from source context
- [Notes](notes.md) — Convert notes into sources
