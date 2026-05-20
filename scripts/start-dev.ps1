# Start backend + frontend for local development (Windows)
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

Write-Host "Starting backend on http://localhost:8000 ..."
Start-Process powershell -ArgumentList @(
  "-NoExit", "-Command",
  "cd '$root'; python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000"
)

Start-Sleep -Seconds 2
Write-Host "Starting frontend on http://localhost:3000 ..."
Start-Process powershell -ArgumentList @(
  "-NoExit", "-Command",
  "cd '$root'; npx --yes serve frontend -p 3000"
)

Write-Host "Open http://localhost:3000 in your browser."
