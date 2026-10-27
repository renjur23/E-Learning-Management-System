# CourseCloud - E-Learning Management System

CourseCloud is a Django learning platform where students can explore courses, manage their cart, pay through Razorpay, and access enrolled lessons. Instructors can organise course modules and lessons, while learners manage their profiles and purchase history through a responsive interface.

## Features

- Course discovery and search with detailed course pages.
- Student and instructor accounts, profile editing, and Google sign-in integration.
- Shopping cart, checkout, and free course enrolment.
- Razorpay order creation, payment verification, and signed webhooks.
- Enrolled course access and purchase history.
- Local demo payment mode for development.

## Screenshots

The screenshots below show the current minimal green interface on desktop and mobile. They use fictional demo accounts and sample courses.

### Explore courses
![Course catalogue](docs/screenshots/courses.png)

### Course details
![Course overview and enrolment](docs/screenshots/course-details.png)

### Shopping cart
![Shopping cart](docs/screenshots/shopping-cart.png)

### Checkout
![Checkout and order summary](docs/screenshots/checkout.png)

### Profile and account menu
![Profile settings and account menu](docs/screenshots/profile.png)

### Mobile previews

| Course catalogue | Course details |
| --- | --- |
| ![Mobile course catalogue](docs/screenshots/courses-mobile.png) | ![Mobile course details](docs/screenshots/course-details-mobile.png) |

| Shopping cart | Checkout | Profile |
| --- | --- | --- |
| ![Mobile shopping cart](docs/screenshots/shopping-cart-mobile.png) | ![Mobile checkout](docs/screenshots/checkout-mobile.png) | ![Mobile profile](docs/screenshots/profile-mobile.png) |

## Run locally

Built with Python, Django, SQLite, HTML, CSS, and JavaScript.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set a unique `SECRET_KEY` in `.env`. Use `DEBUG=True` for local development. Add your Razorpay test keys for payment testing, or set `PAYMENT_DEMO=True` to try the local simulation without charging money.

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Open http://127.0.0.1:8000/. Create an administrator with `manage.py createsuperuser` to manage course records.

See [the setup and integration notes](README_REDESIGN.md) for Razorpay webhook configuration and deployment details. Keep `.env` and API secrets out of version control.
