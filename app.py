from flask import Flask, render_template, jsonify, request, url_for, session, redirect
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.utils import secure_filename
from functools import wraps
import os
import json
from urllib.parse import unquote
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from flask_migrate import Migrate
from datetime import datetime, timedelta
import razorpay
import threading


# Local imports
from database import db
from models import User, Pandit, PujaMaterial, Testimonial, Bundle, Admin, Booking, Order, OrderItem

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Application configuration
# Get database URL with fallback for SQLite (Windows compatibility)
database_url = os.getenv("DATABASE_URL") or "sqlite:///pujapath.db"

# Base config - engine options only for non-SQLite databases
config_dict = {
    'SQLALCHEMY_DATABASE_URI': database_url,
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
}

# Only add connection pooling for PostgreSQL/MySQL (not SQLite)
if not database_url.startswith('sqlite'):
    config_dict['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20
    }

app.config.update(
    **config_dict,
    JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY"),
    SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-key-change-in-production"),
    UPLOAD_FOLDER=os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/uploads'),
    ALLOWED_EXTENSIONS={'png', 'jpg', 'jpeg', 'gif'},
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB file size limit
)

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    raise ValueError("Razorpay keys not set in environment variables")

# Intialise Razorpay Client
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME', 'noreply@pujapath.com')

# Initialize extensions
from flask_mail import Mail, Message
mail = Mail(app)

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

# ==================== HELPER FUNCTIONS ====================

def send_booking_confirmation_email(booking, pandit):
    """Send email with ICS calendar invite attached"""
    try:
        if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
            print("WARNING: Email credentials not set. Skipping email.")
            return

        from icalendar import Calendar, Event
        import io
        from flask_mail import Message
        import random
        import string

        # Generate a mock Google Meet link
        meet_code = "-".join(["".join(random.choices(string.ascii_lowercase, k=x)) for x in [3, 4, 3]])
        meet_link = f"https://meet.google.com/{meet_code}"

        # 1. Create email object
        msg = Message(
            subject=f"Booking Confirmed: {booking.puja_type} with Pandit {pandit.name}",
            recipients=[booking.email]
        )
        
        # 2. Email Body (HTML + Plain Text Fallback)
        msg.body = f"Namaste {booking.customer_name},\n\nYour booking for {booking.puja_type} has been confirmed.\nRef: {booking.booking_number}\nDate: {booking.date.strftime('%d %B %Y')}\nGoogle Meet: {meet_link}"
        
        msg.html = f"""
        <html>
        <head>
            <script type="application/ld+json">
            {{
              "@context": "http://schema.org",
              "@type": "Event",
              "name": "PujaPath: {booking.puja_type}",
              "startDate": "{booking.date.isoformat()}",
              "endDate": "{(booking.date + timedelta(days=1)).isoformat()}",
              "location": {{
                "@type": "Place",
                "name": "{booking.address}",
                "address": {{
                  "@type": "PostalAddress",
                  "streetAddress": "{booking.address}"
                }}
              }},
              "description": "Booking {booking.booking_number} with Pandit {pandit.name}. Video Link: {meet_link}",
              "image": "https://pujapath.com/static/images/logo.png",
              "organizer": {{
                "@type": "Organization",
                "name": "PujaPath",
                "url": "https://pujapath.com"
              }},
              "eventStatus": "http://schema.org/EventScheduled",
              "eventAttendanceMode": "http://schema.org/MixedEventAttendanceMode"
            }}
            </script>
        </head>
        <body>
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0;">Booking Confirmed</h1>
            </div>
            
            <div style="padding: 20px; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 8px 8px;">
                <p>Namaste <strong>{booking.customer_name}</strong>,</p>
                
                <p>We are delighted to confirm your booking for <strong style="color: #6b46c1;">{booking.puja_type}</strong>.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #6b46c1;">
                    <h3 style="margin-top: 0; color: #4a5568;">Booking Details</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 5px 0; color: #718096;">Booking Ref:</td>
                            <td style="padding: 5px 0; font-weight: bold;">{booking.booking_number}</td>
                        </tr>
                        <tr>
                            <td style="padding: 5px 0; color: #718096;">Pandit Ji:</td>
                            <td style="padding: 5px 0; font-weight: bold;">{pandit.name} <span style="font-weight: normal; font-size: 0.9em;">({pandit.phone})</span></td>
                        </tr>
                        <tr>
                            <td style="padding: 5px 0; color: #718096;">Date:</td>
                            <td style="padding: 5px 0; font-weight: bold;">{booking.date.strftime('%d %B %Y')}</td>
                        </tr>
                        <tr>
                            <td style="padding: 5px 0; color: #718096; vertical-align: top;">Address:</td>
                            <td style="padding: 5px 0; font-weight: bold;">{booking.address}</td>
                        </tr>
                        <tr>
                            <td style="padding: 5px 0; color: #718096; vertical-align: top;">Video Link:</td>
                            <td style="padding: 5px 0; font-weight: bold;"><a href="{meet_link}" style="color: #667eea; text-decoration: none;">Join Google Meet</a></td>
                        </tr>
                    </table>
                </div>

                <p style="background-color: #e6fffa; color: #047481; padding: 10px; border-radius: 6px; font-size: 0.9em;">
                    📅 <strong>Note:</strong> We have attached a calendar invitation to this email. It will automatically add this auspicious event to your schedule.
                </p>
                
                <p style="margin-top: 30px; font-size: 0.9em; color: #718096;">
                    Om Shanti,<br>
                    <strong>The PujaPath Team</strong>
                </p>
            </div>
        </div>
        </body>
        </html>
        """
        
        # 3. Generate ICS File
        cal = Calendar()
        cal.add('prodid', '-//PujaPath//pujapath.com//')
        cal.add('version', '2.0')
        
        event = Event()
        event.add('summary', f"PujaPath: {booking.puja_type}")
        event.add('dtstart', booking.date) # All day event
        event.add('dtend', booking.date + timedelta(days=1))
        event.add('location', booking.address) # Physical location
        
        # Add Meet link to description
        description = f"Booking {booking.booking_number} with {pandit.name}. Phone: {pandit.phone}\n\nGoogle Meet Link: {meet_link}"
        event.add('description', description)
        
        # Add organizer
        event.add('organizer', 'mailto:noreply@pujapath.com')
        
        cal.add_component(event)
        
        # 4. Attach ICS to email
        # We need byte stream for attachment
        f = io.BytesIO()
        f.write(cal.to_ical())
        f.seek(0)
        
        msg.attach(
            "puja_booking.ics", 
            "text/calendar", 
            f.read()
        )
        
        # 5. Send Asynchronously
        def send_async(app_obj, message):
            with app_obj.app_context():
                try:
                    mail.send(message)
                    print(f"Email sent successfully to {message.recipients}")
                except Exception as e:
                    print(f"Error sending email async: {e}")

        email_thread = threading.Thread(target=send_async, args=(app, msg))
        email_thread.start()
        print(f"Email sending initiated in background to {booking.email}")
        
    except Exception as e:
        print(f"Error preparing email: {str(e)}")

