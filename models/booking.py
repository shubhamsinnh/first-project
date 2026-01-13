# models/booking.py - Keep ONLY this one
from database import db
from datetime import datetime

class Booking(db.Model):
    __tablename__ = 'bookings'
    __table_args__ = {'schema': 'public', 'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Link to User
    user_id = db.Column(db.Integer, db.ForeignKey('public.users.id'), nullable=True)
    
    # Link to Pandit
    pandit_id = db.Column(db.Integer, db.ForeignKey('public.pandits.id'), nullable=False)
    
    # Booking details
    customer_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(150))
    puja_type = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    address = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)
    
    # Payment fields
    booking_number = db.Column(db.String(50), unique=True, nullable=True)
    amount = db.Column(db.Float, default=999)  # Default booking fee
    payment_status = db.Column(db.String(50), default='pending')  # pending, paid, refunded
    razorpay_order_id = db.Column(db.String(100), nullable=True)
    payment_reference = db.Column(db.String(100), nullable=True)
    payment_date = db.Column(db.DateTime, nullable=True)
    
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    pandit = db.relationship('Pandit', backref='bookings')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'pandit_id': self.pandit_id,
            'pandit_name': self.pandit.name if self.pandit else 'Unknown Pandit',
            'customer_name': self.customer_name,
            'phone': self.phone,
            'email': self.email,
            'puja_type': self.puja_type,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'time': 'All Day',  # Defaulting time since it's not in DB yet
            'address': self.address,
            'location': self.address,  # Frontend expects location
            'notes': self.notes,
            'booking_number': self.booking_number,
            'amount': self.amount,
            'payment_status': self.payment_status,
            'razorpay_order_id': self.razorpay_order_id,
            'payment_reference': self.payment_reference,
            'payment_date': self.payment_date.strftime('%Y-%m-%d %H:%M') if self.payment_date else None,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }