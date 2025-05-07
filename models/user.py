from database import db

class User(db.Model):
    __tablename__ = "users"
    __table_args__ = (
        {'schema': 'public', 'extend_existing': True}
    )
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Hashed password
    
    