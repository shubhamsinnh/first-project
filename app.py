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
            pandits=Pandit.query.all(),
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
        # Clear existing data (optional - remove if you want to keep existing data)
        # PujaMaterial.query.delete()
        # Testimonial.query.delete()
        # Bundle.query.delete()
        
        # Check if data already exists
        if Pandit.query.first() or PujaMaterial.query.first() or Testimonial.query.first() or Bundle.query.first():
            return jsonify({"message": "Data already exists! Clear database first if you want to reseed."}), 200
        
        # Add Puja Materials
        materials = [
            PujaMaterial(
                name="Premium Incense Sticks Set",
                description="Hand-rolled traditional incense sticks made from natural ingredients. Includes sandalwood, jasmine, and rose varieties. Perfect for daily puja and meditation.",
                price=299,
                image_url="priest.jpeg"
            ),
            PujaMaterial(
                name="Brass Diya Collection",
                description="Set of 5 handcrafted brass diyas with intricate designs. Traditional oil lamps perfect for festivals and daily worship. Long-lasting and eco-friendly.",
                price=599,
                image_url="priest1.jpeg"
            ),
            PujaMaterial(
                name="Sacred Puja Thali Set",
                description="Complete brass puja thali with essential items including kumkum holder, rice bowl, diya, bell, and agarbatti holder. Ideal for all Hindu rituals.",
                price=1299,
                image_url="th.png"
            ),
            PujaMaterial(
                name="Organic Camphor Tablets",
                description="Pure and natural camphor tablets for aarti and havan. Smokeless burning, strong fragrance. Pack of 100 tablets for long-lasting use.",
                price=149,
                image_url="priest.jpeg"
            )
        ]
        
        # Add Testimonials
        testimonials = [
            Testimonial(
                author="Priya Sharma",
                author_image="priest.jpeg",
                content="Excellent service! The pandit ji was very knowledgeable and performed the Griha Pravesh puja beautifully. The puja materials were of premium quality. Highly recommended!",
                rating=5,
                location="Mumbai, Maharashtra"
            ),
            Testimonial(
                author="Rajesh Kumar",
                author_image="priest1.jpeg",
                content="Very professional and punctual. All the puja essentials arrived on time and were exactly as described. The complete ritual bundle saved me so much time and effort.",
                rating=5,
                location="Delhi, NCR"
            ),
            Testimonial(
                author="Anjali Verma",
                author_image="th.png",
                content="PujaPath made our wedding ceremony stress-free. The pandit was experienced and guided us through every ritual. Thank you for preserving our traditions with such dedication!",
                rating=5,
                location="Bangalore, Karnataka"
            ),
            Testimonial(
                author="Vikram Singh",
                author_image="priest.jpeg",
                content="Great platform for all puja needs. The prices are reasonable and the quality is authentic. I especially love the monthly subscription for daily puja items.",
                rating=4,
                location="Jaipur, Rajasthan"
            )
        ]
        
        # Add Sample Pandits
        pandits = [
            Pandit(
                name="Pandit Govind Jha",
                experience="15+ Years",
                age=45,
                location="Delhi, NCR",
                availability=True,
                image_url="govind-jha.webp",
                rating=5,
                languages="Hindi, English, Sanskrit",
                email="govind.jha@pujapath.com",
                phone="9876543210",
                specialties="Wedding ceremonies, Griha Pravesh, Satyanarayan Puja",
                is_approved=True
            ),
            Pandit(
                name="Pandit Medhansh Acharya",
                experience="10+ Years",
                age=38,
                location="Mumbai, Maharashtra",
                availability=True,
                image_url="medhansh-acharya.webp",
                rating=5,
                languages="Hindi, English, Marathi",
                email="medhansh@pujapath.com",
                phone="9876543211",
                specialties="Navratri Puja, Wedding, Havan",
                is_approved=True
            ),
            Pandit(
                name="Pandit Pankaj Jha",
                experience="20+ Years",
                age=52,
                location="Bangalore, Karnataka",
                availability=False,
                image_url="pankaj-jha.webp",
                rating=5,
                languages="Hindi, English, Kannada",
                email="pankaj@pujapath.com",
                phone="9876543212",
                specialties="All Hindu rituals, Vedic ceremonies",
                is_approved=True
            ),
            Pandit(
                name="Pandit Shankar Pandit",
                experience="12+ Years",
                age=42,
                location="Pune, Maharashtra",
                availability=True,
                image_url="shankar-pandit.webp",
                rating=5,
                languages="Hindi, English, Marathi, Sanskrit",
                email="shankar@pujapath.com",
                phone="9876543213",
                specialties="Ganesh Puja, Wedding, Mundan, Shradh",
                is_approved=True
            )
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


@app.route('/admin/init', methods=['GET'])
def init_admin():
    """Initialize admin user (run once)"""
    try:
        # Check if admin already exists
        if Admin.query.first():
            return jsonify({"message": "Admin already exists"}), 400
        
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
            "message": "Admin created successfully",
            "username": "admin",
            "password": "admin123",
            "warning": "Please change this password immediately!"
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=os.getenv("FLASK_DEBUG", False))

