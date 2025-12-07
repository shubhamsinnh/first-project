# PujaPath - One Stop Puja Solutions Platform 🙏

A comprehensive platform connecting devotees with certified Pandits and authentic Puja materials. Book priests, purchase puja essentials, and get curated ritual bundles - all in one place!

## Features ✨

### **Customer Features:**
- **Pandit Booking System**: Beautiful modal-based booking with form validation
- **Shopping Cart**: Full-featured cart with localStorage persistence, quantity management
- **Puja Essentials Shop**: 25+ authentic puja materials with ratings and discounts
- **Ritual Bundles**: Complete ceremony packages with discount badges
- **Smooth Carousels**: Manual slide navigation for all product sections
- **Responsive Design**: Works perfectly on mobile, tablet, and desktop
- **Animated Stats**: Counting animation showing 500+ Pandits, 10K+ Customers, 50+ Cities

### **Pandit Features:**
- **Beautiful Signup Page**: Modern form with benefits sidebar
- **Application Tracking**: Success page with next steps
- **Profile Management**: Once approved, pandits appear on home page

### **Admin Panel:**
- **Secure Login**: Session-based authentication
- **Dashboard**: Statistics overview with recent activity
- **Pandit Management**: Approve/reject pandit applications
- **Product Management**: Add/delete puja materials
- **Booking Management**: View all customer bookings
- **Professional UI**: Gradient design matching main site

### **Additional Pages:**
- **About Us**: Company story, mission, vision, and values
- **Contact Us**: Contact form with multiple contact methods
- **User Authentication**: JWT-based login and registration

## Tech Stack 🛠️

- **Backend**: Flask (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Flask-JWT-Extended, Flask-Bcrypt
- **Migrations**: Alembic via Flask-Migrate
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **File Uploads**: Werkzeug secure file handling

## Setup Instructions 🚀

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd first-project
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/pujapath
JWT_SECRET_KEY=your-super-secret-key-change-this
FLASK_DEBUG=True
```

### 5. Initialize database
```bash
flask db upgrade
```

### 6. Seed sample data
Start the Flask app first:
```bash
python app.py
```

Then visit: `http://localhost:5000/api/seed-data` in your browser or use curl:
```bash
curl http://localhost:5000/api/seed-data
```

This will populate the database with:
- **14 Sample Pandits** (across 10+ cities)
- **25 Puja Materials** (incense, diyas, kalash, etc.)
- **8 Customer Testimonials** (5-star reviews)
- **4 Ritual Bundles** (wedding, griha pravesh, etc.)

### 7. Initialize Admin User
Visit this URL to create admin account:
```
http://localhost:5001/admin/init
```

This creates:
- Username: `admin`
- Password: `admin123`
- **⚠️ Change this password immediately in production!**

### 8. View the website
Open your browser and go to: `http://localhost:5001`

### 9. Access Admin Panel
Go to: `http://localhost:5001/admin/login`
- Login with credentials from step 7
- Manage pandits, products, and bookings

## Project Structure 📁

```
first-project/
├── app.py                 # Main Flask application
├── database.py           # Database configuration
├── models/               # SQLAlchemy models
│   ├── user.py
│   ├── pandit.py
│   ├── puja_materials.py
│   ├── testimonial.py
│   └── bundle.py
├── templates/            # HTML templates
│   ├── home.html
│   ├── pandit_signup.html
│   └── pandit_signup_success.html
├── static/               # Static files (images, CSS, JS)
│   ├── uploads/         # User uploaded files
│   └── pandit/          # Pandit profile images
├── migrations/           # Alembic migrations
└── requirements.txt      # Python dependencies
```

## API Endpoints 🔌

### Public Endpoints
- `GET /` - Home page (shows only approved pandits)
- `GET /about` - About Us page
- `GET /contact` - Contact Us page
- `POST /contact` - Submit contact form
- `GET /pandit-signup` - Pandit registration form
- `POST /pandit-signup` - Submit pandit registration
- `POST /api/register` - User registration
- `POST /api/login` - User authentication
- `GET /api/seed-data` - Seed sample data (development only)
- `POST /api/book-pandit` - Book a pandit
- `POST /api/cart/add` - Add item to cart
- `POST /api/checkout` - Checkout cart

### Protected Endpoints (Require JWT)
- `GET /api/pandit-ji` - Fetch all pandits
- `POST /api/upload` - Upload images

### Admin Endpoints (Require Admin Session)
- `GET /admin/login` - Admin login page
- `POST /admin/login` - Admin authentication
- `GET /admin/logout` - Admin logout
- `GET /admin/dashboard` - Admin dashboard with stats
- `GET /admin/pandits` - Manage all pandits
- `POST /admin/pandit/approve/<id>` - Approve pandit
- `POST /admin/pandit/reject/<id>` - Delete pandit
- `GET /admin/products` - Manage products
- `POST /admin/product/add` - Add new product
- `POST /admin/product/delete/<id>` - Delete product
- `GET /admin/bookings` - View all bookings
- `GET /admin/init` - Initialize admin user (run once)

## Navigation Menu 🧭

The home page includes:
- **Home** - Hero section with call-to-action buttons
- **Pandit Ji** - Browse and book verified pandits
- **Puja Essentials** - Shop for puja materials
- **Ritual Bundles** - View discounted ceremony packages
- **Join Team** - Link for pandits to sign up

## Database Models 📊

### User
- username, password (hashed)
- For customer authentication

### Pandit
- name, experience, age, location, availability
- image_url, rating, languages
- email, phone, specialties, is_approved
- Approval workflow for quality control

### PujaMaterial
- name, description, price, image_url
- Products available for purchase

### Testimonial
- author, author_image, content, rating, location
- Customer reviews and feedback

### Bundle
- name, description, image_url
- original_price, discounted_price, includes
- Complete ceremony packages

### Admin
- username, email, password_hash
- is_super_admin, created_at
- Secure admin authentication

### Booking
- pandit_id, customer_name, phone, email
- puja_type, date, address, notes, status
- Booking management system

## Contributing 🤝

This is a learning project. Feel free to fork and experiment!

## License 📄

See LICENSE file for details.

---

Made with ❤️ for preserving Vedic traditions
