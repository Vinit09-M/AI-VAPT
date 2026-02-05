import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from modules.scanner import VulnScanner

print("[-] Initializing VulnScanner...")
scanner = VulnScanner()

print("[-] Checking Tools Availability...")
avail = scanner.check_tools_availability()
print(f"RESULTS: {avail}")

# Detailed checks
import shutil
print(f"\n[DEBUG] shutil.which('nuclei'): {shutil.which('nuclei')}")
print(f"[DEBUG] _find_go_tool('nuclei'): {scanner._find_go_tool('nuclei')}")
print(f"[DEBUG] shutil.which('nikto'): {shutil.which('nikto')}")
print(f"[DEBUG] C:\\Tools\\Nikto path: {os.path.exists(r'C:\Tools\Nikto\program\nikto.pl')}")
print(f"[DEBUG] shutil.which('zap.bat'): {shutil.which('zap.bat')}")
print(f"[DEBUG] ZAP Default Path: {os.path.exists(r'C:\Program Files\OWASP\Zed Attack Proxy\zap.bat')}")
