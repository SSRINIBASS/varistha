# ==============================================================================
# Varistha One-Line Installer (Windows PowerShell)
# Open-source control plane to build, run, monitor and govern AI agents
# License: Apache-2.0
# ==============================================================================

[CmdletBinding()]
param (
    [string]$InstallDir = "$env:USERPROFILE\.varistha",
    [string]$RepoUrl = "https://github.com/SSRINIBASS/varistha.git"
)

$ErrorActionPreference = "Stop"

function Write-Info {
    param ([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param ([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warn {
    param ([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Banner {
    Write-Host @"
  __     __         _     _   _           
  \ \   / /_ _ _ __(_)___| |_| |__   __ _ 
   \ \ / / _` | '__| / __| __| '_ \ / _` |
    \ V / (_| | |  | \__ \ |_| | | | (_| |
     \_/ \__,_|_|  |_|___/\__|_| |_|\__,_|
AI Employee Control Plane for Startups
"@ -ForegroundColor Cyan
}

function Check-Prerequisites {
    Write-Info "Verifying system prerequisites..."

    # Check git
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error "git is not installed. Please install git for Windows and re-run this script."
        exit 1
    }

    # Check docker
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Warn "docker was not detected in PATH. Docker Desktop is required to run the local control plane."
    }

    # Check uv or python
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        Write-Info "Found uv package manager."
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        Write-Info "Found Python runtime."
    } else {
        Write-Warn "Neither uv nor Python 3.12+ was detected. Install uv with: powershell -c 'irm https://astral.sh/uv/install.ps1 | iex'"
    }
}

function Install-Varistha {
    if (Test-Path "$InstallDir\.git") {
        Write-Info "Existing Varistha installation found at $InstallDir. Updating..."
        git -C "$InstallDir" pull --quiet origin main 2>$null
    } else {
        Write-Info "Cloning Varistha into $InstallDir..."
        git clone --quiet "$RepoUrl" "$InstallDir"
    }

    # Setup deploy\.env
    $EnvExample = Join-Path $InstallDir "deploy\.env.example"
    $EnvFile = Join-Path $InstallDir "deploy\.env"
    if ((Test-Path $EnvExample) -and (-not (Test-Path $EnvFile))) {
        Write-Info "Generating initial deploy\.env configuration..."
        Copy-Item -Path $EnvExample -Destination $EnvFile
    }

    # Install CLI
    Write-Info "Installing varistha CLI tool..."
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        uv tool install --editable (Join-Path $InstallDir "packages\cli") --force 2>$null
    } elseif (Get-Command pip -ErrorAction SilentlyContinue) {
        pip install --editable (Join-Path $InstallDir "packages\cli") 2>$null
    }

    Write-Success "Varistha successfully installed at $InstallDir!"
}

function Show-NextSteps {
    Write-Host "`nNext Steps:" -ForegroundColor White
    Write-Host "  1. Start the local control plane:" -ForegroundColor Gray
    Write-Host "     cd $InstallDir; docker compose -f deploy/docker-compose.yml up -d" -ForegroundColor Green
    Write-Host "  2. Access the dashboard:" -ForegroundColor Gray
    Write-Host "     http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  3. Create your first agent spec:" -ForegroundColor Gray
    Write-Host "     varistha init --name my-agent" -ForegroundColor Green
    Write-Host "  4. Apply and trigger execution:" -ForegroundColor Gray
    Write-Host "     varistha apply -f agent.yaml; varistha run my-agent`n" -ForegroundColor Green
}

Write-Banner
Check-Prerequisites
Install-Varistha
Show-NextSteps
