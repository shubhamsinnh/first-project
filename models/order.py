from database import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'orders'
    __table_args__ = (
        {'schema': 'public', 'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(150), nullable=False)
    customer_email = db.Column(db.String(150), nullable=False)
    customer_phone = db.Column(db.String(15), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, confirmed, shipped, delivered, cancelled
    payment_status = db.Column(db.String(50), default='pending')  # pending, paid, failed
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    
    # Relationship
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    
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
            "notes": self.notes,
            "created_at": str(self.created_at),
            "items": [item.to_dict() for item in self.items]
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    __table_args__ = (
        {'schema': 'public', 'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('public.orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('public.puja_materials.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)  # Store name in case product is deleted
    product_price = db.Column(db.Float, nullable=False)  # Store price at time of order
    quantity = db.Column(db.Integer, nullable=False, default=1)
    subtotal = db.Column(db.Float, nullable=False)
    
    # Relationship
    product = db.relationship('PujaMaterial', backref='order_items')
    
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



