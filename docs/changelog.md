# Changelog

All notable changes to HALO Core are documented on this page.

---

## [Unreleased]

### Added

- **DICOM Tools**: Medical imaging anonymization page with HIPAA Safe Harbor compliant tag removal
  - Configurable anonymization (patient, institution, study data)
  - UID regeneration for Study/Series/SOP Instance
  - Private tag removal
  - Batch processing of multiple DICOM files
  - Export anonymization mapping as CSV
- **MCP Connectors**: Environment variable configuration for external integrations
  - Notion API integration
  - Google Drive OAuth credentials
  - Microsoft 365 / OneDrive (MSAL authentication)
- **PACS Integration**: Environment variables for DICOM PACS server connection
- **Auto-anonymization**: Optional DICOM anonymization on upload to Sources

### Changed

- Documentation restructured into three main sections: User Handbook, Admin Guide, Technical Reference
- Mkdocs theme customized with corpusanalytica.com color palette (#00C2A8)
- Developer documentation moved to `docs/reference/` subdirectory

---

## [2025.03] - Documentation Overhaul

### Added

- **User Handbook**: 11 comprehensive pages for end users
  - Getting Started, Sources, Chat, Studio, Notes
  - Configuration, Advanced Usage, Workflows
  - Troubleshooting, FAQ, Glossary
- **Admin Guide**: 7 pages for system administrators
  - Deployment, Configuration, User Management
  - Security, Monitoring, Maintenance
- **Technical Reference**: 8 pages for developers
  - Repository Overview, Architecture and Runtime
  - Agent System, Data Storage and Retrieval
  - UI Panels and Pages, Development Testing and Operations
- Custom MkDocs Material theme with light/dark mode
- Logo and icon integration from assets folder

---

## [2025.02] - Agno Adoption

### Added

- Team-based AI agent orchestration with delegation strategies
- Coordination modes: `direct_only`, `delegate_on_complexity`, `always_delegate`, `coordinated_rag`
- Structured run telemetry for chat turns
- Memory backend support via `HALO_AGENT_DB`
- Streaming event normalization for tool calls
- Knowledge retrieval with LanceDB vector search
- Windows vector search fallback for FTS lock issues

### Changed

- Migrated to Agno agent framework
- Updated streaming to use `RunEvent`/`TeamRunEvent` enums
- Improved chat runtime with fallback behavior

---

## [2025.01] - Initial Release

### Added

- Core Streamlit application with sidebar navigation
- Sources panel for file upload and management
- Chat panel with source-grounded responses
- Studio panel for template-based output generation
- Notes management system
- Configuration hub for app settings
- Multi-format file support (PDF, DOCX, TXT, MD, CSV, XLSX, PPTX, images, audio, video)
- Multimodal input (text, images, audio)
- Studio templates: Bericht, Infografik, Podcast, Videoubersicht, Präsentation, Datentabelle

---

## Versioning

HALO Core follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

---

## Contributing

See [AGENTS.md](https://github.com/aizech/halo_core/blob/main/AGENTS.md) for contribution guidelines.

---

Made with ❤️ by Corpus Analytica
