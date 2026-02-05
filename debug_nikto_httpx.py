import subprocess
import os
import shutil

# 1. Debug Httpx (Recon)
def _find_go_tool(tool_name):
    path = shutil.which(tool_name)
    if path: return path
    go_bin = os.path.expanduser(r"~\go\bin")
    possible_path = os.path.join(go_bin, f"{tool_name}.exe")
    if os.path.exists(possible_path): return possible_path
    return None

print(f"[*] Checking Httpx...")
httpx_path = _find_go_tool("httpx")
print(f"    Path: {httpx_path}")

if httpx_path:
    print(f"    Running test scan on scanme.nmap.org...")
    try:
        # httpx -u <target> -td -json -silent
        cmd = [httpx_path, "-u", "scanme.nmap.org", "-title", "-silent"]
        res = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        print(f"    Return Code: {res.returncode}")
        print(f"    Stdout: {res.stdout.strip()}")
        print(f"    Stderr: {res.stderr.strip()}")
    except Exception as e:
        print(f"    Error: {e}")
else:
    print("    [!] Httpx not found.")


# 2. Debug Nikto (Perl)
print(f"\n[*] Checking Nikto...")
nikto_path = r"C:\Tools\Nikto\nikto-master\program\nikto.pl"
print(f"    Path exists? {os.path.exists(nikto_path)}")

if os.path.exists(nikto_path):
    # Try multiple ways to invoke
    print(f"    Attempt 1: Raw path via Perl")
    cmd = ["perl", nikto_path, "-Version"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        print(f"    [1] Ret: {res.returncode}")
        print(f"    [1] Stdout: {res.stdout.strip()[:100]}")
        print(f"    [1] Stderr: {res.stderr.strip()}")
    except Exception as e:
        print(f"    [1] Exception: {e}")

    # Try normalizing path
    norm_path = os.path.normpath(nikto_path)
    print(f"    Attempt 2: Normalized path ({norm_path})")
    cmd = ["perl", norm_path, "-Version"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        print(f"    [2] Ret: {res.returncode}")
    except Exception as e:
        print(f"    [2] Exception: {e}")
