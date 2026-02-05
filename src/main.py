import argparse
import sys
import os

# Ensure we can import modules from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.input_handler import InputHandler

def print_banner():
    print(r"""
    _   _   _ _____ ___     __  __ _    ___ _____ 
   /_\ | | | |_   _/ _ \   \ \/ /   \ | _ \_   _|
  / _ \| |_| | | || (_) |   >  <| - ||  _/ | |  
 /_/ \_\___/  |_| \___/   /_/\_\_|_||_|   |_|  
    AI-Driven Automated VAPT Framework (MVP)
    """)

def main():
    print_banner()

    parser = argparse.ArgumentParser(description="Auto_VAPT: AI-Driven Vulnerability Assessment")
    parser.add_argument("-t", "--target", help="Target Domain or IP Address to scan", required=True)
    
    args = parser.parse_args()
    
    # --- Step 1: Input Validation ---
    print(f"[*] Analyzing Target: {args.target}")
    
    input_handler = InputHandler()
    valid_target = input_handler.validate_target(args.target)
    
    if not valid_target:
        print(f"[!] Error: '{args.target}' is not a valid Domain or IP address.")
        sys.exit(1)
        
    print(f"[+] Target Type: {valid_target['type'].upper()}")
    print(f"[+] Cleaned Target: {valid_target['target']}")
    
    print("[*] Checking Connectivity...")
    if input_handler.check_connectivity(valid_target['target']):
         print(f"[+] Target is Reachable! Ready for Recon.")
         # Future: Call Recon Module here
    else:
         print(f"[!] Warning: Could not resolve '{valid_target['target']}'. Is it online?")
         sys.exit(1)

if __name__ == "__main__":
    main()
