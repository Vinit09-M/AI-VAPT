Write-Host "🚀 Setting up Auto_VAPT for Local Windows Development..." -ForegroundColor Cyan

# 1. Install Tools with Winget
Write-Host "[*] Installing Nmap..."
winget install -e --id Insecure.Nmap

Write-Host "[*] Installing Go (Golang)..."
winget install -e --id GoLang.Go

# Note: ZAP installer might require user interaction for "Next" buttons, but ensures correct install
Write-Host "[*] Installing OWASP ZAP..."
winget install -e --id OWASP.Zap

# 2. Refresh PATH (Critical: Winget updates PATH but current shell doesn't see it)
Write-Host "[*] Refreshing Environment Variables..."
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
Write-Host "[-] New Path loaded."

# 3. Install Python Deps
Write-Host "[*] Installing Python Dependencies..."
pip install -r requirements.txt

# 3. Install Go Tools
Write-Host "[*] Installing Nuclei, Subfinder, Amass..."

# Add Go bin to current session path
$GoBin = "$env:USERPROFILE\go\bin"
$env:Path += ";$GoBin"

# Add Go bin to PERSISTENT User path (so it works after restart)
$UserPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
if ($UserPath -notlike "*$GoBin*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$GoBin", [EnvironmentVariableTarget]::User)
    Write-Host "[+] Added $GoBin to persistent User Path."
}

go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/owasp-amass/amass/v3/...@master
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

# 4. Download Nuclei Templates
Write-Host "[*] Updating Nuclei Templates..."
& "$env:USERPROFILE\go\bin\nuclei" -update-templates

Write-Host "✅ Setup Complete! Please restart your terminal to load new PATH variables." -ForegroundColor Green
Write-Host "👉 Then run: python start_all.py"
