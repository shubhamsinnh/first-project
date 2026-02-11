from database import db

class PujaMaterial(db.Model):
    __tablename__ = 'puja_materials'
    __table_args__ = (
        {'schema': 'public', 'extend_existing': True}
    )
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(200))
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)