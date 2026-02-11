# models/otp.py
from database import db
from datetime import datetime, timedelta, timezone
import random
import string

class OTP(db.Model):
    __tablename__ = "otps"
    __table_args__ = {'schema': 'public', 'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)

    def __init__(self, email, **kwargs):
        super(OTP, self).__init__(**kwargs)
        self.email = email
        self.otp_code = self.generate_otp()
        self.expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    @staticmethod
    def generate_otp():
        """Generate a 6-digit OTP code"""
        return ''.join(random.choices(string.digits, k=6))

    def is_valid(self):
        """Check if OTP is still valid (not expired and not used)"""
        return not self.is_used and datetime.now(timezone.utc) < self.expires_at

    def mark_as_used(self):
        """Mark the OTP as used"""
        self.is_used = True

    def to_dict(self):
        """Return OTP data as dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'expires_at': self.expires_at.strftime('%Y-%m-%d %H:%M:%S') if self.expires_at else None,
            'is_used': self.is_used,
            'is_valid': self.is_valid()
        }
