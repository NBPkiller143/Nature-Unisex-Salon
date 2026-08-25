# 🌿 Nature Unisex Salon - Full-Stack Web Application

A production-ready, full-stack website and business management application built for **Nature Unisex Salon** with Python Flask, SQLAlchemy, Jinja2 templates, and responsive modern CSS/JS.

---

## 🌟 Key Features

### Public Customer Facing:
- **Luxury Brand Experience**: Deep forest green, warm linen cream, charcoal, and champagne gold aesthetic with Cormorant Garamond & Plus Jakarta Sans typography.
- **Hero & Story**: Engaging hero banner with "Style. Care. Confidence.", brand introduction, hygiene guarantees, and unisex styling features.
- **Dynamic Services & Filterable Pricing**: Real-time filtering by client target (*Men*, *Women*, *Unisex*) and service category (*Hair*, *Skin*, *Grooming*, *Makeup*, *Spa*, *Bridal*, *Packages*).
- **Appointment Booking Engine**: Interactive reservation form with time slots, instant database capture, status tracking, and single-tap **Continue on WhatsApp** handoff.
- **WhatsApp Integration**: Dynamic WhatsApp prefill generator for booking confirmations and a persistent floating quick-chat button.
- **Interactive Portfolio Gallery**: Filterable photo grid with full-screen lightbox preview.
- **Customer Reviews & Feedback**: Client testimonial showcase and direct feedback submission form.
- **Contact & Location**: Live contact information, Google Maps directions, opening hours, and direct customer inquiry form.

### Protected Admin Portal (`/admin`):
- **Secure Authentication**: Flask-Login session management with Werkzeug SHA-256 password hashing.
- **Interactive Overview Dashboard**: Live metrics for Total Bookings, Pending, Confirmed, Completed, Active Services, and Unread Inquiries.
- **Appointments Management**: Search and filter by status (*Pending*, *Confirmed*, *Completed*, *Cancelled*), add internal notes, and chat directly with clients on WhatsApp.
- **Services Catalog CRUD**: Add, edit, delete, toggle active visibility, adjust prices, edit durations, and upload service photos.
- **Gallery Manager**: Upload high-resolution photos, assign categories, and manage showcase assets.
- **Reviews & Moderation**: Moderate incoming reviews, publish verified customer quotes, or add testimonials.
- **Inquiry Inbox**: Review messages submitted through the contact form with one-click WhatsApp replies.
- **Global Settings & Profile**: Update salon contact details, WhatsApp number, opening hours, address, Google Maps embed, and admin credentials from one place.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+ / 3.11 / 3.14, Flask 3.x, Werkzeug |
| **ORM / Database** | SQLAlchemy ORM, SQLite (local), PostgreSQL (production) |
| **Authentication** | Flask-Login, Werkzeug Security (`generate_password_hash`) |
| **Frontend** | HTML5 Semantic, CSS3 Custom Properties, Vanilla JavaScript (ES6+) |
| **Templating** | Jinja2 |
| **Production WSGI** | Gunicorn |
| **Environment** | `python-dotenv` |

---

## 🚀 Local Development Setup

### 1. Clone or Open Project Directory
```bash
cd "Nature Unisex Salon"
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
# Windows PowerShell
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```

### 5. Run the Application
```bash
python app.py
```
The application will automatically initialize the database, create all tables, seed realistic demo services, reviews, and gallery items, and launch on:
👉 **`http://127.0.0.1:5000`**

---

## 🔐 Default Admin Credentials

- **Admin Login URL:** `http://127.0.0.1:5000/admin/login`
- **Username:** `admin`
- **Password:** `Admin@Nature2026`

### Changing or Resetting the Admin Account
You can reset the admin credentials anytime via the CLI command:
```bash
python init_admin.py --username admin --password YourNewSecurePassword123 --email admin@natureunisexsalon.com
```
You can also change your password inside the Admin Portal under **Website Settings > Admin Security & Password**.

---

## ☁️ Deployment on Render (Step-by-Step)

This application is 100% deployment-ready for **Render** (or Railway / Heroku / Fly.io).

### Step 1: Push Code to GitHub / GitLab
```bash
git init
git add .
git commit -m "Initial commit of Nature Unisex Salon application"
git branch -M main
git remote add origin https://github.com/your-username/nature-unisex-salon.git
git push -u origin main
```

