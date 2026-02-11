from database import db
from datetime import datetime
import random

class Order(db.Model):
    __tablename__ = 'orders'
    __table_args__ = (
        {'schema': 'public', 'extend_existing': True}
    )
    
    razorpay_order_id = db.Column(db.String(100), nullable=True)  # razorpay
    payment_date = db.Column(db.DateTime, nullable=True)  # razorpay
    payment_reference = db.Column(db.String(100), nullable=True)  # razorpay payment ID
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(150), nullable=False)
    customer_email = db.Column(db.String(150), nullable=False)
    customer_phone = db.Column(db.String(15), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, shipped, delivered, cancelled
    payment_status = db.Column(db.String(50), default='pending')  # pending, paid, failed
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    
    # Add user_id for logged-in users (optional)
    user_id = db.Column(db.Integer, db.ForeignKey('public.users.id'), nullable=True)
    
    # Relationship
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.order_number:
            self.order_number = self.generate_order_number()
    
    @classmethod
    def generate_order_number(cls):
        """Generate unique order number like ORD-20251214-001"""
        date_str = datetime.now().strftime('%Y%m%d')
        # Get last order for today
        last_order = cls.query.filter(
            cls.order_number.like(f'ORD-{date_str}-%')
        ).order_by(cls.order_number.desc()).first()
        
        if last_order:
            try:
                last_num = int(last_order.order_number.split('-')[-1])
                new_num = str(last_num + 1).zfill(3)
            except (ValueError, IndexError):
                new_num = '001'
        else:
            new_num = '001'
        
        return f"ORD-{date_str}-{new_num}"
    
    def calculate_total(self):
        """Recalculate total from items"""
        self.total_amount = sum(item.subtotal for item in self.items)
        return self.total_amount
    
    def to_dict(self):
        return {
            "id": self.id,
            "order_number": self.order_number,
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "customer_phone": self.customer_phone,
            "shipping_address": self.shipping_address,
            "city": self.city,
            "state": self.state,
            "pincode": self.pincode,
            "total_amount": self.total_amount,
            "status": self.status,
            "payment_status": self.payment_status,
            "payment_reference": self.payment_reference,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "items": [item.to_dict() for item in self.items]
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    __table_args__ = (
        {'schema': 'public', 'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('public.orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('public.puja_materials.id'), nullable=True)
    bundle_id = db.Column(db.Integer, db.ForeignKey('public.bundles.id'), nullable=True)
    product_name = db.Column(db.String(200), nullable=False)
    product_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Relationship
    product = db.relationship('PujaMaterial', backref='order_items')
    bundle = db.relationship('Bundle', backref='order_items')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Calculate subtotal if not provided
        if not self.subtotal and self.product_price and self.quantity:
            self.subtotal = self.product_price * self.quantity
    
    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "product_price": self.product_price,
            "quantity": self.quantity,
            "subtotal": self.subtotal
        }