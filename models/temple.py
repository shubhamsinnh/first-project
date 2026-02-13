from database import db

class Temple(db.Model):
    __tablename__ = 'temples'
    __table_args__ = (
        {'schema': 'public', 'extend_existing': True}
    )
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)  # City name
    state = db.Column(db.String(100))  # State name
    image_url = db.Column(db.String(200))
    description = db.Column(db.Text)
    deity = db.Column(db.String(100))  # Main deity (e.g., Lord Shiva, Maa Vaishno Devi)
    significance = db.Column(db.Text)  # Religious/historical significance
    starting_price = db.Column(db.Numeric(10, 2), default=999)
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    # Relationship to pujas - using 'selectin' for eager loading to avoid N+1 queries
    pujas = db.relationship('TemplePuja', backref='temple', lazy='selectin', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Temple {self.name}>'


class TemplePuja(db.Model):
    __tablename__ = 'temple_pujas'
    __table_args__ = (
        {'schema': 'public', 'extend_existing': True}
    )
    id = db.Column(db.Integer, primary_key=True)
    temple_id = db.Column(db.Integer, db.ForeignKey('public.temples.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    duration = db.Column(db.String(50))  # e.g., "2-3 hours", "1 day"
    benefits = db.Column(db.Text)  # Spiritual benefits
    includes = db.Column(db.Text)  # What's included (video proof, prasad, etc.)
    image_url = db.Column(db.String(200))
    is_popular = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<TemplePuja {self.name} at {self.temple.name if self.temple else "Unknown"}>'
