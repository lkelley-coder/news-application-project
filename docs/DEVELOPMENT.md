# News 4 U: development, database, testing, and operations

## Supported environment

- Windows PowerShell instructions are used below.
- Python 3.13 is the development interpreter used for the current implementation.
- Django 5.2 and Django REST Framework are installed from `requirements.txt`.
- MariaDB is the target database. SQLite can be used for a quick isolated
  development/test run.

## Find the Django project root

Run every command from the `news_application_project` folder, which contains
`manage.py`:

```powershell
Set-Location 'C:\path\to\news_application_project'
```

## Install and run

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

The provided `.env.example` selects MariaDB. To use SQLite for a quick demo,
set `DB_ENGINE=sqlite` in `.env`; otherwise configure MariaDB as described
below. If `.env` already exists, do not overwrite it. Keep its contents
private. Then run:

```powershell
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Browse <http://127.0.0.1:8000/>. The Django admin lives at
<http://127.0.0.1:8000/admin/>.

## MariaDB configuration

Create an application database and a dedicated local account in MariaDB:

```sql
CREATE DATABASE news_application
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'news_app'@'127.0.0.1'
  IDENTIFIED BY 'replace-with-a-strong-password';
GRANT ALL PRIVILEGES ON news_application.*
  TO 'news_app'@'127.0.0.1';
FLUSH PRIVILEGES;
```

Set these entries in `.env`:

```dotenv
DB_ENGINE=mysql
DB_NAME=news_application
DB_USER=news_app
DB_PASSWORD=replace-with-a-strong-password
DB_HOST=127.0.0.1
DB_PORT=3306
```

Apply migrations and verify the active connection:

```powershell
python manage.py migrate
python manage.py shell -c "from django.db import connection; c=connection.cursor(); c.execute('SELECT VERSION(), DATABASE()'); print(c.fetchone())"
```

The expected database name is `news_application`; the version should contain
`MariaDB`. The driver is `mysqlclient`, and Django uses its MySQL backend for
MariaDB.

### Run tests on MariaDB

Django creates a separate `test_news_application` database for tests. For a
restricted application account, create and grant its test database once using
a MariaDB administrator account:

```sql
CREATE DATABASE test_news_application
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON test_news_application.*
  TO 'news_app'@'127.0.0.1';
FLUSH PRIVILEGES;
```

Then run:

```powershell
python manage.py test --keepdb
```

`--keepdb` reuses the named test database on later runs. Do not point the test
database name at the real `news_application` database. Tests create/delete test
records and must never run against production data.

For an isolated SQLite test run without changing `.env`:

```powershell
$env:DB_ENGINE = 'sqlite'
python manage.py test
Remove-Item Env:DB_ENGINE
```

## Create roles and publications

Everything can be done on the website:

1. Users register at `/accounts/register/` and choose Reader, Journalist, or
   Editor.
2. An Editor opens **Publishers** > **Create publisher** (`/publishers/create/`)
   and selects the affiliated editors and journalists.
3. Editors later change membership with **Manage members**.
4. Readers subscribe from `/subscriptions/`.

A superuser (`python manage.py createsuperuser`) is only needed for the optional
Django admin at `/admin/`, e.g. to correct data or reset accounts.
## Email and approval integration

The default email backend is Django's console backend. This is suitable for
local development: message content appears in the server terminal.

To enable SMTP, use private `.env` values:

```dotenv
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DEFAULT_FROM_EMAIL=news@example.com
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=replace-with-provider-username
EMAIL_HOST_PASSWORD=replace-with-provider-secret
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
```

Use either TLS or SSL, not both. Provider credentials, app passwords, and
internal API keys must remain private.

Approval logging defaults to:

```dotenv
APPROVED_ARTICLES_API_URL=http://127.0.0.1:8000/api/approved/
APPROVED_API_TIMEOUT=5
INTERNAL_API_KEY=replace-with-a-long-random-value
```

The configured endpoint is intentionally local to the project. It does not
send approved article content to an external news provider.

## Tests and quality checks

From the Django root:

```powershell
python manage.py test
python manage.py check
python manage.py makemigrations --check --dry-run
```

Tests cover roles, website workflows, API authorization, subscription filters,
article/newsletter CRUD, and approval email/API integrations with mocks. The
test runner creates an isolated database; it does not alter the normal
development database.

There are no model changes in the site-workflow forms/views, so these additions
do not require new migrations.

## Deployment checklist

Before any public deployment:

- Set `DJANGO_DEBUG=false`.
- Set a unique `DJANGO_SECRET_KEY`; do not use the development fallback.
- Set exact production `DJANGO_ALLOWED_HOSTS`.
- Keep the site behind HTTPS. With debug disabled, HTTPS redirects, secure
  session/CSRF cookies, and HSTS default to enabled; verify behavior behind
  reverse proxies before overriding them.
- Use strong, least-privilege database credentials and private SMTP credentials.
- Rotate `INTERNAL_API_KEY` to a separate random production value.
- Configure backups, database maintenance, logging, and a production
  WSGI/ASGI server; do not use Django's development `runserver`.
- Enable HSTS preload only after confirming every relevant domain/subdomain is
  permanently HTTPS-ready and meets the preload requirements.

## Troubleshooting

| Symptom | Likely fix |
| --- | --- |
| `manage.py` not found | Change directory to the `news_application_project` folder. |
| `mariadb` is not recognized | Add the MariaDB `bin` folder to PowerShell's PATH, or call `mariadb.exe` by full path. |
| Database connection refused | Confirm MariaDB is running, listening on configured host/port, and `.env` uses the matching DB credentials. |
| `Access denied` from MariaDB | Check the exact database username/host pair; `news_app`@`127.0.0.1` differs from `news_app`@`localhost`. |
| Test DB create permission error | Create/grant the dedicated `test_news_application` DB as described above and rerun with `--keepdb`. |
| Static CSS returns 404 | Confirm the `static/news/site.css` file exists and `STATICFILES_DIRS` points at the project's `static/` directory. |
| `Forbidden (403)` after signing in another tab | Reload the login form; Django rotates CSRF tokens after authentication. |
| Subscriber email is not delivered | The console backend only prints it. Configure SMTP and test with a real provider in a controlled environment. |
