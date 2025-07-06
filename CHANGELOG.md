# 📜 Changelog

All notable changes to **Sentinel Commander** will be documented in this file.  
This project will adhere to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> 🚨 **Note:** Sentinel Commander is in **early beta**. Breaking changes may occur at any time without notice.

---
Template
```bash
## [Unreleased]
### Added

### Changed

### Fixed
```
## [0.2.6] - 2025-07-06 - Quality of life update nr 2
### Added
- Keyboard shortcuts
- Temporary footer to display version and clock
- Placeholders for internal functions
### Changed
- navbar retrofit, moved some items to settings.
### Notes
- Preparing for the consolidation patch. This will be a big change before v1.0

## [v0.2.5] - 2025-07-04 - Quality of life update nr 1 
### Added
- Promote to case from alert detail view
- Agent View from dropdown alerts
- Agent Detail view to show all alerts from that specific agent
### Changed
- Minor changes to the styles.css
- The default alert view has been changed to a table view for testing
### Fixed
- Javascript bug on alert view
- Fixed bug in operator dashboard due to severity mapping


## [v0.2.4] - 2025-07-03
### Added
- Additional debug statements for help


## [v0.2.3] - 2025-06-19
### Added
- Merge alert ability. Merge alerts into cases.

## [v0.2.2] - 2025-06-09
### Added

### Changed

### Fixed
- Username/Email is now used instead of hardcoded admin on notes in cases
### Removed
- Webhook/Router -- Unused

## [v0.2.1] - 2025-06-03 - The removing a lot of stuff to place new stuff update!
### Added
- Placeholders for MISP, MaxMind and VirusTotal Module Pages
- Placeholder for documentation in settings
- Logging to MISP Module (Centralized Logging)
### Changed
- Commented out the API Routers due to security for production
- Moved matrics.py into app/utils/sockets
- alerts_details_view.py Imports
- Collapsable shown with button for all parsed fields
### Fixed

### Removed
- app/db/session.py (redundant)
- app/utils/display.py (redundant)
- app/utils/geo.py (redundant)
- Removed legacy rendering of Alert Details



## [v0.2.0] - 2025-06-03
### Fixed
- Trying to fix agent name issue in alert detail


## [v0.1.10] - 2025-06-03
### Changed
- Changed the alert presentation on the live dashboard to include ID
- Changed the triage to show only in progress and new alerts when entering sentineliq/triage instead of all


## [v0.1.9] - 2025-06-03
### Fixed
- Alert to live dashboard


## [v0.1.8] - 2025-06-03
### Added
- Added tasks to tasks directory
### Changed
- Added additional debug statements for sockets for real time alerts
### Fixed


## [v0.1.7] - 2025-06-03
### Added
- SentinelIQ Enrichment Module
- Added support for Geolocation and MISP enrichment in SentinelIQ Enrichment Module
- Added some scheduled tasks for quality of life improvements
### Changed
- Changed the main.py to use dedicated router registry
### Fixed
- Persistent filters in alerts when searching and performing bulk actions
- Fixed the dashboard design, forgot to close a div


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
- Switched out print statements with actual logging
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