# 📜 Changelog

All notable changes to **Sentinel Commander** will be documented in this file.  
This project will adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> 🚨 **Note:** Sentinel Commander is in **early alpha**. Breaking changes may occur at any time without notice.

---
Template
```bash
## [Unreleased]
### Added

### Changed

### Fixed
```
## [Unreleased]
### Added

### Changed
- Updated scripts/* due to directory structure changes
### Fixed

## [v0.1.2] - 2025-06-01
### Added
- Added version modal and check in navigation header

### Changed
- Updated README to also include update instructions
### Fixed


## [v0.1.1] - 2025-06-01
### Added
- New alert category view with severity-aware badge styling
- Separate webhook-only application (`webhook_app.py`) with standalone startup/stop scripts
- Pagination with smart limits (`First`, `Prev`, `Next`, `Last`) for better UX
- Category counters on the alert category index
- Started using Semantic versioning
- Added version checks

### Changed
- Moved webhook router out of `main.py` for isolation
- Updated navbar to support `Alerts → Categories` navigation
- CSS updates for severity coloring:
  - Critical = Purple
  - High = Red
  - Medium = Yellow
  - Low = Green

### Fixed
- Resolved full-row background bug in alert tables
- Fixed unclosed `{% if %}` Jinja block that broke category view