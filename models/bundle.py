from database import db

class Bundle(db.Model):
    __tablename__ = 'bundles'
    __table_args__ = (
        {'schema': 'public', 'extend_existing': True}
    )
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(200))
    original_price = db.Column(db.Float, nullable=False)
    discounted_price = db.Column(db.Float, nullable=False)
    includes = db.Column(db.Text)