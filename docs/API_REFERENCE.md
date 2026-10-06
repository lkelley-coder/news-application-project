# News 4 U: REST API reference

Base URL for local development: `http://127.0.0.1:8000`

The API is implemented with Django REST Framework. The browser-facing site
workflows are at `/articles/`, `/newsletters/`, and `/subscriptions/`; `/api/`
remains available to API clients and for the approval log integration.

## Authentication

Obtain a token with:

```http
POST /api/token/
Content-Type: application/json

{"username": "reader-name", "password": "your-password"}
```

Example response:

```json
{"token": "your-token-value"}
```

Send it on subsequent requests:

```http
Authorization: Token your-token-value
```

Authenticated session access is also enabled for browser/API testing. Reader
registration is public. The optional `role` field (`reader`, `journalist`, or
`editor`) selects the account role and defaults to `reader`.

## Endpoints

| Method | Path | Access | Behavior |
| --- | --- | --- | --- |
| `POST` | `/api/token/` | Public | Exchange username/password for a token. |
| `POST` | `/api/accounts/register/` | Public | Register an account; optional `role` (default `reader`). |
| `GET` | `/api/accounts/me/` | Authenticated | Return current account details and role. |
| `GET` | `/api/accounts/me/token/` | Authenticated | Return/create current account's token. |
| `PATCH` | `/api/accounts/me/subscriptions/` | Reader | Replace supplied Reader subscription lists. |
| `GET` | `/api/articles/` | Authenticated | List approved articles; Readers only receive subscribed content. |
| `POST` | `/api/articles/` | Journalist | Submit a new, unapproved article. |
| `GET` | `/api/articles/subscribed/` | Reader | List approved articles from Reader's subscriptions. |
| `GET` | `/api/articles/{id}/` | Authenticated | Retrieve a visible article. Reader detail access is subscription-filtered. |
| `PUT`, `PATCH` | `/api/articles/{id}/` | Editor or owning Journalist | Update an article. |
| `DELETE` | `/api/articles/{id}/` | Editor or owning Journalist | Delete an article. |
| `POST` | `/api/articles/{id}/approve/` | Editor | Approve and distribute an article. |
| `GET` | `/api/newsletters/` | Authenticated | List newsletters that include approved stories. |
| `POST` | `/api/newsletters/` | Journalist or Editor | Create a newsletter. Editor selects a Journalist author. |
| `GET` | `/api/newsletters/{id}/` | Authenticated | Retrieve a visible newsletter. |
| `PUT`, `PATCH`, `DELETE` | `/api/newsletters/{id}/` | Editor or owning Journalist | Manage a newsletter. |
| `GET` | `/api/publishers/` | Authenticated | List publishers and their affiliations. |
| `GET` | `/api/approved/` | Editor | Read locally recorded approval logs. |
| `POST` | `/api/approved/` | Internal API key | Record an approved article ID in the local approval log. |

List endpoints are paginated with a default page size of 20. Lists return
`count`, `next`, `previous`, and `results`.

## Example requests

### Create an independent article

```http
POST /api/articles/
Authorization: Token your-token-value
Content-Type: application/json

{
  "title": "A new report",
  "content": "The full article text."
}
```

The authenticated Journalist becomes the author. `approved`, author, and
approval metadata are server-controlled. To submit for a publication, provide
its `publisher` ID; the Journalist must be affiliated with that Publisher.

### Change a Reader's subscriptions

```http
PATCH /api/accounts/me/subscriptions/
Authorization: Token your-token-value
Content-Type: application/json

{
  "publishers": [1, 3],
  "journalists": [8, 9]
}
```

IDs are database primary keys. The supplied list replaces that subscription
type; omit a key to leave that type unchanged.

### Approve an article

```http
POST /api/articles/42/approve/
Authorization: Token editor-token
```

The response includes the number of sent email messages. If internal API
logging or email fails, the response reports an integration failure; the
article approval itself has already been saved.

### Approval log integration

The app sends the configured `APPROVED_ARTICLES_API_URL` a JSON `POST` with an
`X-Internal-API-Key` header:

```json
{
  "article_id": 42,
  "title": "A new report",
  "author": "reporter",
  "publisher": null,
  "approved": true,
  "approved_at": "2026-09-26T20:00:00+00:00"
}
```

The default URL is `http://127.0.0.1:8000/api/approved/`. The endpoint validates
that the article exists and is approved. It uses a one-to-one log row, so
repeated posts for the same article update the same log rather than duplicate
it. Configure a random `INTERNAL_API_KEY` in `.env`; do not share or commit it.

## Error behavior

- `400 Bad Request`: serializer/input validation failed (for example, invalid
  article fields or a Journalist not affiliated with a chosen Publisher).
- `401 Unauthorized`: credentials or an authentication token are missing or
  invalid.
- `403 Forbidden`: authenticated user lacks the required role, or an internal
  API key was not accepted.
- `404 Not Found`: object does not exist or is intentionally hidden from the
  requesting Reader.
- `503 Service Unavailable`: approval was saved, but an email or HTTP
  integration failed.

Use Django REST Framework's response body for field-level validation details.
