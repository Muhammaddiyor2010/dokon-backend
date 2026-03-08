if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

.venv\Scripts\Activate.ps1
pip install -r requirements.txt

if (Test-Path ".env.production") {
  Copy-Item .env.production .env -Force
}

uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
