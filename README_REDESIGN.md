# CourseCloud redesign

## Run locally

Python 3.10+ recommended. Create and activate a virtual environment, then:

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env`, set a unique SECRET_KEY, and keep DEBUG=True only for local development. On Windows use `copy .env.example .env`; on macOS/Linux use `cp .env.example .env`.

```bash
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/. Existing SQLite data is retained. Uploaded media is now under `media/` with its existing database-relative paths preserved. Do not share the database publicly if it contains personal data.

Optional integrations: configure RZP_KEY_ID/RZP_KEY_SECRET for Razorpay and client_id/secret for Google OAuth. Configure the Google redirect URI for `/accounts/google/login/callback/` and the Django Sites domain for your host. Blank payment credentials leave the cart intact and display a useful error. Live integration checks require real credentials.

## Structure and audit

- `CourseCloud/settings.py`, `urls.py`: Django 5.1.5, session authentication, SQLite, allauth, media/static configuration. Added the missing allauth dependency and root redirect; DEBUG now parses as a boolean.
- `instructor/models.py`: students/instructors, courses, categories, modules, lessons, cart, orders, support messages. No schema changes.
- `student/views.py`, `forms.py`: course discovery, authentication, purchases, lessons, contact. Fixed missing invalid-login response, mismatched contact fields, empty-course crashes and unpaid orders appearing enrolled.
- `student/templates/`: formerly mixed CDN frameworks, fake durations/ratings, coupon controls without functionality, decorative navigation and inconsistent forms. All connected pages now use one layout and local assets.
- `instructor/views.py`, `templates/`: registration and module creation are the only connected instructor screens. Existing dashboard/course-add/auth prototypes are retained as simple administration entry templates; no new dashboard routes were invented. Course creation still uses Django admin. Owners can add modules from course details.

## Design system

Local `student/static/student/app.css`: indigo #334fc4, neutral #f6f7fb background, dark #182339 text, system fonts, consistent cards and panels, 8px controls, generous spacing. Responsive navigation/grid, visible keyboard focus, skip link, labelled bound Django fields, status messages and native curriculum accordions. No UI framework, web font or icon network dependency. Videos, Google OAuth and Razorpay still require their providers.

## Behaviour changes

- Search course title/description using the existing course model.
- My learning shows distinct paid enrolments. No fabricated completion percentage: there is no progress-tracking model.
- Cart add/remove and checkout retain their existing URLs but now require CSRF-protected POST for mutations; legacy GET links redirect without changing data. Any external clients must switch those mutations to POST.
- Confirmation before cart removal; submission feedback and helpful empty states.
- Cart remains available through cancelled/failed paid checkout and is cleared for the purchased courses after verified payment. Free enrolment clears its items immediately.
- Public instructor registration no longer grants staff/superuser. Existing users are unchanged; an administrator must explicitly approve staff access. Module creation requires the instructor to own the course and now saves its formset transactionally.
- Existing Google login and Razorpay signature verification remain integrated. Test payment calls are mocked; no real charge was made.

## Verification

`python manage.py check`: passed.
`python manage.py makemigrations --check --dry-run`: no changes detected.
`python manage.py test`: seven workflow tests passed (search/pages, form errors/contact persistence, free enrolment/empty curriculum, access/cart ownership, module/lesson saving, instructor privileges, mocked paid checkout verification).
No JavaScript build or lint configuration existed. Browser visual checks could not run because Chromium download failed in this environment. Responsive CSS is implemented but needs visual review on your target browsers. External video playback, Google login and live Razorpay are not verified.

## Deployment

Use a currently supported, security-patched dependency set after compatibility testing; the original pinned Django stack is retained here. Set DEBUG=False, configure ALLOWED_HOSTS, serve collected static files and uploaded media with your web server, and use real secrets. Payment confirmation checks the provider capture status and amount. Signed webhooks reconcile payments when the browser callback is missed.


## Razorpay setup

1. Add test mode keys to `.env`: `RZP_KEY_ID`, `RZP_KEY_SECRET`, and a separate random `RZP_WEBHOOK_SECRET`. Keep secrets on the server.
2. Enable automatic payment capture in the Razorpay dashboard. Access is granted only after capture, with matching INR amount and order ID.
3. Register `https://YOUR-DOMAIN/student/payment/webhook/` in the dashboard for `payment.captured` and `order.paid`, using the same webhook secret. Local webhook testing needs a public HTTPS tunnel to port 8000.
4. Start with `.venv\Scripts\python.exe manage.py runserver`, sign in as a learner, add a paid course to the cart and continue to checkout. Test successful payment, cancellation and failure using Razorpay test mode.
5. Confirm the course appears in My learning after capture. Webhook retries are safe; cancelled or unverified payments keep the cart intact.
6. For production, replace test keys with live keys and configure the live webhook separately. Real payments require an activated Razorpay account.

Integration reference: https://razorpay.com/docs/server-integration/python/test-app/

Local demo checkout: set PAYMENT_DEMO=True and DEBUG=True in .env. Checkout then offers Complete demo payment, which creates a paid enrolment without contacting Razorpay or charging money. Disable PAYMENT_DEMO to restore real Razorpay checkout. Demo mode is disabled when DEBUG=False.
