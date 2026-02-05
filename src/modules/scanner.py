import subprocess
import shutil
import json
import os
from datetime import datetime

class VulnScanner:
    def __init__(self):
        # We assume nuclei is in the PATH (installed via Dockerfile)
        self.nuclei_path = shutil.which("nuclei")
        self.output_dir = "scans"
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def check_tools_availability(self):
        # Check ZAP (Windows Default)
        # Found path: C:\Program Files\ZAP\Zed Attack Proxy\zap.bat
        zap_windows = r"C:\Program Files\ZAP\Zed Attack Proxy\zap.bat"
        zap_exists = shutil.which("zap.bat") is not None or os.path.exists(zap_windows)

        # Check Nuclei (Use robust finder)
        nuclei_exists = self._find_go_tool("nuclei") is not None

        # Check Nikto (Requires Perl on Windows, tricky)
        nikto_exists = False 
        # Path: C:\Tools\Nikto\nikto-master\program\nikto.pl
        nikto_w_path = r"C:\Tools\Nikto\nikto-master\program\nikto.pl"
        
        if shutil.which("nikto") or shutil.which("perl"): 
             # If perl exists, check if nikto script exists
             if os.path.exists(nikto_w_path) or os.path.exists(r"C:\Tools\Nikto\nikto.pl"):
                 nikto_exists = True
             elif shutil.which("nikto"):
                 nikto_exists = True

        return {
            "nuclei": nuclei_exists,
            "nikto": False, # Disabled
            "zap": zap_exists
        }

    def run_zap_scan(self, target):
        """
        Runs OWASP ZAP Quick Scan.
        """
        # Windows Path Check
        zap_path = r"C:\Program Files\ZAP\Zed Attack Proxy\zap.bat"
        if not os.path.exists(zap_path):
             zap_path = r"C:\Program Files\OWASP\Zed Attack Proxy\zap.bat" # Old path fallback
             if not os.path.exists(zap_path):
                 zap_path = shutil.which("zap.bat") # Try PATH
        
        # Linux Fallback
        if not zap_path:
             zap_path = "/opt/zap/zap.sh" 

        if not zap_path or not os.path.exists(zap_path) and not shutil.which("zap.bat"):
             # Last ditch check for just 'zap.sh' if on Linux/WSL
             if shutil.which("zap.sh"): zap_path = "zap.sh"
             else: return {"error": "OWASP ZAP is not installed."}

        # Normalize target
        if not target.startswith("http"):
             target = f"http://{target}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # USE ABSOLUTE PATHS for ZAP (Crucial on Windows)
        report_html = os.path.abspath(f"{self.output_dir}/zap_{timestamp}.html")
        session_path = os.path.abspath(f"{self.output_dir}/zap_session_{timestamp}")

        print(f"[*] Running OWASP ZAP Quick Scan on {target} using {zap_path}...")
        try:
            # Command: zap.bat -cmd -quickurl <target> -quickout <filename> -quickprogress
            command = [
                zap_path, 
                "-cmd", 
                "-quickurl", target, 
                "-quickout", report_html, 
                "-newsession", session_path
            ]
            
            # ZAP can take a while. 15m timeout.
            # IMPORTANT: On Windows, .bat files need shell=True or direct cmd execution
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=900,
                shell=True,
                stdin=subprocess.DEVNULL
            )
            
            return {
                "target": target,
                "tool": "zap",
                "timestamp": timestamp,
                "report_file": report_html,
                "report_filename": os.path.basename(report_html), # For easier API serving
                "raw_output": f"Scan Complete. Report generated at {report_html}. Stdout: {result.stdout[:200]}..."
            }
        except subprocess.TimeoutExpired:
             return {"error": "ZAP scan timed out after 15 minutes."}
        except Exception as e:
            return {"error": f"Execution Error: {str(e)}"}

    def run_nikto_scan(self, target):
        nikto_candidates = [
            r"C:\Tools\Nikto\nikto-master\program\nikto.pl", # Correct GitHub extraction path
            r"C:\Tools\Nikto\program\nikto.pl",
            r"C:\Tools\Nikto\nikto.pl",
            "/opt/nikto/program/nikto.pl",
            "/usr/local/bin/nikto",
            shutil.which("nikto")
        ]
        
        nikto_cmd = None
        for path in nikto_candidates:
            if path and os.path.exists(path):
                nikto_cmd = path
                break
                
        if not nikto_cmd:
            return {"error": "Nikto executable not found in /opt/nikto or PATH."}
        
        # Normalize path to fix "Invalid argument" on Windows
        nikto_cmd = os.path.normpath(nikto_cmd)

        # Normalize target for Nikto (ensure http/https if missing)
        if not target.startswith("http"):
             target = f"http://{target}"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.abspath(f"{self.output_dir}/nikto_{timestamp}.txt")
        
        print(f"[*] Running Nikto Scan on {target} using {nikto_cmd}...")
        try:
            # Run from the directory of the script to avoid path issues
            script_dir = os.path.dirname(nikto_cmd)
            script_name = os.path.basename(nikto_cmd)
            
            # Use explicit perl call
            command = ["perl", script_name, "-h", target, "-o", filename]
            
            # Set CWD to script directory
            result = subprocess.run(
                command, 
                cwd=script_dir, 
                capture_output=True, 
                text=True, 
                timeout=900, 
                stdin=subprocess.DEVNULL
            )
            
            # Look for file
            raw_output = ""
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    raw_output = f.read()
            
            # Fallback: if file is empty, verify stdout
            if not raw_output and result.stdout:
                raw_output = result.stdout
                # Try to save it to file for consistency
                with open(filename, 'w') as f:
                    f.write(raw_output)

            return {
                "target": target,
                "tool": "nikto",
                "timestamp": timestamp,
                "output_file": filename,
                "raw_output": raw_output or f"No output. Stderr: {result.stderr}"
            }
        except subprocess.TimeoutExpired:
             return {"error": "Nikto scan timed out after 5 minutes."}
        except Exception as e:
            return {"error": f"Execution Error: {str(e)}"}

    def _find_go_tool(self, tool_name):
        # Helper to find Go tools in common locations
        path = shutil.which(tool_name)
        if path: return path
        
        # Check standard Go bin
        go_bin = os.path.expanduser(r"~\go\bin")
        possible_path = os.path.join(go_bin, f"{tool_name}.exe")
        if os.path.exists(possible_path):
            return possible_path
            
        return None

    def run_nuclei_scan(self, target):
        """
        Runs a Nuclei scan on the target.
        Saves output to a JSON file in output_dir.
        """
        nuclei_path = self._find_go_tool("nuclei")
        if not nuclei_path:
            return {"error": "Nuclei is not installed on the system."}

        # Normalize target for Nuclei (ensure http/https if missing)
        # Nuclei handles bare domains well usually, but user requested explicit http://
        if not target.startswith("http"):
             target = f"http://{target}"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/nuclei_{timestamp}.json"
        
        print(f"[*] Running Nuclei Vulnerability Scan on {target} using {nuclei_path}...")
        
        try:
            # Command: nuclei -u <target> -json -o <filename>
            # -silent: Reduce noise
            # -nc: No color (easier to parse if needed)
            command = [
                nuclei_path, 
                "-u", target, 
                "-json", 
                "-o", filename,
                "-silent"
            ]
            
            # Run the command
            print(f"DEBUG: Running Nuclei command: {' '.join(command)}")
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=600,
                stdin=subprocess.DEVNULL
            )
            
            if result.returncode != 0:
                 print(f"ERROR: Nuclei failed. Stderr: {result.stderr}")
            
            # Read the results back from the file
            findings = []
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    for line in f:
                        try:
                            # Nuclei writes one JSON object per line
                            line = line.strip()
                            if line:
                                findings.append(json.loads(line))
                        except:
                            continue
            
            return {
                "target": target,
                "tool": "nuclei",
                "timestamp": timestamp,
                "output_file": filename,
                "findings_count": len(findings),
                "findings": findings # Return the raw findings list
            }
        except subprocess.TimeoutExpired:
             return {"error": "Nuclei scan timed out after 10 minutes."}
        except Exception as e:
            return {"error": f"Execution Error: {str(e)}"}
