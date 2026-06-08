#!/usr/bin/env python3
import os
import sys
import re
import subprocess
import datetime

# Color configuration for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(title):
    print(f"\n{Colors.BOLD}{Colors.HEADER}=== {title} ==={Colors.ENDC}")

def print_ok(msg):
    print(f"{Colors.OKGREEN}[✓] {msg}{Colors.ENDC}")

def print_warn(msg):
    print(f"{Colors.WARNING}[!] {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}[✗] {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKBLUE}[*] {msg}{Colors.ENDC}")

def run_command(cmd, shell=False, check=False):
    """Utility to run system commands and return stdout/stderr."""
    try:
        res = subprocess.run(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -2, "", str(e)

def check_touchpad_device():
    print_header("Detecting Input Devices")
    if not os.path.exists("/proc/bus/input/devices"):
        print_error("/proc/bus/input/devices not found.")
        return None

    with open("/proc/bus/input/devices", "r") as f:
        content = f.read()

    # Split by double newline to separate devices
    devices = content.strip().split("\n\n")
    touchpad_devices = []

    for dev in devices:
        name_match = re.search(r'N: Name="([^"]+)"', dev)
        handlers_match = re.search(r'H: Handlers=([^\n]+)', dev)
        sysfs_match = re.search(r'S: Sysfs=([^\n]+)', dev)
        
        if name_match:
            name = name_match.group(1)
            handlers = handlers_match.group(1) if handlers_match else ""
            sysfs = sysfs_match.group(1) if sysfs_match else ""
            
            # Look for typical touchpad keywords
            is_touchpad = False
            if any(k in name.lower() for k in ["touchpad", "trackpad", "alps", "dll07"]):
                is_touchpad = True
            elif "mouse" in name.lower() and "i2c" in sysfs.lower():
                # Some I2C touchpads present as mouse
                is_touchpad = True
            elif "dualpoint" in name.lower():
                # Track nub is closely related
                is_touchpad = True
                
            if is_touchpad:
                # Find event handler
                event_match = re.search(r'(event\d+)', handlers)
                event = event_match.group(1) if event_match else None
                touchpad_devices.append({
                    "name": name,
                    "handlers": handlers,
                    "event": event,
                    "sysfs": sysfs
                })

    if not touchpad_devices:
        print_error("No Alps, Dell, or generic touchpads detected in /proc/bus/input/devices.")
        return None

    for dev in touchpad_devices:
        print_ok(f"Found Device: {dev['name']}")
        print(f"   - Event Handler: /dev/input/{dev['event']}" if dev['event'] else "   - Event Handler: Unknown")
        print(f"   - Sysfs Path: {dev['sysfs']}")
        
    return touchpad_devices

def check_kernel_modules():
    print_header("Checking Kernel Modules")
    if not os.path.exists("/proc/modules"):
        print_error("/proc/modules not found.")
        return
        
    with open("/proc/modules", "r") as f:
        modules_content = f.read()
        
    target_modules = ["hid_alps", "i2c_hid_acpi", "i2c_hid", "psmouse"]
    for mod in target_modules:
        if mod in modules_content:
            print_ok(f"Module '{mod}' is currently LOADED.")
        else:
            print_warn(f"Module '{mod}' is NOT loaded.")

def check_kde_settings(touchpad_devices):
    print_header("Checking Desktop Environment Settings (KDE)")
    config_path = os.path.expanduser("~/.config/kcminputrc")
    if not os.path.exists(config_path):
        print_warn("KDE config file (~/.config/kcminputrc) not found. Are you using KDE?")
        return
        
    print_info(f"Reading {config_path}...")
    with open(config_path, "r") as f:
        content = f.read()
        
    for dev in touchpad_devices:
        # Match section [Libinput][<vendor>][<product>][<name>]
        # e.g., [Libinput][1102][4619][DLL07A7:01 044E:120B]
        escaped_name = re.escape(dev['name'])
        section_pattern = r"\[Libinput\]\[\d+\]\[\d+\]\[" + escaped_name + r"\]"
        
        matches = list(re.finditer(section_pattern, content))
        if matches:
            for match in matches:
                start_idx = match.end()
                # Read until next section or end of file
                next_section = content.find("[", start_idx)
                section_content = content[start_idx:next_section] if next_section != -1 else content[start_idx:]
                
                enabled_match = re.search(r"Enabled=(true|false)", section_content)
                if enabled_match:
                    status = enabled_match.group(1)
                    if status == "true":
                        print_ok(f"Device '{dev['name']}' config: Enabled=true")
                    else:
                        print_warn(f"Device '{dev['name']}' config: Enabled=false (Software Disabled!)")
                else:
                    print_info(f"Device '{dev['name']}' config found, but no 'Enabled' key (defaults to True).")
        else:
            print_info(f"No specific configuration section found in kcminputrc for '{dev['name']}'.")

def check_kde_dbus(touchpad_devices):
    print_header("Checking DBus Status (KWin / Plasma)")
    for dev in touchpad_devices:
        if not dev['event']:
            continue
            
        cmd = ["busctl", "--user", "get-property", "org.kde.KWin", 
               f"/org/kde/KWin/InputDevice/{dev['event']}", 
               "org.kde.KWin.InputDevice", "enabled"]
               
        code, stdout, stderr = run_command(cmd)
        if code == 0:
            status = "Enabled" if "true" in stdout.lower() else "Disabled"
            if status == "Enabled":
                print_ok(f"KWin DBus status for {dev['name']} ({dev['event']}): {status}")
            else:
                print_warn(f"KWin DBus status for {dev['name']} ({dev['event']}): {status} (Software Disabled!)")
        else:
            print_warn(f"Could not query DBus for {dev['name']}: {stderr}")

def collect_journal_logs():
    print_header("Analyzing Recent System Logs")
    # Search for errors/bugs in the journal related to input drivers
    cmd = "journalctl -b 0 --no-pager | grep -i -E 'alps|dll07|i2c_hid|touchpad|trackpad' | tail -n 15"
    code, stdout, stderr = run_command(cmd, shell=True)
    
    if code == 0 and stdout:
        print_info("Recent system log entries:")
        for line in stdout.splitlines():
            if "kernel bug" in line.lower() or "error" in line.lower() or "fail" in line.lower():
                print(f"  {Colors.FAIL}{line}{Colors.ENDC}")
            elif "discarded" in line.lower():
                print(f"  {Colors.WARNING}{line}{Colors.ENDC}")
            else:
                print(f"  {line}")
    else:
        print_info("No relevant log entries found in the current boot journal.")

def reload_drivers(force=False):
    print_header("Reloading Input Drivers (Root Permissions Needed)")
    print_warn("This operation requires sudo permissions to reload kernel modules.")
    
    if not force:
        confirm = input("Do you want to proceed with reloading modules? (y/N): ").strip().lower()
        if confirm != 'y':
            print_info("Reload canceled.")
            return
        
    modules = ["hid_alps", "i2c_hid_acpi", "i2c_hid"]
    
    print_info("Unloading modules...")
    # Unload in correct order of dependency
    for mod in modules:
        print(f"  Removing {mod}...")
        code, stdout, stderr = run_command(f"sudo rmmod {mod}", shell=True)
        if code != 0 and "not currently loaded" not in stderr:
            print_error(f"Failed to remove {mod}: {stderr}")
            
    print_info("Loading modules...")
    # Load back
    code, stdout, stderr = run_command("sudo modprobe i2c_hid_acpi", shell=True)
    if code == 0:
        print_ok("Loaded i2c_hid_acpi")
    else:
        print_error(f"Failed to load i2c_hid_acpi: {stderr}")
        
    code, stdout, stderr = run_command("sudo modprobe hid_alps", shell=True)
    if code == 0:
        print_ok("Loaded hid_alps")
    else:
        print_error(f"Failed to load hid_alps: {stderr}")

def live_event_test(touchpad_devices):
    print_header("Testing Physical Hardware Events")
    
    # Select device
    valid_devices = [d for d in touchpad_devices if d['event']]
    if not valid_devices:
        print_error("No devices with valid event handlers to test.")
        return
        
    dev = valid_devices[0]
    if len(valid_devices) > 1:
        print("Select device to test:")
        for i, d in enumerate(valid_devices):
            print(f"  [{i}] {d['name']} (/dev/input/{d['event']})")
        try:
            choice = int(input("Choice (default 0): ").strip() or 0)
            dev = valid_devices[choice]
        except:
            dev = valid_devices[0]
            
    print_info(f"Starting event listener on /dev/input/{dev['event']} for 5 seconds...")
    print_warn("Move your finger on the trackpad NOW to see if events trigger.")
    
    # Run timeout 5s libinput debug-events --device /dev/input/eventX
    cmd = f"sudo timeout 5s libinput debug-events --device /dev/input/{dev['event']}"
    code, stdout, stderr = run_command(cmd, shell=True)
    
    # timeout returns 124 when it times out (which is expected)
    if stdout:
        print_ok("SUCCESS! Received events from the hardware:")
        lines = stdout.splitlines()
        for line in lines[:15]:
            print(f"  {line}")
        if len(lines) > 15:
            print(f"  ... and {len(lines)-15} more events.")
        print_ok("\nThe hardware is sending signals! If it doesn't move the cursor, it is a window manager/software mapping problem.")
    else:
        print_error("NO EVENTS RECEIVED. The hardware did not send any touch signals.")
        print_info("This indicates either a hardware fault, disconnected ribbon cable, or the bus/driver is totally stuck.")

def export_report(touchpad_devices):
    report_file = "touchpad_diagnostic_report.txt"
    print_header(f"Exporting Report to {report_file}")
    
    with open(report_file, "w") as f:
        f.write("=========================================\n")
        f.write("  TOUCHPAD DIAGNOSTIC REPORT\n")
        f.write(f"  Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=========================================\n\n")
        
        f.write("--- 1. INPUT DEVICES ---\n")
        if touchpad_devices:
            for d in touchpad_devices:
                f.write(f"Name: {d['name']}\n")
                f.write(f"Event: /dev/input/{d['event']}\n")
                f.write(f"Sysfs: {d['sysfs']}\n\n")
        else:
            f.write("No touchpad devices detected.\n\n")
            
        f.write("--- 2. KERNEL MODULES ---\n")
        if os.path.exists("/proc/modules"):
            with open("/proc/modules", "r") as m:
                mods = m.read()
                for target in ["hid_alps", "i2c_hid_acpi", "i2c_hid", "psmouse"]:
                    status = "LOADED" if target in mods else "NOT LOADED"
                    f.write(f"{target}: {status}\n")
        f.write("\n")
        
        f.write("--- 3. RECENT LOGS ---\n")
        code, stdout, stderr = run_command("journalctl -b 0 --no-pager | grep -i -E 'alps|dll07|i2c_hid|touchpad|trackpad' | tail -n 30", shell=True)
        if stdout:
            f.write(stdout)
        else:
            f.write("No matching logs found.\n")
            
    print_ok(f"Report exported successfully to {os.path.abspath(report_file)}")

def main():
    print(f"{Colors.BOLD}{Colors.OKBLUE}==============================================={Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKBLUE}  Dell Touchpad Troubleshooter & Data Collector{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKBLUE}==============================================={Colors.ENDC}")
    
    # Check for CLI flags
    if len(sys.argv) > 1:
        flag = sys.argv[1].lower()
        if flag in ["--fix", "-f"]:
            reload_drivers(force=True)
            sys.exit(0)
        elif flag in ["--status", "-s"]:
            devices = check_touchpad_device()
            if devices:
                check_kernel_modules()
                check_kde_settings(devices)
                check_kde_dbus(devices)
                collect_journal_logs()
            sys.exit(0)
        elif flag in ["--report", "-r"]:
            devices = check_touchpad_device()
            export_report(devices)
            sys.exit(0)
        elif flag in ["--help", "-h"]:
            print("Usage: ./touchpad_tool.py [option]")
            print("Options:")
            print("  --fix, -f       Force reload drivers non-interactively (requires sudo)")
            print("  --status, -s    Run diagnostics and print health check")
            print("  --report, -r    Export diagnostic report to file")
            print("  --help, -h      Show this help message")
            sys.exit(0)
            
    # 1. Detect device first
    devices = check_touchpad_device()
    
    while True:
        print_header("Main Menu")
        print("  [1] Run All Diagnostics (Health Check)")
        print("  [2] Reload Touchpad Drivers (Fix Unresponsive Trackpad)")
        print("  [3] Test Physical Hardware Events (libinput listener)")
        print("  [4] Export Diagnostic Log to File")
        print("  [5] Exit")
        
        try:
            choice = input("\nEnter choice (1-5): ").strip()
            if choice == '1':
                if devices:
                    check_kernel_modules()
                    check_kde_settings(devices)
                    check_kde_dbus(devices)
                    collect_journal_logs()
                else:
                    print_error("Cannot run diagnostics: No touchpad device detected.")
            elif choice == '2':
                reload_drivers()
                # Re-detect in case event handles changed
                devices = check_touchpad_device()
            elif choice == '3':
                if devices:
                    live_event_test(devices)
                else:
                    print_error("No device detected to test.")
            elif choice == '4':
                export_report(devices)
            elif choice == '5':
                print_info("Exiting troubleshooter. Have a nice day!")
                break
            else:
                print_error("Invalid choice. Please enter 1-5.")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print_error(f"Error in menu: {e}")

if __name__ == "__main__":
    main()
