from flask import Flask, render_template, jsonify, request, url_for
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from flask_migrate import Migrate

# Local imports
from database import db
from models import User, Pandit, PujaMaterial, Testimonial, Bundle

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Application configuration
app.config.update(
    SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY"),
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
        return render_template('error.html'), 500

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
            email = request.form.get('email')
            phone = request.form.get('phone')
            experience = request.form.get('experience')
            languages = request.form.get('languages')
            location = request.form.get('location')
            specialties = request.form.get('specialties')

            new_pandit = Pandit(
                name=name,
                email=email,
                phone=phone,
                experience=experience,
                languages=languages,
                location=location,
                specialties=specialties,
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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=os.getenv("FLASK_DEBUG", False))

