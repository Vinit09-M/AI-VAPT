Write-Host "[*] Starting Missing Tools Installation..."

# 1. Install OWASP ZAP
Write-Host "[*] Installing OWASP ZAP..."
winget install -e --id ZAP.ZAP

# 2. Install Strawberry Perl (For Nikto)
Write-Host "[*] Installing Perl (Required for Nikto)..."
winget install -e --id StrawberryPerl.StrawberryPerl

# 3. Install Nikto manually
$niktoDir = "C:\Tools\Nikto"
if (-not (Test-Path $niktoDir)) {
    Write-Host "[*] Downloading Nikto..."
    New-Item -ItemType Directory -Force -Path $niktoDir | Out-Null
    
    $url = "https://github.com/sullo/nikto/archive/refs/heads/master.zip"
    $zip = "$niktoDir\nikto.zip"
    
    Invoke-WebRequest -Uri $url -OutFile $zip
    Expand-Archive -Path $zip -DestinationPath $niktoDir -Force
    
    # Move files up one level if needed (github zip often has a nested folder)
    $nested = "$niktoDir\nikto-master"
    if (Test-Path $nested) {
        Copy-Item -Path "$nested\*" -Destination $niktoDir -Recurse -Force
    }
    
    Write-Host "[-] Nikto installed to $niktoDir"
} else {
    Write-Host "[-] Nikto already exists in $niktoDir"
}

# 4. Refresh Environment
Write-Host "[*] Refreshing Environment Variables..."
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "✅ Installation Complete!"
Write-Host "👉 Please RESTART your terminal/PC to ensure Perl works."
