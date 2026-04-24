param(
    [Parameter(Mandatory = $true)]
    [string]$Token
)

$repoRoot = (git rev-parse --show-toplevel) 2>$null
if (-not $repoRoot) {
    Write-Error "Not inside a git repository."
    exit 1
}

Set-Location $repoRoot

$dirty = git status --porcelain
if ($dirty) {
    Write-Error "Working tree not clean. Commit or stash changes first."
    exit 1
}

$tempFile = [System.IO.Path]::GetTempFileName()
try {
    Set-Content -Path $tempFile -Value ("{0}==>REMOVED_JWT" -f $Token) -Encoding ASCII

    Write-Host "Rewriting history to remove token..."
    git filter-repo --replace-text $tempFile --force

    Write-Host "Cleaning reflog and garbage collecting..."
    git reflog expire --expire=now --all
    git gc --prune=now --aggressive

    Write-Host "History rewrite complete. Next steps:"
    Write-Host "  1) git push --force --all"
    Write-Host "  2) git push --force --tags"
    Write-Host "  3) Ask collaborators to reclone or reset to the new history."
} finally {
    Remove-Item -Path $tempFile -ErrorAction SilentlyContinue
}
