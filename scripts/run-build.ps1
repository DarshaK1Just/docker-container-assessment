# PowerShell wrapper to run scripts/build.sh on Windows
# Tries WSL first, then bash on PATH, then falls back to running docker-compose directly.

$scriptPath = Join-Path -Path $PSScriptRoot -ChildPath "build.sh"

function CommandExists($cmd) {
    $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

# Try WSL first. We must call wslpath inside WSL (not in PowerShell).
if (CommandExists 'wsl') {
    Write-Host "Found WSL. Attempting to run build.sh via WSL..."
    $repoWin = (Resolve-Path $PSScriptRoot).Path
    try {
        # Use a single wsl invocation that converts the Windows path and runs the script inside WSL
        # The $(wslpath '$repoWin') is evaluated inside WSL, not by PowerShell.
        & wsl bash -lc "cd \"\$(wslpath '$repoWin')\" && ./scripts/build.sh"
        exit $LASTEXITCODE
    } catch {
        Write-Warning "WSL attempt failed: $_"
        # continue to next option
    }
}

# Next try bash on PATH (Git Bash / MSYS)
if (CommandExists 'bash') {
    Write-Host "Found bash on PATH. Running build.sh via bash..."
    try {
        & bash "$scriptPath"
        exit $LASTEXITCODE
    } catch {
        Write-Warning "bash attempt failed: $_"
    }
}

Write-Host "No working bash/WSL invocation detected. Running docker-compose directly from PowerShell as a fallback..."
try {
    docker-compose build --pull --no-cache
} catch {
    Write-Error "Failed to run docker-compose. Please install WSL or Git Bash, or run the docker-compose command manually. Error: $_"
    exit 1
}
