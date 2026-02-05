import os
import urllib.request
import zipfile
import shutil

nikto_dir = r"C:\Tools\Nikto"
zip_path = os.path.join(nikto_dir, "nikto.zip")
url = "https://github.com/sullo/nikto/archive/refs/heads/master.zip"

print(f"[*] Fixing Nikto Installation in {nikto_dir}...")

# 1. Clean up
if os.path.exists(nikto_dir):
    try:
        shutil.rmtree(nikto_dir)
        print("   [-] Removed existing directory.")
    except Exception as e:
        print(f"   [!] Failed to delete dir: {e}")

os.makedirs(nikto_dir, exist_ok=True)

# 2. Download
print(f"[*] Downloading Nikto from {url}...")
try:
    urllib.request.urlretrieve(url, zip_path)
    print("   [-] Download successful.")
except Exception as e:
    print(f"   [!] Download failed: {e}")
    exit(1)

# 3. Extract
print("[*] Extracting...")
try:
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(nikto_dir)
    print("   [-] Extraction successful.")
except Exception as e:
    print(f"   [!] Extraction failed: {e}")
    exit(1)

# 4. Verify
expected_path = os.path.join(nikto_dir, "nikto-master", "program", "nikto.pl")
if os.path.exists(expected_path):
    print(f"\n✅ SUCCESS: Found nikto.pl at {expected_path}")
else:
    print(f"\n❌ ERROR: Still cannot find nikto.pl. Listing dir:")
    for root, dirs, files in os.walk(nikto_dir):
         print(f"   {root} -> {files}")
