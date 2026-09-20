<#
.SYNOPSIS
  Publishes a release asset to GitHub Releases using GitHub CLI (gh).

.DESCRIPTION
  release-push.ps1
  Auto-detects version from constants.py (or accepts version parameter),
  commits changes, pushes to main, tags the release, and creates/uploads
  the release asset via 'gh release'.

.PARAMETER ReleaseFile
  Path to the release binary/artifact (default: Releases\BubbleArena.exe or dist\BubbleArena.exe).

.PARAMETER Version
  Release version string (e.g. 1.0.0). Auto-detected if omitted.

.EXAMPLE
  .\release-push.ps1
  .\release-push.ps1 -ReleaseFile "Releases\BubbleArena.exe"
  .\release-push.ps1 -ReleaseFile "Releases\BubbleArena.exe" -Version "1.0.0"
#>

[CmdletBinding()]
param(
    [Parameter(Position=0)]
    [string]$ReleaseFile = "",

    [Parameter(Position=1)]
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"

# Auto-locate release file if not specified
if ([string]::IsNullOrWhiteSpace($ReleaseFile)) {
    if (Test-Path "Releases\BubbleArena.exe") {
        $ReleaseFile = "Releases\BubbleArena.exe"
    } elseif (Test-Path "dist\BubbleArena.exe") {
        $ReleaseFile = "dist\BubbleArena.exe"
    } else {
        Write-Error "Release file not specified and neither Releases\BubbleArena.exe nor dist\BubbleArena.exe found."
        exit 1
    }
}

if (-not (Test-Path $ReleaseFile)) {
    Write-Error "Release file not found: $ReleaseFile"
    exit 1
}

# Auto-detect version if not supplied
if ([string]::IsNullOrWhiteSpace($Version)) {
    if (Test-Path "constants.py") {
        $matched = Select-String -Path "constants.py" -Pattern 'VERSION\s*=\s*["'']([^"'']+)["'']'
        if ($matched -and $matched.Matches.Groups.Count -gt 1) {
            $Version = $matched.Matches.Groups[1].Value.Trim()
        }
    }
    if ([string]::IsNullOrWhiteSpace($Version)) {
        try {
            $Version = (python -c "import constants; print(constants.VERSION)" 2>$null).Trim()
        } catch {}
    }
}

if ([string]::IsNullOrWhiteSpace($Version)) {
    Write-Error "Could not determine version. Please specify it explicitly: .\release-push.ps1 -ReleaseFile `"$ReleaseFile`" -Version 1.0.0"
    exit 1
}

$Tag = "v$Version"

Write-Host "File:    $ReleaseFile"
Write-Host "Version: $Version"
Write-Host "Tag:     $Tag"

# Locate GitHub CLI executable
$ghCmd = Get-Command gh -ErrorAction SilentlyContinue
if (-not $ghCmd) {
    if (Test-Path "C:\Program Files\GitHub CLI\bin\gh.exe") {
        $ghExe = "C:\Program Files\GitHub CLI\bin\gh.exe"
    } elseif (Test-Path "C:\Program Files\GitHub CLI\gh.exe") {
        $ghExe = "C:\Program Files\GitHub CLI\gh.exe"
    } else {
        Write-Error "GitHub CLI ('gh') was not found in PATH or standard installation folders. Please install it (e.g. winget install GitHub.cli) and run 'gh auth login'."
        exit 1
    }
} else {
    $ghExe = "gh"
}

# Check GitHub CLI authentication
$null = cmd.exe /c "`"$ghExe`" auth status >nul 2>&1"
if ($LASTEXITCODE -ne 0) {
    Write-Error "GitHub CLI is not authenticated. Please run 'gh auth login' or provide a GH_TOKEN environment variable."
    exit 1
}

# Stage and commit repository updates if any
git add .
$null = cmd.exe /c "git diff --cached --quiet"
if ($LASTEXITCODE -ne 0) {
    git commit -m "Release $Tag"
}

# Push main
Write-Host "Pushing main to origin..."
git push origin main

# Tag and push tag
Write-Host "Tagging $Tag..."
git tag -f "$Tag"
git push origin "$Tag" --force

# Upload to GitHub Releases
Write-Host "Publishing release via GitHub CLI..."
$releaseExists = $false
$null = cmd.exe /c "`"$ghExe`" release view `"$Tag`" >nul 2>&1"
if ($LASTEXITCODE -eq 0) {
    $releaseExists = $true
}

if ($releaseExists) {
    & $ghExe release upload "$Tag" "$ReleaseFile" --clobber
} else {
    & $ghExe release create "$Tag" "$ReleaseFile" --title "$Tag" --notes "Release $Tag"
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nRelease $Tag published successfully." -ForegroundColor Green
} else {
    Write-Error "Failed to publish release with GitHub CLI."
    exit 1
}
