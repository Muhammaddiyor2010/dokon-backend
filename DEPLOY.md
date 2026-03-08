# Backend Deploy Guide (Docker'siz)

## 1. Production `.env` tayyorlash

`.env.production.example` dan nusxa oling:

```bash
cp .env.production.example .env.production
```

Keyin quyidagilarni to'g'ri to'ldiring:

- `ENVIRONMENT=production`
- `SECRET_KEY` (kamida 32 belgili random qiymat)
- `ADMIN_PASSWORD` (kuchli parol)
- `FRONTEND_URL` va/yoki `CORS_ORIGINS`
- `TRUSTED_HOSTS` (masalan: `api.example.com`)
- `DOCS_ENABLED=false`
- `SEED_CATALOG_ON_STARTUP=false`

`SECRET_KEY` yaratish:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 2. Serverda ishga tushirish (Linux/macOS)

```bash
cd Backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.production .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

## 3. Serverda ishga tushirish (Windows PowerShell)

```powershell
cd Backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.production .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

## 4. Health check

```bash
curl http://localhost:8000/health
```

## 5. Muhim eslatmalar

- `ENVIRONMENT=production` bo'lsa, default `SECRET_KEY` yoki `ADMIN_PASSWORD` bilan app ishga tushmaydi.
- SQLite ishlatilgani uchun `market.db` ni serverda persistent diskda saqlang.
- HTTPS uchun reverse proxy (Nginx/Caddy) ortida ishlatish tavsiya etiladi.