def send_order_confirmation_email(order):
    """Send order confirmation email receipt"""
    try:
        if not app.config.get('MAIL_USERNAME'):
            print("WARNING: Email credentials not set. Skipping email.")
            return

        from flask_mail import Message
        from icalendar import Calendar, Event
        pass # To satisfy linter if needed, though imports are used below

        # Determine recipient email
        recipient_email = order.customer_email
        if not recipient_email and order.user:
            recipient_email = order.user.email
            
        if not recipient_email:
            print(f"WARNING: No email found for order {order.order_number}. Skipping.")
            return

        print(f"Preparing order confirmation email for {recipient_email}")

        # 1. Create email object
        msg = Message(
            subject=f"Order Confirmed: #{order.order_number}",
            recipients=[recipient_email]
        )
        
        items_html = ""
        events_to_attach = []

        for item in order.items:
            # Use safe access for item properties
            try:
                name = item.product_name
                price = item.product_price
                qty = item.quantity
                subtotal = item.subtotal
                
                # Check for scheduled items to generate ICS
                # Format: "Bundle Name [Date: YYYY-MM-DD, Time: Slot]"
                if "Date:" in name:
                    print(f"Found Date in product name: {name}")
                    try:
                        import re
                        # More flexible regex to catch the date
                        date_match = re.search(r"Date:\s*(\d{4}-\d{1,2}-\d{1,2})", name)
                        time_match = re.search(r"Time:\s*(.*?)(\]|$)", name)
                        
                        if date_match:
                            booking_date_str = date_match.group(1)
                            # Convert to date object for All Day event (creates better UX in calendar apps)
                            booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
                            time_slot = time_match.group(1) if time_match else "All Day"
                            
                            # Create ICS event
                            cal = Calendar()
                            cal.add('prodid', '-//PujaPath//pujapath.com//')
                            cal.add('version', '2.0')
                            
                            event = Event()
                            # Clean up name for summary
                            summary_name = name.split('[')[0].strip()
                            event.add('summary', f"PujaPath Ritual: {summary_name}")
                            event.add('dtstart', booking_date) # All day event
                            event.add('dtend', booking_date + timedelta(days=1))
                            event.add('description', f"Order #{order.order_number}\nItem: {summary_name}\nTime Slot: {time_slot}")
                            
                            cal.add_component(event)
                            events_to_attach.append({
                                "filename": f"ritual_{booking_date_str}.ics",
                                "data": cal.to_ical()
                            })
                    except Exception as e:
                        print(f"Error creating ICS for item {name}: {e}")

            except Exception as e:
                print(f"Error processing item in email: {e}")
                continue
                
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{name}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">{qty}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">₹{price}</td>
                <td style="padding: 10px; border-bottom: 1px solid #eee;">₹{subtotal}</td>
            </tr>
            """

        # Add calendar note if events are attached
        calendar_note = ""
        if events_to_attach:
            calendar_note = """
            <p style="background-color: #e6fffa; color: #047481; padding: 10px; border-radius: 6px; font-size: 0.9em; margin-top: 20px;">
                📅 <strong>Note:</strong> We have attached a calendar invitation to this email. It will automatically add this auspicious ritual to your schedule.
            </p>
            """

        msg.html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
            <div style="background-color: #f8f9fa; padding: 20px; text-align: center; border-bottom: 3px solid #ff9933;">
                <h2 style="color: #d35400; margin: 0;">Order Confirmation</h2>
                <p style="margin-top: 5px;">Thank you for your purchase!</p>
            </div>
            
            <div style="padding: 20px;">
                <p>Namaste <strong>{order.customer_name}</strong>,</p>
                <p>Your order has been confirmed and meets our quality standards. We will ship it shortly.</p>
                
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Order Number:</strong> {order.order_number}</p>
                    <p style="margin: 5px 0;"><strong>Date:</strong> {order.created_at.strftime('%d %B %Y')}</p>
                    <p style="margin: 5px 0;"><strong>Payment Status:</strong> <span style="color: green; font-weight: bold;">{order.payment_status.upper()}</span></p>
                </div>
                
                <h3>Items Ordered:</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <thead>
                        <tr style="background-color: #fcebe6;">
                            <th style="padding: 10px; text-align: left; border-bottom: 2px solid #e67e22;">Item</th>
                            <th style="padding: 10px; text-align: left; border-bottom: 2px solid #e67e22;">Qty</th>
                            <th style="padding: 10px; text-align: left; border-bottom: 2px solid #e67e22;">Price</th>
                            <th style="padding: 10px; text-align: left; border-bottom: 2px solid #e67e22;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colspan="3" style="padding: 10px; text-align: right; font-weight: bold;">Grand Total:</td>
                            <td style="padding: 10px; font-weight: bold; color: #d35400;">₹{order.total_amount}</td>
                        </tr>
                    </tfoot>
                </table>
                
                {calendar_note}
                
                <div style="margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                    <h3>Shipping Details:</h3>
                    <p>
                        {order.customer_name}<br>
                        {order.shipping_address}<br>
                        {order.city}, {order.state} - {order.pincode}<br>
                        Phone: {order.customer_phone}
                    </p>
                </div>
                
                <p style="margin-top: 40px; text-align: center; color: #7f8c8d; font-size: 0.9em;">
                    Om Shanti,<br>
                    <strong>The PujaPath Team</strong>
                </p>
            </div>
        </div>
        """
        
        # Attach ICS files
        for ics in events_to_attach:
            msg.attach(
                ics['filename'], 
                "text/calendar", 
                ics['data']
            )

        # 2. Send Asynchronously
        def send_async(app_obj, message):
            with app_obj.app_context():
                try:
                    mail.send(message)
                    print(f"Order confirmation email sent successfully to {message.recipients}")
                except Exception as e:
                    print(f"Error sending order email async: {e}")
                    
        email_thread = threading.Thread(target=send_async, args=(app, msg))
        email_thread.start()
        print(f"Order email sending initiated in background to {recipient_email}")
        
    except Exception as e:
        print(f"Error preparing order email: {str(e)}")
        import traceback
        traceback.print_exc()

