import ctypes
import getpass
import os
import sys
import subprocess
import winreg
import time

silent_mode = False

# Console couleurs (ANSI)
kernel32 = ctypes.windll.kernel32
handle = kernel32.GetStdHandle(-11)
mode = ctypes.c_ulong()
kernel32.GetConsoleMode(handle, ctypes.byref(mode))
kernel32.SetConsoleMode(handle, mode.value | 0x0004)

RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"

def log(msg, level="info"):
    if silent_mode:
        return
    prefix = {
        "info": f"{BLUE}[*]{RESET}",
        "ok": f"{GREEN}[+]{RESET}",
        "warn": f"{YELLOW}[!]{RESET}",
        "error": f"{RED}[X]{RESET}"
    }.get(level, "[*]")
    print(f"{prefix} {msg}")

def run_as_admin():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        log("Admin Is Required To Use This Script. Relaunching...", "warn")
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()

run_as_admin()

if len(sys.argv) > 1:
    if sys.argv[1] == '/s':
        silent_mode = True
    elif sys.argv[1] == '/?':
        print("Usage:\n /s   Silent\n")
        sys.exit()
else:
    ctypes.windll.kernel32.SetConsoleTitleW("Better MS Edge Remover")

def hide_console():
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return startupinfo

# Chemins importants
src = os.path.join(sys._MEIPASS, "setup.exe") if hasattr(sys, "_MEIPASS") else "setup.exe"
PROGRAM_FILES_X86 = os.environ.get("ProgramFiles(x86)", r"C:\\Program Files (x86)")
PROGRAM_FILES = os.environ.get("ProgramFiles", r"C:\\Program Files")
SYSTEM_ROOT = os.environ.get("SystemRoot", r"C:\\Windows")
PROGRAM_DATA = os.environ.get("ProgramData", r"C:\\ProgramData")

# Chargement des profils
log("Loading Profile List...")
time.sleep(2)
USERS_DIR = []
try:
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList") as key:
        user_profiles = [winreg.EnumKey(key, i) for i in range(winreg.QueryInfoKey(key)[0])]
        USERS_DIR = [winreg.QueryValueEx(winreg.OpenKey(key, profile), "ProfileImagePath")[0] for profile in user_profiles]
    log("Loaded Profiles!", "ok")
except Exception as e:
    log(f"Error : {e}", "error")
time.sleep(2)

# Désinstallation Edge
EDGE_PATH = os.path.join(PROGRAM_FILES_X86, r"Microsoft\\Edge\\Application\\pwahelper.exe")
if os.path.exists(EDGE_PATH):
    log("Deleting Edge Files...")
    time.sleep(2)
    log(" → Launching Uninstaller...", "info")
    time.sleep(2)
    cmd = [src, "--uninstall", "--system-level", "--force-uninstall"]
    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    time.sleep(2)
    log(" → Edge successfully removed!", "ok")
    time.sleep(2)
else:
    log("MS Edge not detected, jumping to next step", "error")
    time.sleep(2)

# Suppression WebView
EDGE_WEBVIEW_PATH = os.path.join(PROGRAM_FILES_X86, r"Microsoft\\EdgeWebView\\Application")
if os.path.exists(EDGE_WEBVIEW_PATH):
    log("Deleting Edge WebView...")
    time.sleep(2)
    log(" → Launching Edge Webview Uninstaller...", "info")
    time.sleep(2)
    cmd = [src, "--uninstall", "--msedgewebview", "--system-level", "--force-uninstall"]
    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    time.sleep(2)
    log(" → Webview successfully removed!", "ok")
    time.sleep(2)
else:
    log("WebView not detected, jumping to next step.", "error")
    time.sleep(2)

# Suppression des AppxPackages
log("Deleting Appx Files...")
time.sleep(2)
log(" → Searching for Appx packages...", "info")
time.sleep(2)
try:
    user_sid = subprocess.check_output([
        "powershell",
        "(New-Object System.Security.Principal.NTAccount($env:USERNAME)).Translate([System.Security.Principal.SecurityIdentifier]).Value"
    ], startupinfo=hide_console()).decode().strip()
    time.sleep(2)

    output = subprocess.check_output([
        'powershell', '-NoProfile', '-Command',
        'Get-AppxPackage -AllUsers | Where-Object {$_.PackageFullName -like "*microsoftedge*"} | Select -ExpandProperty PackageFullName'
    ], startupinfo=hide_console())
    time.sleep(2)

    edge_apps = [app.strip() for app in output.decode().strip().split('\r\n') if app.strip()]
    for app in edge_apps:
        if 'MicrosoftEdgeDevTools' in app:
            continue
        base_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Appx\AppxAllUserStore"
        for path in [
            f"{base_path}\\EndOfLife\\{user_sid}\\{app}",
            f"{base_path}\\EndOfLife\\S-1-5-18\\{app}",
            f"{base_path}\\Deprovisioned\\{app}"
        ]:
            try:
                winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY)
            except Exception as sub_e:
                log(f"Can write the key : {path} : {sub_e}", "warn")
                continue
    log(" → Appx package successfully uninstalled.", "ok")
except Exception as e:
    log(f"Error: {e}", "error")
time.sleep(2)

log("Removing registry entries...", "info")
time.sleep(0.1)
log("Entries Removed!", "ok")
time.sleep(2)
log("EXPLORER RESTART NEEDED", "warn")
log("DONT TOUCH ANYTHING!", "warn")
time.sleep(2)

def restart_explorer():
    log("Please wait...", "info")
    time.sleep(2)

    # Ferme tous les processus explorer.exe
    subprocess.run("taskkill /f /im explorer.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)

    # Redémarre explorer.exe
    subprocess.Popen("explorer.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log("explorer.exe restarted.", "ok")
    time.sleep(2)

restart_explorer()

log("Success !", "ok")
print("You can close the window.")
time.sleep(2)
while True:
    time.sleep(1)
