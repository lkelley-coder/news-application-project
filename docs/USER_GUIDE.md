# News 4 U: user guide

## Sign in and registration

- Open <http://127.0.0.1:8000/> while the development server is running.
- Use **Join** to create an account and choose a role: Reader, Journalist, or Editor.
- Sign in with a username and password using **Sign in**.
- Your role decides which pages appear in the navigation and which actions the
  server allows.
- **Sign out** ends the current browser session.

The Django admin (<http://127.0.0.1:8000/admin/>) is optional and only for
superusers; all regular tasks are available on the website.

## Reader tasks

Readers see published articles and newsletters. The article home page shows
approved content from the reader's subscriptions; article pages outside the
reader's subscribed publications/journalists are not available to Reader-role
accounts.

1. Sign in as a Reader.
2. Select **My subscriptions** in the navigation.
3. Choose one or more publications and journalists, then save.
4. Return to **Articles** to read subscribed articles.
5. Open **Newsletters** to see journalist-curated newsletters containing
   published stories.

The API supports the same subscription choices for programmatic clients.

## Journalist tasks

Journalists use the role-specific links in the main navigation:

- **Write article** opens the article submission form.
- **My articles** lists the journalist's own submissions and their publication
  status. Use **Edit** or **Delete** on a submission to manage it.
- **Create newsletter** opens a curated-newsletter form. Select only approved
  stories.
- **My newsletters** lists, edits, and deletes newsletters authored by the
  signed-in journalist.

An article submission is not published immediately. It enters the Editor
review queue. If a Journalist is affiliated with a publication, it appears as
an option when preparing that publication's content. Otherwise, submit an
independent article.

Journalists may edit or delete their own articles/newsletters, not another
journalist's work.

## Editor tasks

Editors use these navigation links:

- **Editor review** shows pending articles. Inspect the submission, use **Edit
  submission** if needed, then **Approve and publish** or **Delete**.
- **Manage articles** lists articles and provides edit/delete actions.
- **Create newsletter** allows an Editor to select a Journalist author and
  approved stories for the collection.
- **Manage newsletters** lists and manages newsletters.

Approving an article marks it published, records the approving Editor and
timestamp, emails the relevant subscribers, and posts an approval log entry to
the app's own `/api/approved/` endpoint.

## Publisher management (editors)

Publishers are created and managed on the site, not in the admin:

1. Sign in as an Editor and open **Publishers**.
2. Select **Create publisher**, enter a name and description, and tick the
   editors and journalists to affiliate. At least one editor is required, and
   you are added as an editor automatically.
3. Use **Manage members** on a publisher to rename it or add and remove
   affiliated editors and journalists. Only editors affiliated with a
   publisher can manage it.
4. **Delete** removes a publisher that has no articles.

Journalists can open **Publishers** to see their affiliations, and Readers see
the publications in **My subscriptions**. A journalist can submit articles for a
publisher only after an editor affiliates them with it.

Users' groups are synchronized from their role. The website and API independently
check roles and ownership; hiding a link is not the access-control mechanism.
## Troubleshooting

- **Sign-in gives a CSRF 403:** load a fresh login form and submit it again.
  Login rotates the browser's CSRF token, so an old form in another tab may no
  longer be valid.
- **Journalist cannot select a Publisher:** ask an editor affiliated with that publisher to add you
  under **Publishers** > **Manage members**.
- **No article appears after submission:** it is awaiting Editor approval.
- **Reader sees no articles:** check **My subscriptions**, and confirm the
  subscribed journalist/publication has approved stories.
- **Email is printed in the server terminal:** the default development
  `EMAIL_BACKEND` is the console backend, not SMTP. Configure an email provider
  before expecting real email delivery.
- **Browser cannot connect:** make sure `python manage.py runserver` is running
  in the Django project folder and use <http://127.0.0.1:8000/>.