@app.route("/")
def home():
    """Main landing page route"""
    try:
        return render_template(
            'home.html',
            pandits=Pandit.query.filter_by(is_approved=True).limit(4).all(),  # Limit to 4 featured pandits
            materials=PujaMaterial.query.limit(8).all(),      # Limit to 8 featured materials
            testimonials=Testimonial.query.limit(6).all(),    # Limit to 6 testimonials
            bundles=Bundle.query.limit(4).all()               # Limit to 4 featured bundles
        )
    except SQLAlchemyError as e:
        app.logger.error(f"Database error: {str(e)}")
        return jsonify({
            "error": "Database connection error. Please check your database connection.",
            "details": str(e)
        }), 500

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        
        # Check if user exists
        if User.query.filter_by(email=data.get('email')).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        if User.query.filter_by(username=data.get('username')).first():
            return jsonify({'error': 'Username already taken'}), 400
        
        # Create new user with profile data
        user = User(
            username=data.get('username'),
            email=data.get('email'),
            full_name=data.get('full_name', ''),
            phone=data.get('phone', '')
        )
        user.set_password(data.get('password'))
        
        db.session.add(user)
        db.session.commit()
        
        # Generate JWT token
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'Registration successful',
            'user': user.to_dict(),
            'access_token': access_token
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Update your `/api/login` endpoint
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        identifier = data.get('email') or data.get('username')
        
        if not identifier:
            return jsonify({'error': 'Email or username is required'}), 400
            
        # Try to find user by email OR username
        user = User.query.filter(
            (User.email == identifier) | (User.username == identifier)
        ).first()
        
        if user and user.check_password(data.get('password')):
            access_token = create_access_token(identity=str(user.id))
            
            return jsonify({
                'message': 'Login successful',
                'user': user.to_dict(),
                'access_token': access_token
            }), 200
        
        return jsonify({'error': 'Invalid email/username or password'}), 401
        
    except Exception as e:
        # Log the error for debugging: app.logger.error(f"Login error: {e}")
        return jsonify({'error': 'An internal error occurred. Please try again.'}), 500

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


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Product detail page"""
    product = PujaMaterial.query.get_or_404(product_id)
    # Get some testimonials for reviews section
    testimonials = Testimonial.query.limit(6).all()
    # Get related products (other products excluding current) - fetch 4 for display
    related_products = PujaMaterial.query.limit(4).all()
    return render_template('product_detail.html', product=product, testimonials=testimonials, related_products=related_products)



@app.route('/bundle/<int:bundle_id>')
def bundle_detail(bundle_id):
    """Bundle detail page"""
    bundle = Bundle.query.get_or_404(bundle_id)
    
    # Get related products for the "You May Also Like" section
    related_products = PujaMaterial.query.limit(4).all()
    
    # OR if you want to exclude products that might be in the bundle:
    # Get some products (excluding any that might be in the bundle)
    # You need to know how your Bundle and PujaMaterial models are related
    
    return render_template('bundle_detail.html', 
                         bundle=bundle, 
                         related_products=related_products)  # Now passing related_products


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


@app.route('/careers')
def careers():
    """Careers/Join Team page"""
    return render_template('careers.html')    


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
@jwt_required(optional=True)
def book_pandit():
    """API endpoint for booking a pandit"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['pandit_id', 'name', 'phone', 'puja_type', 'date', 'address']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Generate booking number
        booking_number = f"BOOK{datetime.now().strftime('%Y%m%d%H%M%S')}{Booking.query.count() + 1}"
        
        # Parse the date string
        from datetime import datetime as dt
        try:
            booking_date = dt.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Create booking
        booking = Booking(
            pandit_id=data['pandit_id'],
            customer_name=data['name'],
            phone=data['phone'],
            email=data.get('email', ''),
            puja_type=data['puja_type'],
            date=booking_date,
            address=data['address'],
            notes=data.get('notes', ''),
            booking_number=booking_number,
            amount=999,  # Fixed price for now
            payment_status='pending',
            status='pending'
        )
        
        # If user is logged in, associate booking with user
        user_id = get_jwt_identity()
        if user_id:
            booking.user_id = int(user_id)
        
        
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Booking created. Please proceed to payment.",
            "booking_number": booking_number,
            "booking_id": booking.id,
            "amount": booking.amount,
            "redirect_url": url_for('pandit_payment_page', booking_number=booking_number)
        }), 201
        
    except Exception as e:
        db.session.rollback()
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


