# models/user.py - FINAL VERSION
from database import db
from flask_bcrypt import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    __tablename__ = "users"
    __table_args__ = {'schema': 'public', 'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)  # Hashed password
    
    # Profile fields
    full_name = db.Column(db.String(150))
    phone = db.Column(db.String(15))
    profile_pic = db.Column(db.String(200), default='default_avatar.jpg')
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    pincode = db.Column(db.String(10))
    
    # User roles: 'customer', 'pandit', 'admin' - ESSENTIAL
    role = db.Column(db.String(20), default='customer')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True)
    # orders = db.relationship('Order', backref='user', lazy=True)
    
    # Password security methods
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Return user data as dictionary for API responses"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'profile_pic': self.profile_pic,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'pincode': self.pincode,
            'role': self.role,  # Important for frontend permissions
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
    
    # Optional: Admin helper methods
    def is_admin(self):
        return self.role == 'admin'
    
    def is_pandit(self):
        return self.role == 'pandit'
    
    def is_customer(self):
        return self.role == 'customer'