### Step 2: Create a Web Service on Render
1. Log in to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** &rarr; **Web Service**.
3. Connect your GitHub repository.
4. Set the following configuration:
   - **Name:** `nature-unisex-salon`
   - **Environment:** `Python 3`
   - **Region:** Choose closest to your target audience (e.g., Singapore / Frankfurt)
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`

### Step 3: Add Environment Variables in Render
In the **Environment** tab on Render, add:
- `FLASK_ENV` = `production`
- `SECRET_KEY` = *[Generate a random 32-character string]*
- `SALON_NAME` = `Nature Unisex Salon`
- `SALON_PHONE` = `+91 74837 37517`
- `SALON_WHATSAPP` = `917483737517`
- `SALON_EMAIL` = `info@natureunisexsalon.com`
- `SALON_ADDRESS` = `Nature Unisex Salon, Austin Town / Neelasandra, Bengaluru, Karnataka 560047, India`
- `ADMIN_USERNAME` = `admin`
- `ADMIN_PASSWORD` = `YourProductionAdminPassword2026`

*(Optional)* To use PostgreSQL on Render:
1. Create a free **PostgreSQL Database** on Render.
2. Copy the **Internal Database URL**.
3. Add `DATABASE_URL` in your Web Service environment variables. SQLAlchemy will automatically connect to Postgres!

### Step 4: Deploy
Click **Create Web Service**. Render will build and deploy your application live with automatic SSL/HTTPS!

---

## 📁 Project Directory Structure

```
nature-unisex-salon/
├── app.py                     # Main application factory & route controllers
├── config.py                  # Environment & database configuration
├── models.py                  # SQLAlchemy ORM models (User, Service, Appointment, etc.)
├── utils.py                   # Secure file uploads & WhatsApp link generation
├── seed_data.py               # Auto-seeding initial salon services, reviews & gallery
├── init_admin.py              # CLI utility to create or reset admin credentials
├── setup_images.py            # Local asset organizer
├── requirements.txt           # Python package dependencies
├── Procfile                   # Production WSGI process declaration for Render
├── runtime.txt                # Python runtime target
├── .env                       # Local environment variables
├── .env.example               # Environment variables template
├── instance/
│   └── salon.db               # Local SQLite database (auto-generated)
├── static/
│   ├── css/
│   │   ├── style.css          # Master public luxury stylesheet
│   │   └── admin.css          # Admin dashboard stylesheet
│   ├── js/
│   │   ├── main.js            # Public client-side scripts & lightbox
│   │   └── admin.js           # Admin modal & interactive controllers
│   ├── images/
│   │   ├── hero_salon.jpg     # Hero banner photograph
│   │   ├── about_salon.jpg    # About section photograph
│   │   ├── services/          # Individual service thumbnails
│   │   └── gallery/           # Portfolio showcase images
│   └── uploads/               # User & admin uploaded media
└── templates/
    ├── base.html              # Master public layout with nav & footer
    ├── index.html             # Homepage
    ├── about.html             # About Us page
    ├── services.html          # Filterable Services catalog
    ├── pricing.html           # Salon rate card & packages
    ├── booking.html           # Appointment reservation form
    ├── booking_confirmation.html # Appointment success & WhatsApp handoff
    ├── gallery.html           # Public photo showcase & lightbox
    ├── reviews.html           # Testimonials & review submission
    ├── contact.html           # Contact details, map & enquiry form
    ├── 404.html               # Branded 404 Not Found error page
    ├── 500.html               # Branded 500 Server Error page
    └── admin/
        ├── base.html          # Admin sidebar layout
        ├── login.html         # Secure admin login
        ├── dashboard.html     # Analytics & quick actions
        ├── appointments.html  # Appointment management & status modal
        ├── services.html      # Service catalog CRUD & pricing
        ├── gallery.html       # Media upload & manager
        ├── reviews.html       # Feedback moderation
        ├── enquiries.html     # Customer inquiry inbox
        └── settings.html      # Global salon profile & credentials
```

---

## 🌿 License & Deliverable
Designed and built for **Nature Unisex Salon**. Production-ready for client handoff and live deployment.