@app.route('/checkout', methods=['GET', 'POST'])
def checkout_page():
    """Checkout page - display form and process order"""
    if request.method == 'GET':
        # Get cart from session or request
        cart_data = request.args.get('cart')
        if cart_data:
            try:
                cart = json.loads(unquote(cart_data))
            except:
                cart = []
        else:
            cart = []
        
        if not cart:
            return redirect(url_for('home'))
        
        # Calculate totals
        total = 0
        for item in cart:
            total += item.get('price', 0) * item.get('quantity', 1)
        
        return render_template('checkout.html', cart=cart, total=total)
    
    # POST - Process 

    try:
        data = request.form
        
        # Validate required fields
        required_fields = ['customer_name', 'customer_email', 'customer_phone', 
                          'shipping_address', 'city', 'state', 'pincode']
        for field in required_fields:
            if not data.get(field):
                return render_template('checkout.html', 
                                     error=f"Please fill in {field.replace('_', ' ')}",
                                     cart=json.loads(data.get('cart_data', '[]')),
                                     total=float(data.get('total', 0)))
        
        # Get cart items
        cart_data = data.get('cart_data')
        if not cart_data:
            return render_template('checkout.html', 
                                 error="Cart is empty",
                                 cart=[],
                                 total=0)
        
        try:
            cart = json.loads(cart_data)
        except:
            return render_template('checkout.html', 
                                 error="Invalid cart data",
                                 cart=[],
                                 total=0)
        
        if not cart:
            return render_template('checkout.html', 
                                 error="Cart is empty",
                                 cart=[],
                                 total=0)
        
        # Calculate total and validate products
        total_amount = 0
        order_items_data = []
        
        for item in cart:
            product = PujaMaterial.query.get(item.get('id'))
            if not product:
                continue
            
            quantity = item.get('quantity', 1)
            price = product.price
            subtotal = price * quantity
            total_amount += subtotal
            
            order_items_data.append({
                'product': product,
                'product_name': product.name,
                'product_price': price,
                'quantity': quantity,
                'subtotal': subtotal
            })
        
        if not order_items_data:
            return render_template('checkout.html', 
                                 error="No valid items in cart",
                                 cart=cart,
                                 total=0)
        
        # Generate order number
        order_number = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{Order.query.count() + 1}"
        
        # Create order
        order = Order(
            order_number=order_number,
            customer_name=data.get('customer_name'),
            customer_email=data.get('customer_email'),
            customer_phone=data.get('customer_phone'),
            shipping_address=data.get('shipping_address'),
            city=data.get('city'),
            state=data.get('state'),
            pincode=data.get('pincode'),
            total_amount=total_amount,
            status='pending',
            payment_status='initiated',  # In real app, integrate payment gateway
            notes=data.get('notes', '')
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data['product'].id,
                product_name=item_data['product_name'],
                product_price=item_data['product_price'],
                quantity=item_data['quantity'],
                subtotal=item_data['subtotal']
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        # Redirect to order confirmation
        return redirect(url_for('payment_page', order_number=order.order_number))
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in checkout: {str(e)}")
        return render_template('checkout.html', 
                             error=f"Checkout failed: {str(e)}",
                             cart=json.loads(data.get('cart_data', '[]')) if 'data' in locals() else [],
                             total=float(data.get('total', 0)) if 'data' in locals() else 0)


@app.route('/order-confirmation/<order_number>')
def order_confirmation(order_number):
    """Order confirmation page"""
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    return render_template('order_confirmation.html', order=order)
    # ✅ NEW: Check if payment was made
    if order.payment_status != 'paid':
        # Redirect to payment page if not paid
        return redirect(url_for('payment_page', order_number=order_number))
    
    return render_template('order_confirmation.html', order=order)


@app.route('/api/orders', methods=['POST'])
@jwt_required(optional=True)
def create_order():
    """Create a new order (supports authenticated and guest users)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['customer_name', 'customer_email', 'customer_phone', 
                          'shipping_address', 'city', 'state', 'pincode', 'cart']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        cart = data.get('cart')
        if not cart:
            return jsonify({"error": "Cart is empty"}), 400
            
        # Calculate total and validate products
        total_amount = 0
        order_items_data = []
        
        for item in cart:
            item_type = item.get('type', 'product')
            quantity = int(item.get('quantity', 1))
            schedule = item.get('schedule')
            
            if item_type == 'bundle':
                bundle = Bundle.query.get(item.get('id'))
                if not bundle:
                    continue
                
                price = bundle.discounted_price
                subtotal = price * quantity
                total_amount += subtotal
                
                product_name = bundle.name
                if schedule and schedule.get('date'):
                     product_name += f" [Date: {schedule.get('date')}, Time: {schedule.get('time', 'Any')}]"
                
                order_items_data.append({
                    'bundle_id': bundle.id,
                    'product_name': product_name,
                    'product_price': price,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
            else:
                product = PujaMaterial.query.get(item.get('id'))
                if not product:
                    continue
                
                price = product.price
                subtotal = price * quantity
                total_amount += subtotal
                
                order_items_data.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_price': price,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
        
        if not order_items_data:
            return jsonify({"error": "No valid items in cart"}), 400
        
        # Generate order number
        order_number = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{Order.query.count() + 1}"
        
        # Create order
        order = Order(
            order_number=order_number,
            customer_name=data.get('customer_name'),
            customer_email=data.get('customer_email'),
            customer_phone=data.get('customer_phone'),
            shipping_address=data.get('shipping_address'),
            city=data.get('city'),
            state=data.get('state'),
            pincode=data.get('pincode'),
            total_amount=total_amount,
            status='pending',
            payment_status='initiated',
            notes=data.get('notes', '')
        )
        
        if user_id:
            order.user_id = user_id
        
        db.session.add(order)
        db.session.flush()  # Get order ID
        
        # Create order items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data.get('product_id'),
                bundle_id=item_data.get('bundle_id'),
                product_name=item_data['product_name'],
                product_price=item_data['product_price'],
                quantity=item_data['quantity'],
                subtotal=item_data['subtotal']
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": "Order created. Please proceed to payment.",
            "order_number": order_number,
            "redirect_url": url_for('payment_page', order_number=order_number)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in create_order: {str(e)}")
        return jsonify({"error": str(e)}), 500

#Razorpay Payment Create

@app.route('/api/payment/create', methods=['POST'])
def create_razorpay_payment():
    try:
        data = request.get_json()
        order_number = data.get("order_number")

        # Get order from database
        order = Order.query.filter_by(order_number=order_number).first()
        if not order:
            return jsonify({"error": "Order not found"}), 404

        # Create Razorpay Order (amount in paise)
        amount_in_paise = int(order.total_amount * 100)
        
        razorpay_order = razorpay_client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": order_number,
            "payment_capture": 1,  # Auto-capture
            "notes": {
                "order_number": order_number,
                "customer_email": order.customer_email
            }
        })

        # Update order with Razorpay ID
        order.razorpay_order_id = razorpay_order['id']
        db.session.commit()

        return jsonify({
            "success": True,
            "order_id": razorpay_order['id'],
            "amount": amount_in_paise,
            "currency": "INR",
            "key": os.getenv('RAZORPAY_KEY_ID'),  # Frontend needs this
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "customer_phone": order.customer_phone,
            "order_number": order_number
        })

    except Exception as e:
        app.logger.error(f"Razorpay payment creation error: {str(e)}")
        return jsonify({"error": str(e)}), 500

#*******New Payment Rule ****


@app.route('/payment/<order_number>')
def payment_page(order_number):
    """Show Razorpay payment page for an order"""
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    
    # Don't show payment page if already paid
    if order.payment_status == 'paid':
        return redirect(url_for('order_confirmation', order_number=order_number))
    
    return render_template('payment.html', 
                         order=order,
                         razorpay_key=os.getenv('RAZORPAY_KEY_ID'),
                         amount_in_paise=int(order.total_amount * 100))


@app.route('/payment/verify', methods=['POST'])
def verify_razorpay_payment():
    try:
        data = request.get_json()
        
        # Get parameters from frontend
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        order_number = data.get('order_number')

        # Verify payment signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        razorpay_client.utility.verify_payment_signature(params_dict)
        
            # Signature verified - update order
        order = Order.query.filter_by(order_number=order_number).first()
        if order:
            order.payment_status = 'paid'
            order.status = 'confirmed'
            order.payment_reference = razorpay_payment_id
            order.payment_date = datetime.utcnow()
            db.session.commit()
            
            print(f"Payment verified for Order {order_number}. Sending email...")

            # Send Order Confirmation Email
            try:
                # Debug logging
                print(f"Calling send_order_confirmation_email for order {order.id}")
                send_order_confirmation_email(order)
            except Exception as e:
                app.logger.error(f"Failed to trigger order email: {str(e)}")
                import traceback
                traceback.print_exc()

            return jsonify({
                "success": True,
                "message": "Payment verified successfully",
                "order_number": order_number,
                "payment_id": razorpay_payment_id
            })

    except razorpay.errors.SignatureVerificationError as e:
        app.logger.error(f"Signature verification failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Payment verification failed",
            "details": "Invalid payment signature"
        }), 400
    except Exception as e:
        app.logger.error(f"Payment verification error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/checkout', methods=['POST'])
def checkout_api():
    """API endpoint for checkout (legacy support)"""
    return create_order()


# ==================== PANDIT BOOKING PAYMENT ROUTES ====================

@app.route('/pandit-payment/<booking_number>')
def pandit_payment_page(booking_number):
    """Show Razorpay payment page for a pandit booking"""
    booking = Booking.query.filter_by(booking_number=booking_number).first_or_404()
    
    # Don't show payment page if already paid
    if booking.payment_status == 'paid':
        return redirect(url_for('pandit_booking_confirmation', booking_number=booking_number))
    
    # Get pandit details
    pandit = Pandit.query.get(booking.pandit_id)
    
    return render_template('pandit_payment.html', 
                         booking=booking,
                         pandit=pandit,
                         razorpay_key=os.getenv('RAZORPAY_KEY_ID'),
                         amount_in_paise=int(booking.amount * 100))


@app.route('/api/pandit-payment/create', methods=['POST'])
def create_pandit_razorpay_payment():
    """Create Razorpay order for pandit booking"""
    try:
        data = request.get_json()
        booking_number = data.get("booking_number")

        # Get booking from database
        booking = Booking.query.filter_by(booking_number=booking_number).first()
        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        # Create Razorpay Order (amount in paise)
        amount_in_paise = int(booking.amount * 100)
        
        razorpay_order = razorpay_client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": booking_number,
            "payment_capture": 1,  # Auto-capture
            "notes": {
                "booking_number": booking_number,
                "customer_name": booking.customer_name,
                "puja_type": booking.puja_type
            }
        })

        # Update booking with Razorpay ID
        booking.razorpay_order_id = razorpay_order['id']
        db.session.commit()

        return jsonify({
            "success": True,
            "order_id": razorpay_order['id'],
            "amount": amount_in_paise,
            "currency": "INR",
            "key": os.getenv('RAZORPAY_KEY_ID'),
            "customer_name": booking.customer_name,
            "customer_email": booking.email,
            "customer_phone": booking.phone,
            "booking_number": booking_number
        })

    except Exception as e:
        app.logger.error(f"Razorpay payment creation error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/pandit-payment/verify', methods=['POST'])
def verify_pandit_razorpay_payment():
    """Verify Razorpay payment for pandit booking"""
    try:
        data = request.get_json()
        
        # Get parameters from frontend
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        booking_number = data.get('booking_number')

        # Verify payment signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Signature verified - update booking
        booking = Booking.query.filter_by(booking_number=booking_number).first()
        if booking:
            booking.payment_status = 'paid'
            booking.status = 'confirmed'
            booking.payment_reference = razorpay_payment_id
            booking.payment_date = datetime.utcnow()
            db.session.commit()

            # Send Confirmation Email with Calendar Invite
            # We run this in a try/except to ensure response returns even if email fails
            try:
                send_booking_confirmation_email(booking, booking.pandit)
            except Exception as e:
                app.logger.error(f"Failed to trigger email: {str(e)}")

            return jsonify({
                "success": True,
                "message": "Payment verified successfully",
                "booking_number": booking_number,
                "payment_id": razorpay_payment_id
            })

    except razorpay.errors.SignatureVerificationError as e:
        app.logger.error(f"Signature verification failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Payment verification failed",
            "details": "Invalid payment signature"
        }), 400
    except Exception as e:
        app.logger.error(f"Payment verification error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/pandit-booking-confirmation/<booking_number>')
def pandit_booking_confirmation(booking_number):
    """Pandit booking confirmation page"""
    booking = Booking.query.filter_by(booking_number=booking_number).first_or_404()
    pandit = Pandit.query.get(booking.pandit_id)
    
    # Generate Google Calendar Link
    from urllib.parse import quote
    from datetime import timedelta
    
    # Create event title and details
    event_title = f"{booking.puja_type} with Pandit {pandit.name}"
    event_details = (
        f"Booking Ref: {booking.booking_number}\n"
        f"Pandit: {pandit.name} ({pandit.phone})\n"
        f"Puja Type: {booking.puja_type}\n"
        f"Notes: {booking.notes or 'None'}"
    )
    
    # Format dates for Google Calendar (YYYYMMDD)
    # Since we only have a date, we make it an all-day event
    # End date must be the next day for a single-day all-day event
    start_date_str = booking.date.strftime('%Y%m%d')
    end_date = booking.date + timedelta(days=1)
    end_date_str = end_date.strftime('%Y%m%d')
    
    # Construct URL
    google_calendar_url = (
        f"https://www.google.com/calendar/render?action=TEMPLATE"
        f"&text={quote(event_title)}"
        f"&details={quote(event_details)}"
        f"&location={quote(booking.address)}"
        f"&dates={start_date_str}/{end_date_str}"
    )
    
    return render_template('pandit_booking_confirmation.html', 
                           booking=booking, 
                           pandit=pandit,
                           google_calendar_url=google_calendar_url)


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


@app.route('/admin/pandit/edit/<int:pandit_id>', methods=['GET', 'POST'])
@admin_required
def edit_pandit(pandit_id):
    """Edit pandit - GET returns data, POST updates"""
    pandit = Pandit.query.get_or_404(pandit_id)
    
    if request.method == 'POST':
        try:
            data = request.get_json() if request.content_type and 'application/json' in request.content_type else request.form
            
            pandit.name = data.get('name', pandit.name)
            pandit.age = int(data.get('age', pandit.age)) if data.get('age') else pandit.age
            pandit.email = data.get('email', pandit.email)
            pandit.phone = data.get('phone', pandit.phone)
            pandit.experience = data.get('experience', pandit.experience)
            pandit.languages = data.get('languages', pandit.languages)
            pandit.location = data.get('location', pandit.location)
            pandit.specialties = data.get('specialties', pandit.specialties)
            pandit.availability = data.get('availability', 'true').lower() == 'true' if isinstance(data.get('availability'), str) else bool(data.get('availability', pandit.availability))
            if 'image_url' in data:
                pandit.image_url = data['image_url']
            
            db.session.commit()
            return jsonify({"success": True, "message": "Pandit updated successfully"})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 500
    
    # GET - return pandit data
    return jsonify({
        "id": pandit.id,
        "name": pandit.name,
        "age": pandit.age,
        "email": pandit.email,
        "phone": pandit.phone,
        "experience": pandit.experience,
        "languages": pandit.languages,
        "location": pandit.location,
        "specialties": pandit.specialties,
        "availability": pandit.availability,
        "image_url": pandit.image_url,
        "is_approved": pandit.is_approved
    })


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
        # Handle both JSON and form data
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        product = PujaMaterial(
            name=data.get('name'),
            description=data.get('description', ''),
            price=float(data.get('price', 0)),
            image_url=data.get('image_url', 'priest.jpeg')
        )
        db.session.add(product)
        db.session.commit()
        return jsonify({"success": True, "message": "Product added", "product": product.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    """Edit product - GET shows form, POST updates"""
    product = PujaMaterial.query.get_or_404(product_id)
    
    if request.method == 'POST':
        try:
            # Handle form data
            if request.content_type and 'application/json' in request.content_type:
                data = request.get_json()
                product.name = data.get('name', product.name)
                product.description = data.get('description', product.description)
                product.price = float(data.get('price', product.price))
                if 'image_url' in data:
                    product.image_url = data['image_url']
            else:
                # Handle form data
                product.name = request.form.get('name', product.name)
                product.description = request.form.get('description', product.description)
                product.price = float(request.form.get('price', product.price))
                if 'image_url' in request.form:
                    product.image_url = request.form['image_url']
            
            db.session.commit()
            return jsonify({"success": True, "message": "Product updated successfully", "product": {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "image_url": product.image_url
            }})
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": str(e)}), 500
    
    # GET - return product data as JSON
    return jsonify({
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "image_url": product.image_url
    })


@app.route('/admin/product/upload-image', methods=['POST'])
@admin_required
def upload_product_image():
    """Upload product image"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file part"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No selected file"}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to avoid conflicts
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Return relative path for database storage
            image_url = f'uploads/{filename}'
            return jsonify({
                "success": True,
                "message": "Image uploaded successfully",
                "image_url": image_url,
                "url": url_for('static', filename=image_url)
            }), 200
        
        return jsonify({"success": False, "error": "Invalid file type. Allowed: png, jpg, jpeg, gif"}), 400
    except Exception as e:
        app.logger.error(f"Error uploading image: {str(e)}")
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


@app.route('/admin/booking/update-status/<int:booking_id>', methods=['POST'])
@admin_required
def update_booking_status(booking_id):
    """Update booking status"""
    try:
        booking = Booking.query.get_or_404(booking_id)
        data = request.get_json() if request.content_type and 'application/json' in request.content_type else request.form
        new_status = data.get('status')
        
        if new_status in ['pending', 'confirmed', 'completed', 'cancelled']:
            booking.status = new_status
            db.session.commit()
            return jsonify({"success": True, "message": "Booking status updated"})
        else:
            return jsonify({"success": False, "error": "Invalid status"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/admin/orders')
@admin_required
def admin_orders():
    """View all orders"""
    orders = Order.query.order_by(Order.id.desc()).all()
    return render_template('admin_orders.html', orders=orders)


@app.route('/admin/order/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    """View order details"""
    order = Order.query.get_or_404(order_id)
    return render_template('admin_order_detail.html', order=order)


@app.route('/admin/order/update-status/<int:order_id>', methods=['POST'])
@admin_required
def update_order_status(order_id):
    """Update order status"""
    try:
        order = Order.query.get_or_404(order_id)
        data = request.get_json() if request.content_type and 'application/json' in request.content_type else request.form
        new_status = data.get('status')
        payment_status = data.get('payment_status')
        
        if new_status in ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']:
            order.status = new_status
        if payment_status in ['pending', 'paid', 'refunded']:
            order.payment_status = payment_status
        
        db.session.commit()
        return jsonify({"success": True, "message": "Order status updated"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


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
            email="shubhprsnl@gmail.com",
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
    
# USER DASHBOARD ENDPOINTS
# ============================================ #

@app.route('/api/user/dashboard', methods=['GET'])
@jwt_required()
def get_user_dashboard():
    """Get user dashboard summary"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get recent orders (limit to 5)
        recent_orders = Order.query.filter_by(user_id=user_id)\
            .order_by(Order.created_at.desc())\
            .limit(5).all()
        
        # Get recent bookings (limit to 5)
        recent_bookings = Booking.query.filter_by(user_id=user_id)\
            .order_by(Booking.created_at.desc())\
            .limit(5).all()
        
        # Calculate stats
        total_orders = Order.query.filter_by(user_id=user_id).count()
        total_bookings = Booking.query.filter_by(user_id=user_id).count()
        total_spent = db.session.query(db.func.sum(Order.total_amount))\
            .filter(Order.user_id == user_id)\
            .scalar() or 0
        
        dashboard_data = {
            'user': user.to_dict(),
            'stats': {
                'total_orders': total_orders,
                'total_bookings': total_bookings,
                'total_spent': total_spent
            },
            'recent_orders': [order.to_dict() for order in recent_orders],
            'recent_bookings': [booking.to_dict() for booking in recent_bookings]
        }
        
        return jsonify(dashboard_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/orders', methods=['GET'])
@jwt_required()
def get_user_orders():
    """Get all orders for the logged-in user"""
    try:
        user_id = get_jwt_identity()
        orders = Order.query.filter_by(user_id=user_id)\
            .order_by(Order.created_at.desc())\
            .all()
        
        return jsonify({
            'orders': [order.to_dict() for order in orders]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/bookings', methods=['GET'])
@jwt_required()
def get_user_bookings():
    """Get all bookings for the logged-in user"""
    try:
        user_id = get_jwt_identity()
        bookings = Booking.query.filter_by(user_id=user_id)\
            .order_by(Booking.created_at.desc())\
            .all()
        
        return jsonify({
            'bookings': [booking.to_dict() for booking in bookings]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/bookings/<int:booking_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_user_booking(booking_id):
    """Cancel a booking"""
    try:
        user_id = get_jwt_identity()
        booking = Booking.query.get(booking_id)
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
            
        if booking.user_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
            
        if booking.status not in ['pending', 'confirmed']:
            return jsonify({'error': 'Cannot cancel this booking'}), 400
            
        booking.status = 'cancelled'
        db.session.commit()
        
        return jsonify({'message': 'Booking cancelled successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """Get user profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    """Update user profile"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.json
        
        # Update fields if provided
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'phone' in data:
            user.phone = data['phone']
        if 'email' in data and data['email'] != user.email:
            # Check if new email is already taken
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user.id:
                return jsonify({'error': 'Email already in use'}), 400
            user.email = data['email']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.json
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        # Verify current password
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Set new password
        user.set_password(new_password)
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500    


@app.route('/user/dashboard')
def user_dashboard_page():
    """Render user dashboard HTML page"""
    return render_template('user/dashboard.html')

@app.route('/user/orders')
def user_orders_page():
    """Render user orders HTML page"""
    return render_template('user/orders.html')

@app.route('/user/profile')
def user_profile_page():
    """Render user profile HTML page"""
    return render_template('user/profile.html')

@app.route('/user/bookings')
def user_bookings_page():
    """Render user bookings HTML page"""
    return render_template('user/bookings.html')    

@app.route('/user/settings')
def user_settings_page():
    """Render user settings HTML page"""
    return render_template('user/settings.html')    



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=os.getenv("FLASK_DEBUG", False))

