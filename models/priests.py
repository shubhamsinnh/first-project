from database import db

class Priests(db.Model):
    __tablename__ = "priests"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    experience = db.Column(db.String(250), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    availability = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "experience": self.experience,
            "age": self.age,
            "location": self.location,
            "availability": self.availability
        }
