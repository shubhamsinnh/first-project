from database import db

class Pandit(db.Model):
    __tablename__ = "pandits"
    __table_args__ = (
        {'schema': 'public', 'extend_existing': True}
    )
    
    # Match existing columns
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    experience = db.Column(db.String(250), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    availability = db.Column(db.Boolean, default=True)
    
    # Add new columns for home page features
    image_url = db.Column(db.String(200))  # New column for profile images
    rating = db.Column(db.Integer, default=5)  # New column for star ratings
    languages = db.Column(db.String(200))  # New column for spoken languages
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "experience": self.experience,
            "age": self.age,
            "location": self.location,
            "availability": self.availability,
            # New fields with defaults for existing records
            "image_url": self.image_url or "/static/images/default-pandit.jpg",
            "rating": self.rating or 5,
            "languages": self.languages or "Hindi, English"
        }