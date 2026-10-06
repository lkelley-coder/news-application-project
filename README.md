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
