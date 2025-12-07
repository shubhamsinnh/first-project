from flask import Flask, render_template, jsonify, request, url_for, session, redirect
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.utils import secure_filename
from functools import wraps
import os
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from flask_migrate import Migrate
from datetime import datetime, timedelta

# Local imports
from database import db
from models import User, Pandit, PujaMaterial, Testimonial, Bundle, Admin, Booking

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Application configuration
app.config.update(
    SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={
        'pool_pre_ping': True,  # Verify connections before using them
        'pool_recycle': 300,    # Recycle connections after 5 minutes
        'pool_size': 10,
        'max_overflow': 20
    },
    JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY"),
    SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"),
    UPLOAD_FOLDER=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/uploads'),
    ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg', 'gif'},
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB file size limit
)

# Initialize extensions
db.init_app(app) # Initialize database
migrate = Migrate(app, db) # Initialize Flask-Migrate AFTER db
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Ensure upload directory exists
with app.app_context():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    # db.create_all()

def allowed_file(filename):
    """Check if filename has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Admin login required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def home():
    """Main landing page route"""
    try:
        return render_template(
            'home.html',
            pandits=Pandit.query.filter_by(is_approved=True).all(),  # Only show approved pandits
            materials=PujaMaterial.query.all(),
            testimonials=Testimonial.query.all(),
            bundles=Bundle.query.all()
        )
    except SQLAlchemyError as e:
        app.logger.error(f"Database error: {str(e)}")
        return jsonify({
            "error": "Database connection error. Please check your database connection.",
            "details": str(e)
        }), 500

@app.route('/api/register', methods=['POST'])
def register():
    """User registration endpoint"""
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Username and password required"}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "User already exists"}), 409

    try:
        user = User(
            username=data['username'],
            password=bcrypt.generate_password_hash(data['password']).decode('utf-8')
        )
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "User created successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User authentication endpoint"""
    data = request.get_json()
    user = User.query.filter_by(username=data.get('username')).first()

    if not user or not bcrypt.check_password_hash(user.password, data.get('password', '')):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token), 200

@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_image():
    """Secure image upload endpoint"""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return jsonify({
            "url": url_for('static', filename=f'uploads/{filename}', _external=True)
        }), 200
    
    return jsonify({"error": "Invalid file type"}), 400

@app.route("/api/pandit-ji", methods=["GET"])
@jwt_required()
def fetch_panditji():
    """Get list of available pandits (authenticated)"""
    try:
        pandits = Pandit.query.all()
        return jsonify([p.to_dict() for p in pandits]), 200
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500


@app.route('/about')
def about():
    """About Us page"""
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact Us page"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            subject = request.form.get('subject')
            message = request.form.get('message')
            
            # Here you would typically save to database or send email
            app.logger.info(f"Contact form submission from {name} ({email}): {subject}")
            
            return render_template('contact.html', success=True)
        except Exception as e:
            app.logger.error(f"Error in contact form: {str(e)}")
            return render_template('contact.html', error=str(e))
    
    return render_template('contact.html')


@app.route("/pandit-signup", methods=['GET', 'POST'])
def pandit_signup():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            age = request.form.get('age')
            email = request.form.get('email')
            phone = request.form.get('phone')
            experience = request.form.get('experience')
            languages = request.form.get('languages')
            location = request.form.get('location')
            specialties = request.form.get('specialties')

            new_pandit = Pandit(
                name=name,
                age=int(age) if age else 35,
                email=email,
                phone=phone,
                experience=experience,
                languages=languages,
                location=location,
                specialties=specialties,
                availability=True,
                is_approved=False  # Admin will approve later
            )
            
            db.session.add(new_pandit)
            db.session.commit()
            
            return render_template('pandit_signup_success.html')
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error in pandit signup: {str(e)}")
            return render_template('pandit_signup.html', error=str(e))
    
    return render_template('pandit_signup.html')


