from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import FileResponse
import sys
import os

# Ensure we can import modules from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.input_handler import InputHandler
from modules.recon import ReconScanner
from modules.scanner import VulnScanner
from modules.scanner import VulnScanner

app = FastAPI(title="Auto_VAPT API")

# Enable CORS so the React Frontend can talk to this Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TargetRequest(BaseModel):
    target: str

@app.get("/")
def read_root():
    return {"status": "Auto_VAPT Backend is Online"}

@app.post("/validate")
def validate_target_endpoint(request: TargetRequest):
    handler = InputHandler()
    
    # 1. Validate Format
    result = handler.validate_target(request.target)
    if not result:
        return {"valid": False, "message": "Invalid Domain or IP format"}
    
    # 2. Check Connectivity
    is_reachable = handler.check_connectivity(result['target'])
    
    return {
        "valid": True,
        "type": result['type'],
        "cleaned_target": result['target'],
        "reachable": is_reachable,
        "message": "Target validated successfully"
    }

@app.post("/scan")
def run_scan_endpoint(request: TargetRequest):
    """
    Triggers the Recon Module (Nmap).
    Warning: This is synchronous for MVP. Large scans will block.
    """
    scanner = ReconScanner()
    
    if not scanner.check_nmap_availability():
        return {"status": "error", "message": "Nmap is not installed on the server."}
        
    result = scanner.run_nmap_scan(request.target)
    
    if "error" in result:
        return {"status": "error", "message": result["error"]}
        
    return {"status": "success", "data": result}

@app.post("/scan/inventory")
def run_inventory_scan_endpoint(request: TargetRequest):
    """
    Step 2: Complete Recon & Asset Discovery.
    Consolidates Nmap, Subfinder, Amass, and Tech detection.
    """
    try:
        scanner = ReconScanner()
        result = scanner.get_asset_inventory(request.target)
        
        # Check for success
        if "error" in result:
            return {"status": "error", "message": result["error"]}
            
        return {"status": "success", "data": result}
    except Exception as e:
        print(f"CRITICAL ERROR in /scan/inventory: {str(e)}")
        return {"status": "error", "message": f"Internal Server Error: {str(e)}"}

@app.post("/scan/vuln")
def run_vuln_scan_endpoint(request: TargetRequest):
    """
    Step 3: Automated Vulnerability Scanner.
    Runs Nuclei and Nikto, consolidates reports.
    """
    try:
        scanner = VulnScanner()
        
        # Check tool availability (Nuclei + ZAP)
        avail = scanner.check_tools_availability()
        if not avail["nuclei"] and not avail["zap"]:
            return {"status": "error", "message": "No vulnerability scanners (Nuclei/ZAP) available."}
            
        nuclei_result = scanner.run_nuclei_scan(request.target) if avail["nuclei"] else {"error": "Nuclei not available"}
        
        # Nikto disabled by user request
        nikto_result = {"info": "Nikto scan disabled by policy."}
        
        # ZAP Re-enabled
        zap_result = scanner.run_zap_scan(request.target) if avail["zap"] else {"error": "ZAP not available"}
        
        # Consolidate findings
        findings_count = 0
        if "findings_count" in nuclei_result:
            findings_count += nuclei_result["findings_count"]
        
        # Return consolidated report info
        return {
            "status": "success", 
            "message": f"Step 3 Complete. Detected vulnerabilities and misconfigurations.",
            "findings_count": findings_count,
            "nuclei": nuclei_result,
            "nikto": nikto_result,
            "zap": zap_result
        }
    except Exception as e:
        print(f"CRITICAL ERROR in /scan/vuln: {str(e)}")
        return {"status": "error", "message": f"Internal Server Error: {str(e)}"}

@app.get("/report/{filename}")
def get_report(filename: str):
    """
    Serves the JSON report file.
    """
    file_path = os.path.join("scans", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

