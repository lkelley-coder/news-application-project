# News 4 U

News 4 U is a Django news application for readers, independent journalists,
editors, and curated publications. Every workflow is available through the
website; the Django admin is optional and only needed for superuser tasks.

- Readers browse published stories and newsletters and subscribe to
  publications and individual journalists.
- Journalists submit articles, manage their own work, and create newsletters.
- Editors review and approve articles, manage articles and newsletters, and
  create and manage publishers and their affiliated editors and journalists.
- Approving an article emails subscribers and logs the approval through this
  application's own REST API (`/api/approved/`).
- The same role and ownership rules apply to website pages and API actions.

## Documentation

- [User guide](./docs/USER_GUIDE.md): registration, roles, publishers, and
  every role's workflow on the site.
- [API reference](./docs/API_REFERENCE.md): authentication, endpoints,
  permissions, and example requests.
- [Architecture and data model](./docs/ARCHITECTURE.md): project structure,
  relationships, approval flow, and design decisions.
- [Development and operations](./docs/DEVELOPMENT.md): setup, MariaDB, email,
  testing, troubleshooting, and deployment.
- [Generated Sphinx reference](./docs/generated/index.html): browsable HTML
  documentation for application roles, models, and services.

## Quick start (Windows PowerShell)

Run these commands from this directory (the one containing `manage.py`):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
python manage.py migrate
python manage.py runserver
```

`.env.example` selects MariaDB. For a quick demo without MariaDB, set
`DB_ENGINE=sqlite` in `.env` before running `migrate`. See
[Development and operations](./docs/DEVELOPMENT.md) for the MariaDB setup.
Never overwrite an existing `.env`, and never commit it.

Open <http://127.0.0.1:8000/> and use **Join** to register. Choose a role on
the sign-up form:

| Role | What you can do |
| --- | --- |
| Reader | Subscribe to publishers/journalists and read approved stories. |
| Journalist | Write and manage your own articles and newsletters. |
| Editor | Approve articles, manage content, and manage publishers. |

## Build and run with Docker

Install and start Docker Desktop, then run these commands from the project
root:

```powershell
docker build -t news-4-u .
docker run --rm -p 8000:8000 -v news-4-u-data:/data `
  -e DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 news-4-u
```

The image uses SQLite for a self-contained demo, applies migrations on
startup, and keeps the database in the `news-4-u-data` Docker volume. Browse
<http://127.0.0.1:8000/>. For a hosted playground, add its exact host name to
`DJANGO_ALLOWED_HOSTS`; do not use a wildcard for a public deployment.

This image runs Django's development server and is for local learning and
testing, not production. Before deploying, configure a unique
`DJANGO_SECRET_KEY`, a separate random `INTERNAL_API_KEY`, `DJANGO_DEBUG=false`,
and the exact production `DJANGO_ALLOWED_HOSTS` through private environment
variables. Generate keys with Django's
`get_random_secret_key()` and Python's `secrets.token_urlsafe(32)`:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add the generated values to your ignored local `.env` or pass them as runtime
environment variables. Never put real credentials in the Dockerfile, README,
`.env.example`, or Git history.

## Try the whole workflow

1. Register an **Editor** and sign in. Open **Publishers** > **Create
   publisher**, name it, and tick the editors and journalists to affiliate.
2. Register a **Journalist**, then have the editor open **Publishers** >
   **Manage members** and tick that journalist.
3. As the journalist, use **Write article** (pick the publisher or leave it
   independent).
4. As the editor, open **Editor review** and approve the article.
5. Register a **Reader**, subscribe under **My subscriptions**, and read the
   approved story. Subscribers are emailed on approval (printed in the server
   console unless SMTP is configured).

## Tests

```powershell
python manage.py test
```

## Project layout

| Path | Purpose |
| --- | --- |
| `config/` | Settings, root URL configuration, WSGI/ASGI entry points |
| `accounts/` | Custom user and roles, registration, subscriptions, permissions |
| `publications/` | Publisher model, website management pages |
| `articles/` | Articles, newsletters, approval workflow, REST API |
| `templates/`, `static/` | Website templates and styles |
| `tests/` | Automated tests |
| `docs/` | Detailed guides |

## Security

Do not commit `.env`, database passwords, email credentials, Django secret
keys, or the internal API key. See [Development and operations](./docs/DEVELOPMENT.md)
for the deployment checklist.
