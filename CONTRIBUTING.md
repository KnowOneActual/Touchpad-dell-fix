# Contributing Guidelines

Thank you for your interest in contributing to the Touchpad Troubleshooter & Data Collector! Contributions from the community help make this tool better for everyone.

## How to Contribute

### 1. Reporting Bugs
If you find a bug or issue (such as the utility failing to detect a touchpad or failing to unload modules on your specific kernel version):
1. Check the existing issues to see if it has already been reported.
2. Open a new issue with a clear description, your system logs, and details of your laptop configuration (output of `uname -a` and `/proc/bus/input/devices`).

### 2. Suggesting Enhancements
We welcome ideas for new features or improvements:
1. Open an issue describing the proposed enhancement.
2. Explain the use case and how it benefits users.

### 3. Pull Requests
If you would like to submit a code change:
1. Fork the repository and create a new branch.
2. Write clean, readable Python code matching the existing style.
3. Ensure no trailing whitespaces or syntax errors (run a linter like `flake8` or `black` on your changes).
4. Submit a Pull Request targeting the `main` branch.

## Code Style

This project follows standard Python guidelines (PEP 8):
*   Use 4 spaces for indentation (no tabs).
*   Add descriptive docstrings and comments where appropriate.
*   Keep functions focused and modular.
