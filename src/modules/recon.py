import subprocess
import shutil
import json
import os
from datetime import datetime

class ReconScanner:
    def __init__(self):
        # Explicit Nmap check for Windows
        self.nmap_path = shutil.which("nmap")
        if not self.nmap_path:
            possible_path = r"C:\Program Files (x86)\Nmap\nmap.exe"
            if os.path.exists(possible_path):
                self.nmap_path = possible_path

    def check_nmap_availability(self):
        return self.nmap_path is not None

    def run_nmap_scan(self, target):
        """
        Runs a fast Nmap scan (-F) on the target.
        Returns a list of open ports and services.
        """
        if not self.check_nmap_availability():
            print("ERROR: Nmap not found in PATH or standard Program Files.")
            return {"error": "Nmap not installed or not found in PATH"}

        print(f"[*] Running Nmap Fast Scan on {target}...")
        
        try:
            # Command: nmap -F <target>
            # -F: Fast mode (scan fewer ports than the default scan)
            command = [self.nmap_path, "-F", target]
            
            # Using subprocess to run the command
            print(f"DEBUG: Executing command: {' '.join(command)}")
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True,
                stdin=subprocess.DEVNULL
            )
            
            if result.returncode != 0:
                print(f"ERROR: Nmap failed. Stderr: {result.stderr}")
                return {"error": f"Nmap Scan Failed: {result.stderr}"}
                
            # Parse simple output (For MVP, we just return the raw lines that look like ports)
            output_lines = result.stdout.splitlines()
            parsed_ports = []
            
            # Basic parsing logic for Nmap text output
            scanning_ports = False
            for line in output_lines:
                if "PORT" in line and "STATE" in line:
                    scanning_ports = True
                    continue
                if scanning_ports and "/tcp" in line:
                     parts = line.split()
                     # Example line: 80/tcp open http
                     if len(parts) >= 3 and parts[1] == "open":
                         parsed_ports.append({
                             "port": parts[0],
                             "state": parts[1],
                             "service": parts[2]
                         })
            
            return {
                "target": target,
                "tool": "nmap",
                "scan_type": "Fast Scan (-F)",
                "open_ports": parsed_ports,
                "raw_output": result.stdout
            }

        except Exception as e:
            return {"error": f"Execution Error: {str(e)}"}

    def _find_go_tool(self, tool_name):
        # Helper to find Go tools in common locations
        # PRIORITIZE Go bin to avoid conflicts (e.g. python 'httpx' module)
        go_bin = os.path.expanduser(r"~\go\bin")
        possible_path = os.path.join(go_bin, f"{tool_name}.exe")
        if os.path.exists(possible_path):
            return possible_path

        # Fallback to PATH
        path = shutil.which(tool_name)
        if path: return path
            
        return None

    def run_subfinder(self, target):
        """
        Runs Subfinder to discover subdomains.
        """
        subfinder_path = self._find_go_tool("subfinder")
        if not subfinder_path:
            print("ERROR: Subfinder not found in PATH or Go/bin")
            return {"error": "Subfinder not installed or not found in PATH"}
        
        print(f"[*] Running Subfinder on {target} using {subfinder_path}...")
        try:
             # subfinder -d <target> -silent -json
            command = [subfinder_path, "-d", target, "-silent", "-json"]
            
            result = subprocess.run(command, capture_output=True, text=True, stdin=subprocess.DEVNULL)
            
            if result.returncode != 0:
                print(f"ERROR: Subfinder failed. Stderr: {result.stderr}")
                print(f"[!] Subfinder Error: {result.stderr}")
                
            subdomains = []
            for line in result.stdout.splitlines():
                try:
                    data = json.loads(line)
                    if "host" in data:
                        subdomains.append(data["host"])
                except:
                    continue
            
            return {
                "target": target,
                "tool": "subfinder",
                "subdomains_count": len(subdomains),
                "subdomains": subdomains
            }
        except Exception as e:
            return {"error": f"Execution Error: {str(e)}"}

    def run_amass(self, target):
        """
        Runs Amass (Passive) to discover subdomains.
        """
        amass_path = self._find_go_tool("amass")
        if not amass_path:
            return {"error": "Amass not installed or not found in PATH"}
        
        print(f"[*] Running Amass (Passive) on {target} using {amass_path}...")
        try:
            # amass enum -passive -d <target>
            command = [amass_path, "enum", "-passive", "-d", target]
            
            result = subprocess.run(command, capture_output=True, text=True, stdin=subprocess.DEVNULL)
            
            subdomains = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if line:
                    subdomains.append(line)
            
            return {
                "target": target,
                "tool": "amass",
                "subdomains_count": len(subdomains),
                "subdomains": subdomains
            }
        except Exception as e:
            return {"error": f"Execution Error: {str(e)}"}

    def run_httpx(self, target):
        """
        Runs httpx for technology detection and status code checking.
        """
        httpx_path = self._find_go_tool("httpx")
        if not httpx_path:
            return {"error": "httpx not installed or not found in PATH"}

        print(f"[*] Running httpx Technology Detection on {target} using {httpx_path}...")
        try:
            # httpx -u <target> -td -json -silent
            # -td: Technology Detection
            command = [httpx_path, "-u", target, "-td", "-json", "-silent"]
            
            result = subprocess.run(command, capture_output=True, text=True, stdin=subprocess.DEVNULL)
            
            tech_data = {}
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    tech_data = {
                        "url": data.get("url"),
                        "title": data.get("title"),
                        "status_code": data.get("status_code"),
                        "technologies": data.get("tech", []),
                        "webserver": data.get("webserver"),
                        "ip": data.get("host")
                    }
                except:
                    tech_data = {"error": "Failed to parse httpx JSON output"}
            
            return {
                "target": target,
                "tool": "httpx",
                "data": tech_data
            }
        except Exception as e:
            return {"error": f"Execution Error: {str(e)}"}

    def get_asset_inventory(self, target):
        """
        Consolidates results from all tools into a structured JSON inventory.
        Fulfills Step 2 'Workflow Connection'.
        """
        print(f"[*] Starting Complete Asset Discovery for: {target}")
        
        # 1. Subdomain Discovery
        subs_sf = self.run_subfinder(target)
        subs_am = self.run_amass(target)
        
        all_subs = set()
        if "subdomains" in subs_sf: all_subs.update(subs_sf["subdomains"])
        if "subdomains" in subs_am: all_subs.update(subs_am["subdomains"])
        
        # 2. Port Scan
        ports_root = self.run_nmap_scan(target)
        
        # 3. Technology Detection
        tech_root = self.run_httpx(target)
        
        inventory = {
            "target": target,
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "discovery": {
                "subdomains_count": len(all_subs),
                "subdomains": list(all_subs)
            },
            "infrastructure": {
                "main_target_ports": ports_root.get("open_ports", []),
                "technologies": tech_root.get("data", {})
            },
            "summary": f"Found {len(all_subs)} subdomains and {len(ports_root.get('open_ports', []))} open ports."
        }
        
        return inventory
