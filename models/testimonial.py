from database import db

class Testimonial(db.Model):
    __tablename__ = 'testimonials'
    __table_args__ = (
        {'schema': 'public', 'extend_existing': True}
    )
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    author_image = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100))