# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-06-08

### Added
- Linux Distribution and Desktop Environment compatibility matrix in `README.md`.

## [0.1.1] - 2026-06-08

### Added
- Comprehensive system prerequisite and package installation details in `README.md`.
- Interactive troubleshooting decision tree using Mermaid flowcharts.
- Instruction guide for automating driver reloads upon suspend/resume using a systemd service.


## [0.1.0] - 2026-06-08

### Added
- Initial release of the Dell Touchpad Troubleshooter and Data Collector utility.
- Interactive terminal menu for quick diagnostics, hardware event testing, and exporting reports.
- Non-interactive CLI flags (`--fix`, `--status`, `--report`, `--help`) for quick scripting or CLI usage.
- Automated system check of loaded kernel modules (`hid_alps`, `i2c_hid_acpi`, `i2c_hid`, `psmouse`).
- Detection and check of desktop configuration files (`kcminputrc`) and DBus properties for touchpad activation state.
- Automated log parsing to highlight errors or jumps related to input devices from the boot journal.
- GitHub Actions CI workflow to automate Python code linting.
- Community and repository files including `LICENSE` (MIT), `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md`.
