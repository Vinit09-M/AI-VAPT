import subprocess
import os
import shutil
import sys

def run_cmd(name, cmd_list):
    print(f"\n[*] Testing {name}...")
    try:
        # Use shell=True for bat files or complex path resolution
        result = subprocess.run(
            cmd_list, 
            capture_output=True, 
            text=True, 
            shell=True if name == "ZAP" else False
        )
        if result.returncode == 0:
             print(f"   SUCCESS: {result.stdout[:100].strip()}...")
        else:
             print(f"   FAILED (Code {result.returncode})")
             print(f"   STDERR: {result.stderr.strip()}")
    except Exception as e:
        print(f"   EXCEPTION: {e}")

# 1. Test Perl (Critical for Nikto)
run_cmd("Perl", ["perl", "-v"])

# 2. Test Nikto Paths
nikto_candidates = [r"C:\Tools\Nikto\program\nikto.pl", r"C:\Tools\Nikto\nikto.pl"]
found_nikto = False
for p in nikto_candidates:
    if os.path.exists(p):
        print(f"\n[*] Found Nikto script at: {p}")
        # Try running it with perl
        run_cmd("Nikto (via Perl)", ["perl", p, "-H"])
        found_nikto = True
        break
if not found_nikto:
    print("\n[!] Nikto script NOT FOUND in C:\\Tools\\Nikto")

# 3. Test ZAP
zap_path = r"C:\Program Files\OWASP\Zed Attack Proxy\zap.bat"
if os.path.exists(zap_path):
    print(f"\n[*] Found ZAP at: {zap_path}")
    run_cmd("ZAP", [zap_path, "-help"])
else:
    print(f"\n[!] ZAP NOT FOUND at {zap_path}")
    # Try finding it
    w = shutil.which("zap.bat")
    print(f"    shutil.which('zap.bat') -> {w}")

# 4. Test Nuclei
# Manually look in Go path if not in global path
go_nuclei = os.path.expanduser(r"~\go\bin\nuclei.exe")
if os.path.exists(go_nuclei):
     run_cmd("Nuclei (Direct Path)", [go_nuclei, "-version"])
else:
     run_cmd("Nuclei (Global)", ["nuclei", "-version"])
