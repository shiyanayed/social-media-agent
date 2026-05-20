# Check ffmpeg installation (Windows)
$ff = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ff) {
    Write-Host "ffmpeg OK:" $ff.Source -ForegroundColor Green
    ffmpeg -version | Select-Object -First 1
    exit 0
}
$search = @(
    "$env:LOCALAPPDATA\Microsoft\WinGet\Packages",
    "C:\ffmpeg\bin",
    "$env:ProgramFiles\ffmpeg\bin"
)
foreach ($root in $search) {
    if (Test-Path $root) {
        $found = Get-ChildItem -Path $root -Filter "ffmpeg.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) {
            Write-Host "ffmpeg found but not on PATH:" $found.FullName -ForegroundColor Yellow
            Write-Host "Close and reopen PowerShell, or add that folder to PATH."
            exit 0
        }
    }
}
Write-Host "ffmpeg not installed. Run: winget install Gyan.FFmpeg" -ForegroundColor Red
exit 1
