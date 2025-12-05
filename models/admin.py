from database import db
from flask_bcrypt import generate_password_hash, check_password_hash

class Admin(db.Model):
    __tablename__ = 'admins'
    __table_args__ = (
        {'schema': 'public', 'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return check_password_hash(self.password_hash.encode('utf-8'), password)
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_super_admin": self.is_super_admin
        }


class Booking(db.Model):
    __tablename__ = 'bookings'
    __table_args__ = (
        {'schema': 'public', 'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    pandit_id = db.Column(db.Integer, db.ForeignKey('public.pandits.id'), nullable=False)
    customer_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(150))
    puja_type = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    address = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, completed, cancelled
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    # Relationship
    pandit = db.relationship('Pandit', backref='bookings')
    
    def to_dict(self):
        return {
            "id": self.id,
            "pandit_id": self.pandit_id,
            "pandit_name": self.pandit.name if self.pandit else None,
            "customer_name": self.customer_name,
            "phone": self.phone,
            "email": self.email,
            "puja_type": self.puja_type,
            "date": str(self.date),
            "address": self.address,
            "notes": self.notes,
            "status": self.status,
            "created_at": str(self.created_at)
        }

