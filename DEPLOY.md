# Backend Deploy Guide

## 1. Production `.env` tayyorlash

`.env.production.example` dan nusxa oling:

```bash
cp .env.production.example .env.production
```

Keyin quyidagilarni albatta to'g'ri to'ldiring:

- `ENVIRONMENT=production`
- `SECRET_KEY` (kamida 32 belgili random qiymat)
- `ADMIN_PASSWORD` (strong parol)
- `FRONTEND_URL` va/yoki `CORS_ORIGINS`
- `TRUSTED_HOSTS` (masalan: `api.example.com`)
- `DOCS_ENABLED=false`
- `SEED_CATALOG_ON_STARTUP=false`

`SECRET_KEY` yaratish uchun:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 2. Docker bilan ishga tushirish (tavsiya etiladi)

```bash
docker compose up -d --build
```

Tekshirish:

```bash
docker compose ps
curl http://localhost:8000/health
```

## 3. Docker'siz serverda ishga tushirish

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

Windows uchun activate:

```bash
.venv\Scripts\activate
```

## 4. Muhim eslatmalar

- `ENVIRONMENT=production` bo'lsa, default `SECRET_KEY` yoki `ADMIN_PASSWORD` bilan app ishga tushmaydi.
- SQLite faylini saqlash uchun volume yoki alohida persistent disk ishlating.
- Reverse proxy (Nginx/Caddy) ortida HTTPS bilan ishlatish tavsiya etiladi.
