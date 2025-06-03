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

## [v0.1.6] - 2025-06-03
### Added
- Added basic MISP support (testing only)
### Changed
- Changed the Severity Distribution graph to only show the last day of data
### Fixed
- Fixed HTTPS support for web sockets
- Fixed the design for GeoLocation in Alerts and IOCS
- Fixed wire framing in YAML files (DO NOT USE EMPTY YAML FILES FOR PRODUCTION)

## [v0.1.5] - 2025-06-02
### Added
- Added Geolocation to IOCS and Alerts (Alert Detail View)
- Added windows alert YAML (as a wireframe)
- Added ubuntu alert YAML (as wireframe)
- Added a general linux alert YAML (as a wireframe)
- Added websockets for live dashboard (started implementation)
### Changed

### Fixed

## [v0.1.4] - 2025-06-02 - Production Ready for small environments
### Added
- Added saved search in SentinelIQ Search Module
- Addded saved search modal and pydantic scheme
- Added back the search bar within the alert details page
- Added support for resolution search in alerts page
- Added support for customer in sources
- Added support for customer details
- Added wireframe for operator dashboard -> dashboard/operator
- Added wireframe for settings/modules
- Added support for MaxMind GeoIP database for IP geolocation
- Added wireframe for ioc enrichment
### Changed
- User profile now uses modal for edit user
- User Role Admin for accessing settings/users -> Create, Delete Users, and view all users
- Minor changes to the changelog
### Fixed
- Added date to dashboard graph "Alerts over time"
- Minor fixes to the alert details page
- Minor fixes to the iocs page


## [v0.1.3] - 2025-06-02
### Added
- Triage All eligible alerts button
- Added searching and filtering to triage page
### Changed
- Updated scripts/* due to directory structure changes
### Fixed
- Webhook startup script now correctly handles the application load


## [v0.1.2] - 2025-06-01
### Added
- Added version modal and check in navigation header
### Changed
- Updated README to also include update instructions


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