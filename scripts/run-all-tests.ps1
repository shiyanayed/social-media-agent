# Run all tool tests (backend need not be running except test_api.py)
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$failed = 0

$tests = @(
  "scripts/test_research.py",
  "scripts/test_writer.py",
  "scripts/test_twitter.py",
  "scripts/test_tiktok.py",
  "scripts/test_youtube.py",
  "scripts/test_video.py"
)

foreach ($t in $tests) {
  Write-Host "`n======== $t ========" -ForegroundColor Cyan
  python $t
  if ($LASTEXITCODE -ne 0) { $failed++ }
}

Write-Host "`n======== scripts/test_api.py (needs backend on :8000) ========" -ForegroundColor Cyan
python scripts/test_api.py
if ($LASTEXITCODE -ne 0) { $failed++ }

if ($failed -gt 0) {
  Write-Host "`n$failed test(s) reported issues." -ForegroundColor Yellow
} else {
  Write-Host "`nAll tests completed." -ForegroundColor Green
}
