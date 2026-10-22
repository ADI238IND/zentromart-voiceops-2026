$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$url = (Get-Content REPOSITORY_URL.txt -Raw).Trim()
if ($url -ne "https://github.com/ADI238IND/zentromart-voiceops-2026") { throw "Review the actual repository URL before publishing." }
$checkout = Join-Path $PSScriptRoot "publish-checkout"
if (Test-Path $checkout) { throw "publish-checkout already exists. Use that checkout to review and push updates, or move it aside." }
git clone $url $checkout
if ($LASTEXITCODE -ne 0) { throw "Clone failed. Sign into GitHub through Git Credential Manager or gh auth login first." }
$files = @(".gitignore", ".env.example", "README.md", "SUBMIT.md", "requirements.txt", "run.py", "app.py", "evaluate.py", "make_report.py", "package_submission.py", "setup_dataset.py", "publish_github.ps1", "src", "tests", "docs", "sample_outputs", "report.pdf", "report_notes.json", "REPOSITORY_URL.txt")
foreach ($item in $files) { Copy-Item -Path (Join-Path $PSScriptRoot $item) -Destination $checkout -Recurse -Force }
git -C $checkout add -- @files
if ($LASTEXITCODE -ne 0) { throw "Staging failed" }
git -C $checkout commit -m "Update ZentroMart VoiceOps deliverables"
if ($LASTEXITCODE -ne 0) { throw "No changes, or commit failed. Check git status in publish-checkout." }
git -C $checkout push
if ($LASTEXITCODE -ne 0) { throw "Push failed. Review the checkout; local source is preserved." }
Write-Host "Updated $url. Visibility was not changed."
