$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
& .\.venv\Scripts\pyinstaller.exe --noconfirm --clean --onefile --windowed --name FootprintCleaner footprint_cleaner.py
Write-Host "Built: $PSScriptRoot\dist\FootprintCleaner.exe"
