python -m venv .venv
.\.venv\Scripts\activate.ps1
python -m pip install --upgrade pip

if (Test-Path requirements.txt) {
    python -m pip install -r requirements.txt
} else {
    Write-Host "File requirements.txt not found."
}
