from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import os
from dotenv import load_dotenv

load_dotenv()
print("Database URL:", os.getenv("DATABASE_URL"))

app = Flask(__name__)

# Database Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['JWT_SECRET_KEY'] = 'supersecretkey'  # Change this in production

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# ✅ Ensure the database connection works
with app.app_context(): 
    try:
        db.engine.connect()
        print("✅ Successfully connected to Neon PostgreSQL!")
    except Exception as e:
        print(f"❌ Database connection error: {e}")

# Database Models
class User(db.Model):
    __tablename__ = "users"
    __table_args__ = {'schema': 'public'}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Hashed password

class Priests(db.Model):
    __tablename__ = "priests"
    __table_args__ = {'schema': 'public'}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    experience = db.Column(db.String(250), nullable=False)
    age = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    availability = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "experience": self.experience,
            "age": self.age,
            "location": self.location,
            "availability": self.availability
        }

# Ensure tables are created
with app.app_context():
    db.create_all()

# Routes
@app.route("/")
def home():
    priests = Priests.query.all()  # Fetch all priests
    print(f"Fetched Priests: {priests}")  # Debugging output

    if not priests:
        print("❌ No priests found in database!")

    return render_template('home.html', priests=priests)

# ✅ Register User (No user.py, everything is inside app.py)
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

# ✅ Login User
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=user.id)
    return jsonify({"message": "Login successful", "access_token": access_token}), 200

# ✅ Fetch Priests (Requires Authentication)
@app.route("/api/priests", methods=["GET"])
@jwt_required()
def fetch_priests():
    current_user = get_jwt_identity()  # Get user identity from the token
    priests = Priests.query.all()

    return jsonify({
        "current_user": current_user,
        "priests": [priest.to_dict() for priest in priests]
    })

# ✅ Fetch Available Priests (Public Route)
@app.route("/api/available-priests", methods=["GET"])
def get_available_priests():
    priests = Priests.query.filter_by(availability=True).all()
    return jsonify([priest.to_dict() for priest in priests])

if __name__ == "__main__":
    app.run(debug=True)
