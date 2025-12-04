# PujaPath - One Stop Puja Solutions Platform 🙏

A comprehensive platform connecting devotees with certified Pandits and authentic Puja materials. Book priests, purchase puja essentials, and get curated ritual bundles - all in one place!

## Features ✨

- **Pandit Booking**: Connect with verified and experienced pandits for all types of Hindu rituals
- **Puja Essentials Shop**: Purchase authentic puja materials and spiritual items
- **Ritual Bundles**: Get complete packages for specific ceremonies (Griha Pravesh, Wedding, Satyanarayan Puja, etc.)
- **User Authentication**: Secure JWT-based login and registration system
- **Pandit Signup**: Pandits can register to join the platform
- **Testimonials**: See what our delighted customers have to say

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
- 4 Sample Pandits
- 4 Puja Materials
- 4 Customer Testimonials
- 4 Ritual Bundles

### 7. View the website
Open your browser and go to: `http://localhost:5000`

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
- `GET /` - Home page
- `GET /pandit-signup` - Pandit registration form
- `POST /pandit-signup` - Submit pandit registration
- `POST /api/register` - User registration
- `POST /api/login` - User authentication
- `GET /api/seed-data` - Seed sample data (development only)

### Protected Endpoints (Require JWT)
- `GET /api/pandit-ji` - Fetch all pandits
- `POST /api/upload` - Upload images

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

### Pandit
- name, experience, age, location, availability
- image_url, rating, languages

### PujaMaterial
- name, description, price, image_url

### Testimonial
- author, author_image, content, rating, location

### Bundle
- name, description, image_url
- original_price, discounted_price, includes

## Contributing 🤝

This is a learning project. Feel free to fork and experiment!

## License 📄

See LICENSE file for details.

---

Made with ❤️ for preserving Vedic traditions
