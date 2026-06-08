# Touchpad Troubleshooter & Data Collector

An interactive Python utility to troubleshoot Dell/Alps trackpads on Linux (e.g. Fedora, Ubuntu) when they stop responding. The utility handles data collection, system diagnostics, and can automatically reload driver modules to fix unresponsive trackpads.

---

## 🚀 How to Run the Tool

Ensure the script is executable:
```bash
chmod +x touchpad_tool.py
```

### Interactive Mode
You can run the script interactively to use the built-in menu:
```bash
./touchpad_tool.py
```

### Non-Interactive CLI Arguments
You can also run specific actions directly from the command line:

*   **Automatic Fix** (unloads and reloads kernel modules directly, requires `sudo`):
    ```bash
    ./touchpad_tool.py --fix
    ```
*   **Status Check** (performs diagnostics and prints results to terminal):
    ```bash
    ./touchpad_tool.py --status
    ```
*   **Export Report** (runs diagnostics and exports to a file):
    ```bash
    ./touchpad_tool.py --report
    ```

---

## 🛠️ Main Features & Options

### 1. Run All Diagnostics (Health Check)
Performs a comprehensive scan of your touchpad's status:
*   **Hardware Detection**: Scans `/proc/bus/input/devices` to verify the trackpad device is visible to the kernel and find its active event handler (e.g., `/dev/input/event7`).
*   **Kernel Modules**: Checks if the necessary drivers (`hid_alps`, `i2c_hid_acpi`, `i2c_hid`, `psmouse`) are loaded in memory.
*   **KDE Config Check**: Reads your desktop user settings file (`~/.config/kcminputrc`) to see if the trackpad has been disabled in the desktop configuration.
*   **KWin DBus Status**: Direct query to KWin (Fedora Wayland Window Manager) to see if it has marked the device as active or disabled.
*   **Log Analysis**: Pulls recent boot logs from `journalctl` matching the touchpad and filters for kernel errors or jumping events.

### 2. Reload Touchpad Drivers (Fix Unresponsive Trackpad)
When your trackpad stops responding due to a driver crash or erratic jump:
*   Unloads the stacked kernel modules (`hid_alps`, `i2c_hid_acpi`, and `i2c_hid`).
*   Reloads them in sequence.
*   *Note: This operation requires root/sudo privileges to load and unload kernel modules.*

### 3. Test Physical Hardware Events (libinput listener)
To determine if the issue is a physical hardware fault or just a software misconfiguration:
*   Launches a 5-second listener via `libinput debug-events`.
*   **What to do**: Swipe your finger on the trackpad during the 5-second window.
*   If you see output coordinates, the hardware and kernel are working perfectly, meaning the issue is purely a Wayland/KWin desktop setting. If you see no output, the touchpad is not sending physical signals.

### 4. Export Diagnostic Log to File
*   Generates a clean text file named `touchpad_diagnostic_report.txt` in the folder where you ran the script.
*   You can open, read, or share this report.

---

## 📝 Common Dell Hotkeys
If the tool diagnostics show that the touchpad is software-disabled or not receiving events, try pressing the hardware toggle key. On Dell laptops, this is usually:
*   **Fn + F3**
*   **Fn + F9**
*   **Fn + F5**
*   Or press the function key directly (depending on your BIOS toggle setup).