@app.route('/api/seed-data', methods=['GET'])
def seed_data():
    """Seed the database with sample data"""
    try:
        # Check if data already exists
        if Pandit.query.first() or PujaMaterial.query.first() or Testimonial.query.first() or Bundle.query.first():
            return jsonify({
                "message": "Data already exists!",
                "tip": "Visit /api/clear-data first if you want to reseed",
                "counts": {
                    "pandits": Pandit.query.count(),
                    "materials": PujaMaterial.query.count(),
                    "testimonials": Testimonial.query.count(),
                    "bundles": Bundle.query.count()
                }
            }), 200
        
        # Add Puja Materials (20+ products)
        materials = [
            PujaMaterial(name="Premium Incense Sticks Set", description="Hand-rolled traditional incense sticks made from natural ingredients. Includes sandalwood, jasmine, and rose varieties.", price=299, image_url="priest.jpeg"),
            PujaMaterial(name="Brass Diya Collection", description="Set of 5 handcrafted brass diyas with intricate designs. Traditional oil lamps perfect for festivals and daily worship.", price=599, image_url="priest1.jpeg"),
            PujaMaterial(name="Sacred Puja Thali Set", description="Complete brass puja thali with essential items including kumkum holder, rice bowl, diya, bell, and agarbatti holder.", price=1299, image_url="th.png"),
            PujaMaterial(name="Organic Camphor Tablets", description="Pure and natural camphor tablets for aarti and havan. Smokeless burning, strong fragrance. Pack of 100 tablets.", price=149, image_url="priest.jpeg"),
            PujaMaterial(name="Sandalwood Powder", description="Premium quality pure sandalwood powder for tilak, havan, and puja. 100g pack of aromatic sandalwood.", price=450, image_url="priest1.jpeg"),
            PujaMaterial(name="Rudraksha Mala 108 Beads", description="Authentic 5 Mukhi Rudraksha mala with 108 beads. Perfect for meditation, japa, and spiritual practices.", price=899, image_url="th.png"),
            PujaMaterial(name="Copper Kalash Set", description="Traditional copper kalash (pot) with coconut holder and mango leaves holder. Essential for all Hindu pujas.", price=799, image_url="priest.jpeg"),
            PujaMaterial(name="Havan Samagri Pack", description="Complete havan samagri pack with all essential herbs and ingredients. Includes guggal, camphor, ghee, and more.", price=199, image_url="priest1.jpeg"),
            PujaMaterial(name="Kumkum & Haldi Set", description="Pure kumkum and turmeric powder set in decorative containers. Perfect for tilak and puja rituals.", price=159, image_url="th.png"),
            PujaMaterial(name="Brass Bell (Ghanti)", description="Handcrafted brass temple bell with beautiful sound. Used in daily puja and aarti ceremonies.", price=399, image_url="priest.jpeg"),
            PujaMaterial(name="Silver Puja Items Set", description="Premium silver-plated puja items set including diya, incense holder, and kumkum container.", price=1899, image_url="priest1.jpeg"),
            PujaMaterial(name="Cotton Wicks (Batti)", description="Pure cotton wicks for diyas. Pack of 200 pieces. Long-lasting and smokeless burning.", price=99, image_url="th.png"),
            PujaMaterial(name="Tulsi Mala", description="Authentic Tulsi wood mala with 108 beads. Sacred for Lord Vishnu worship and meditation.", price=299, image_url="priest.jpeg"),
            PujaMaterial(name="Puja Oil (Til Tel)", description="Pure sesame oil for lighting diyas. 1 liter bottle. Traditional and long-lasting.", price=249, image_url="priest1.jpeg"),
            PujaMaterial(name="Dhoop Sticks Premium", description="Natural dhoop sticks made from cow dung, herbs, and essential oils. Pack of 50 sticks.", price=179, image_url="th.png"),
            PujaMaterial(name="Gangajal (Holy Water)", description="Authentic Ganga jal from Haridwar in sealed bottle. 500ml. Essential for all pujas.", price=99, image_url="priest.jpeg"),
            PujaMaterial(name="Panchamrit Set", description="Complete set of 5 containers for panchamrit ingredients: milk, curd, honey, sugar, ghee.", price=699, image_url="priest1.jpeg"),
            PujaMaterial(name="Bhagavad Gita Book", description="Complete Bhagavad Gita with Hindi and English translation. Hardcover edition with beautiful illustrations.", price=399, image_url="th.png"),
            PujaMaterial(name="Brass Aarti Plate", description="Decorative brass aarti thali with handles. Perfect for evening aarti and festivals.", price=549, image_url="priest.jpeg"),
            PujaMaterial(name="Shankh (Conch Shell)", description="Natural white shankh for puja and blowing during aarti. Large size, clear sound.", price=799, image_url="priest1.jpeg"),
            PujaMaterial(name="Puja Bells Set", description="Set of 3 brass bells in different sizes. Melodious sound for temple and home puja.", price=599, image_url="th.png"),
            PujaMaterial(name="Agarbatti Stand Holder", description="Beautiful brass incense stick holder with ash catcher. Decorative and functional.", price=249, image_url="priest.jpeg"),
            PujaMaterial(name="Lotus Diya Holders", description="Set of 5 lotus-shaped brass diya holders. Beautiful design for decoration and worship.", price=699, image_url="priest1.jpeg"),
            PujaMaterial(name="Puja Flowers Fresh Pack", description="Fresh flowers for daily puja including roses, marigolds, and jasmine. One day supply.", price=149, image_url="th.png"),
            PujaMaterial(name="Sacred Thread (Janeu)", description="Pure cotton sacred thread for religious ceremonies. Pack of 10 pieces.", price=129, image_url="priest.jpeg")
        ]
        
        # Add Testimonials (8 reviews)
        testimonials = [
            Testimonial(author="Priya Sharma", author_image="priest.jpeg", content="Excellent service! The pandit ji was very knowledgeable and performed the Griha Pravesh puja beautifully. The puja materials were of premium quality. Highly recommended!", rating=5, location="Mumbai, Maharashtra"),
            Testimonial(author="Rajesh Kumar", author_image="priest1.jpeg", content="Very professional and punctual. All the puja essentials arrived on time and were exactly as described. The complete ritual bundle saved me so much time and effort.", rating=5, location="Delhi, NCR"),
            Testimonial(author="Anjali Verma", author_image="th.png", content="PujaPath made our wedding ceremony stress-free. The pandit was experienced and guided us through every ritual. Thank you for preserving our traditions with such dedication!", rating=5, location="Bangalore, Karnataka"),
            Testimonial(author="Vikram Singh", author_image="priest.jpeg", content="Great platform for all puja needs. The prices are reasonable and the quality is authentic. I especially love the monthly subscription for daily puja items.", rating=5, location="Jaipur, Rajasthan"),
            Testimonial(author="Meera Patel", author_image="priest1.jpeg", content="Booked a pandit for Satyanarayan Katha and it was a wonderful experience. The pandit was knowledgeable and explained everything beautifully. Will definitely use again!", rating=5, location="Ahmedabad, Gujarat"),
            Testimonial(author="Amit Gupta", author_image="th.png", content="The quality of puja items is top-notch. Received my order within 2 days with proper packaging. Customer service is also very helpful and responsive.", rating=5, location="Pune, Maharashtra"),
            Testimonial(author="Kavita Reddy", author_image="priest.jpeg", content="Found the perfect pandit for my daughter's wedding through PujaPath. Everything was organized professionally and the ceremony was beautiful. Highly satisfied!", rating=5, location="Hyderabad, Telangana"),
            Testimonial(author="Sandeep Joshi", author_image="priest1.jpeg", content="Impressed with the variety of puja materials available. The Rudraksha mala I purchased is authentic and of excellent quality. Great initiative to preserve our culture!", rating=5, location="Kolkata, West Bengal")
        ]
        
        # Add Sample Pandits (10+ pandits)
        pandits = [
            Pandit(name="Pandit Govind Jha", experience="15+ Years", age=45, location="Delhi, NCR", availability=True, image_url="govind-jha.webp", rating=5, languages="Hindi, English, Sanskrit", email="govind.jha@pujapath.com", phone="9876543210", specialties="Wedding ceremonies, Griha Pravesh, Satyanarayan Puja", is_approved=True),
            Pandit(name="Pandit Medhansh Acharya", experience="10+ Years", age=38, location="Mumbai, Maharashtra", availability=True, image_url="medhansh-acharya.webp", rating=5, languages="Hindi, English, Marathi", email="medhansh@pujapath.com", phone="9876543211", specialties="Navratri Puja, Wedding, Havan", is_approved=True),
            Pandit(name="Pandit Pankaj Jha", experience="20+ Years", age=52, location="Bangalore, Karnataka", availability=False, image_url="pankaj-jha.webp", rating=5, languages="Hindi, English, Kannada", email="pankaj@pujapath.com", phone="9876543212", specialties="All Hindu rituals, Vedic ceremonies", is_approved=True),
            Pandit(name="Pandit Shankar Pandit", experience="12+ Years", age=42, location="Pune, Maharashtra", availability=True, image_url="shankar-pandit.webp", rating=5, languages="Hindi, English, Marathi, Sanskrit", email="shankar@pujapath.com", phone="9876543213", specialties="Ganesh Puja, Wedding, Mundan, Shradh", is_approved=True),
            Pandit(name="Pandit Rajesh Sharma", experience="18+ Years", age=48, location="Jaipur, Rajasthan", availability=True, image_url="govind-jha.webp", rating=5, languages="Hindi, English, Rajasthani", email="rajesh@pujapath.com", phone="9876543214", specialties="Durga Puja, Lakshmi Puja, Wedding", is_approved=True),
            Pandit(name="Pandit Suresh Mishra", experience="8+ Years", age=35, location="Lucknow, UP", availability=True, image_url="medhansh-acharya.webp", rating=5, languages="Hindi, English", email="suresh@pujapath.com", phone="9876543215", specialties="Satyanarayan Katha, Griha Pravesh, Havan", is_approved=True),
            Pandit(name="Pandit Vishnu Sharma", experience="25+ Years", age=58, location="Varanasi, UP", availability=True, image_url="pankaj-jha.webp", rating=5, languages="Hindi, Sanskrit, English", email="vishnu@pujapath.com", phone="9876543216", specialties="All Vedic rituals, Shradh, Mundan", is_approved=True),
            Pandit(name="Pandit Anil Tiwari", experience="14+ Years", age=44, location="Indore, MP", availability=True, image_url="shankar-pandit.webp", rating=5, languages="Hindi, English", email="anil@pujapath.com", phone="9876543217", specialties="Wedding, Engagement, Griha Pravesh", is_approved=True),
            Pandit(name="Pandit Krishna Bhatt", experience="11+ Years", age=40, location="Ahmedabad, Gujarat", availability=True, image_url="govind-jha.webp", rating=5, languages="Hindi, Gujarati, English", email="krishna@pujapath.com", phone="9876543218", specialties="Navratri Puja, Janmashtami, Wedding", is_approved=True),
            Pandit(name="Pandit Ramesh Pandey", experience="16+ Years", age=46, location="Kolkata, West Bengal", availability=False, image_url="medhansh-acharya.webp", rating=5, languages="Hindi, Bengali, English", email="ramesh@pujapath.com", phone="9876543219", specialties="Durga Puja, Kali Puja, Wedding", is_approved=True),
            Pandit(name="Pandit Mahesh Joshi", experience="9+ Years", age=37, location="Hyderabad, Telangana", availability=True, image_url="pankaj-jha.webp", rating=5, languages="Hindi, Telugu, English", email="mahesh@pujapath.com", phone="9876543220", specialties="Satyanarayan Puja, Housewarming, Wedding", is_approved=True),
            Pandit(name="Pandit Deepak Upadhyay", experience="13+ Years", age=43, location="Chennai, Tamil Nadu", availability=True, image_url="shankar-pandit.webp", rating=5, languages="Hindi, Tamil, English, Sanskrit", email="deepak@pujapath.com", phone="9876543221", specialties="All Hindu ceremonies, Wedding, Shradh", is_approved=True),
            Pandit(name="Pandit Sanjay Trivedi", experience="22+ Years", age=54, location="Surat, Gujarat", availability=True, image_url="govind-jha.webp", rating=5, languages="Hindi, Gujarati, Sanskrit", email="sanjay@pujapath.com", phone="9876543222", specialties="Vedic rituals, Yagna, Wedding", is_approved=True),
            Pandit(name="Pandit Prakash Dubey", experience="7+ Years", age=33, location="Nagpur, Maharashtra", availability=True, image_url="medhansh-acharya.webp", rating=5, languages="Hindi, Marathi, English", email="prakash@pujapath.com", phone="9876543223", specialties="Griha Pravesh, Mundan, Birthday Puja", is_approved=True)
        ]
        
        # Add Ritual Bundles
        bundles = [
            Bundle(
                name="Griha Pravesh Complete Package",
                description="Everything you need for a perfect housewarming ceremony. Includes pandit booking, all puja materials, havan samagri, and decorative items.",
                image_url="priest.jpeg",
                original_price=5999,
                discounted_price=4499,
                includes="Pandit Service, Puja Thali, Havan Kund, Samagri, Flowers, Fruits"
            ),
            Bundle(
                name="Satyanarayan Puja Bundle",
                description="Complete kit for Satyanarayan Katha puja. Authentic materials curated by experienced pandits. Perfect for home celebrations and festivals.",
                image_url="priest1.jpeg",
                original_price=3499,
                discounted_price=2799,
                includes="Puja Book, Kalash Set, Prasad Items, Decorations, Photo Frame"
            ),
            Bundle(
                name="Monthly Puja Essentials Box",
                description="Subscription box with all daily puja needs delivered monthly. Includes incense, diyas, kumkum, vibhuti, and seasonal items.",
                image_url="th.png",
                original_price=999,
                discounted_price=799,
                includes="Incense Sticks, Diyas, Kumkum, Rice, Camphor, Sacred Thread"
            ),
            Bundle(
                name="Wedding Ritual Complete Set",
                description="Comprehensive package for Hindu wedding ceremonies. Experienced pandit with all required materials. Make your special day memorable.",
                image_url="priest.jpeg",
                original_price=15999,
                discounted_price=12999,
                includes="Expert Pandit, Complete Samagri, Mandap Items, Mangalsutra, Documentation"
            )
        ]
        
        # Add all items to database
        db.session.add_all(pandits)
        db.session.add_all(materials)
        db.session.add_all(testimonials)
        db.session.add_all(bundles)
        db.session.commit()
        
        return jsonify({
            "message": "Sample data seeded successfully!",
            "pandits": len(pandits),
            "materials": len(materials),
            "testimonials": len(testimonials),
            "bundles": len(bundles)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error seeding data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/book-pandit', methods=['POST'])
def book_pandit():
    """API endpoint for booking a pandit"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['pandit_id', 'name', 'phone', 'puja_type', 'date', 'address']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Here you would typically save to database
        # For now, just return success
        return jsonify({
            "success": True,
            "message": "Booking confirmed! We will contact you shortly.",
            "booking_id": "BK" + str(data['pandit_id']) + "001",
            "pandit_id": data['pandit_id'],
            "customer_name": data['name'],
            "phone": data['phone'],
            "puja_type": data['puja_type'],
            "date": data['date']
        }), 201
        
    except Exception as e:
        app.logger.error(f"Error in booking: {str(e)}")
        return jsonify({"error": "Booking failed. Please try again."}), 500


@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    """API endpoint for adding items to cart"""
    try:
        data = request.get_json()
        
        if 'product_id' not in data:
            return jsonify({"error": "Product ID required"}), 400
        
        product = PujaMaterial.query.get(data['product_id'])
        if not product:
            return jsonify({"error": "Product not found"}), 404
        
        return jsonify({
            "success": True,
            "message": "Item added to cart",
            "product": {
                "id": product.id,
                "name": product.name,
                "price": product.price
            }
        }), 200
        
    except Exception as e:
        app.logger.error(f"Error adding to cart: {str(e)}")
        return jsonify({"error": "Failed to add to cart"}), 500


@app.route('/api/checkout', methods=['POST'])
def checkout():
    """API endpoint for checkout"""
    try:
        data = request.get_json()
        
        if 'items' not in data or not data['items']:
            return jsonify({"error": "Cart is empty"}), 400
        
        # Calculate total
        total = 0
        for item in data['items']:
            product = PujaMaterial.query.get(item['id'])
            if product:
                total += product.price * item['quantity']
        
        # Here you would typically process payment and create order
        return jsonify({
            "success": True,
            "message": "Order placed successfully!",
            "order_id": "ORD" + str(int(total)),
            "total": total
        }), 201
        
    except Exception as e:
        app.logger.error(f"Error in checkout: {str(e)}")
        return jsonify({"error": "Checkout failed"}), 500


# ==================== ADMIN PANEL ROUTES ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            return redirect(url_for('admin_dashboard'))
        
        return render_template('admin_login.html', error="Invalid credentials")
    
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    return redirect(url_for('admin_login'))


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard with statistics"""
    try:
        # Get statistics
        total_pandits = Pandit.query.count()
        pending_pandits = Pandit.query.filter_by(is_approved=False).count()
        total_products = PujaMaterial.query.count()
        total_bookings = Booking.query.count()
        pending_bookings = Booking.query.filter_by(status='pending').count()
        
        # Recent bookings
        recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
        
        # Recent pandit signups
        recent_pandits = Pandit.query.order_by(Pandit.id.desc()).limit(5).all()
        
        return render_template('admin_dashboard.html',
                             total_pandits=total_pandits,
                             pending_pandits=pending_pandits,
                             total_products=total_products,
                             total_bookings=total_bookings,
                             pending_bookings=pending_bookings,
                             recent_bookings=recent_bookings,
                             recent_pandits=recent_pandits)
    except Exception as e:
        app.logger.error(f"Dashboard error: {str(e)}")
        return f"Error loading dashboard: {str(e)}", 500


@app.route('/admin/pandits')
@admin_required
def admin_pandits():
    """Manage pandits"""
    pandits = Pandit.query.order_by(Pandit.id.desc()).all()
    return render_template('admin_pandits.html', pandits=pandits)


@app.route('/admin/pandit/approve/<int:pandit_id>', methods=['POST'])
@admin_required
def approve_pandit(pandit_id):
    """Approve a pandit"""
    try:
        pandit = Pandit.query.get_or_404(pandit_id)
        pandit.is_approved = True
        db.session.commit()
        return jsonify({"success": True, "message": "Pandit approved successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/admin/pandit/reject/<int:pandit_id>', methods=['POST'])
@admin_required
def reject_pandit(pandit_id):
    """Reject/delete a pandit"""
    try:
        pandit = Pandit.query.get_or_404(pandit_id)
        db.session.delete(pandit)
        db.session.commit()
        return jsonify({"success": True, "message": "Pandit rejected successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/admin/products')
@admin_required
def admin_products():
    """Manage products"""
    products = PujaMaterial.query.all()
    return render_template('admin_products.html', products=products)


@app.route('/admin/product/add', methods=['POST'])
@admin_required
def add_product():
    """Add new product"""
    try:
        data = request.get_json()
        product = PujaMaterial(
            name=data['name'],
            description=data['description'],
            price=float(data['price']),
            image_url=data.get('image_url', 'priest.jpeg')
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({"success": True, "message": "Product added", "product": product.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    """Delete product"""
    try:
        product = PujaMaterial.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        return jsonify({"success": True, "message": "Product deleted"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/admin/bookings')
@admin_required
def admin_bookings():
    """View all bookings"""
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('admin_bookings.html', bookings=bookings)


@app.route('/api/clear-data', methods=['GET'])
def clear_data():
    """Clear all seed data (use with caution!)"""
    try:
        PujaMaterial.query.delete()
        Testimonial.query.delete()
        Bundle.query.delete()
        # Don't delete pandits as they might be real signups
        db.session.commit()
        return jsonify({"message": "Seed data cleared successfully. You can now reseed."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/admin/init', methods=['GET'])
def init_admin():
    """Initialize admin user (run once)"""
    try:
        # Check if admin already exists
        if Admin.query.first():
            return jsonify({
                "message": "Admin already exists",
                "tip": "Login at /admin/login with existing credentials"
            }), 200
        
        # Create default admin
        admin = Admin(
            username="admin",
            email="admin@pujapath.com",
            is_super_admin=True
        )
        admin.set_password("admin123")  # Change this password!
        
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Admin created successfully!",
            "credentials": {
                "username": "admin",
                "password": "admin123"
            },
            "login_url": "/admin/login",
            "warning": "⚠️ Please change this password immediately after first login!"
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=os.getenv("FLASK_DEBUG", False))

