# Lentech Nexus

A collaboration platform where builders share ideas, publish projects, and find
people to build with.

- **Backend:** Django 6 + Django REST Framework (session auth, OpenAPI docs)
- **Frontend:** React 19 + TypeScript + Vite + React Router

## Repository layout

```
lentech_project/
├── lentech-nexus-backend/    # Django project (config + apps)
├── lentech-nexus-frontend/   # React + Vite SPA
├── .gitignore
└── README.md
```

Backend apps: `accounts` (custom user + auth), `developers` (profiles),
`projects` (projects, members, join requests), `ideas` (ideas + interest),
`core` (shared permissions, pagination, throttling, storage).

## Prerequisites

- Python 3.12+ (developed on 3.14)
- Node.js 20+ (developed on 22)
- Optional: PostgreSQL 14+, a Cloudinary account

## Backend

```powershell
cd lentech-nexus-backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

copy .env.example .env      # then edit values

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- API root: http://127.0.0.1:8000/api/
- Swagger UI: http://127.0.0.1:8000/api/docs/
- ReDoc: http://127.0.0.1:8000/api/redoc/

Run the test suite:

```powershell
python manage.py test
```

### Configuration

All configuration is environment driven (see `.env.example`).

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Django secret (required in production) |
| `DJANGO_DEBUG` | `True` for local development |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts |
| `DB_ENGINE` | `sqlite` (default) or `postgres` |
| `DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT` | PostgreSQL connection |
| `CORS_ALLOWED_ORIGINS` | Frontend origins allowed to call the API |
| `CSRF_TRUSTED_ORIGINS` | Origins trusted for CSRF |
| `CLOUDINARY_ENABLED` | Enables live profile-image uploads |
| `CLOUDINARY_CLOUD_NAME`/`CLOUDINARY_API_KEY`/`CLOUDINARY_API_SECRET` | Cloudinary credentials |
| `MAX_PROFILE_IMAGE_MB` | Max upload size |
| `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SECURE_HSTS_SECONDS` | Production hardening |

**PostgreSQL:** set `DB_ENGINE=postgres` and fill the `DB_*` values, then run
`python manage.py migrate`.

**Image uploads:** uploads are disabled while `CLOUDINARY_ENABLED=False` (the
upload endpoint returns `503`). Set the flag and credentials to enable them. All
Cloudinary access is isolated behind `core/services/storage.py`.

## Frontend

```powershell
cd lentech-nexus-frontend
npm install

copy .env.example .env      # optional, see below

npm run dev        # dev server at http://localhost:5173
npm run build      # type-check + production build
npm run lint
npm test           # Vitest + Testing Library
```

Optional `lentech-nexus-frontend/.env`:

```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

The frontend talks to the API with `fetch` using `credentials: 'include'` and
sends the `X-CSRFToken` header on unsafe methods.

## Authentication

The API uses Django session authentication:

- Sessions are stored in an **HttpOnly** cookie.
- The CSRF cookie is readable by JavaScript; the SPA reads it and sends it back
  in the `X-CSRFToken` header on unsafe requests.
- `GET /api/auth/csrf/` establishes the CSRF cookie before the first write.

## API overview

| Area | Endpoints |
| --- | --- |
| Auth | `POST /api/auth/register/`, `login/`, `logout/`, `password/`; `GET/PATCH /api/auth/me/`; `GET /api/auth/csrf/` |
| Developers | `/api/developers/`, `/api/developers/me/`, `/api/developers/me/photo/` |
| Projects | `/api/projects/` + `join/`, `leave/`, `requests/`, `members/`, `members/<user_id>/` |
| Join requests | `/api/join-requests/<id>/` + `approve/`, `reject/` |
| Ideas | `/api/ideas/` + `interest/`, `interests/` |

## Deployment notes

1. Set `DJANGO_DEBUG=False`, a strong `DJANGO_SECRET_KEY`, and real
   `DJANGO_ALLOWED_HOSTS`.
2. Point `DB_*` at PostgreSQL and run `python manage.py migrate`.
3. Enable HTTPS hardening (`DJANGO_SECURE_SSL_REDIRECT=True`,
   `DJANGO_SECURE_HSTS_SECONDS=31536000`).
4. Add the deployed frontend origin to `CORS_ALLOWED_ORIGINS` and
   `CSRF_TRUSTED_ORIGINS`.
5. Build the frontend with `npm run build` and serve `dist/` from a static host
   or CDN.
6. Configure Cloudinary credentials to enable profile-image uploads.
