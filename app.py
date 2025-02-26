from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv

load_dotenv()
print("Database URL:", os.getenv("DATABASE_URL"))

app = Flask(__name__)

# Ensure environment variable or fallback for local testing
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

with app.app_context():
    try:
        db.engine.connect()
        print("✅ Successfully connected to the PostgreSQL database!")
    except Exception as e:
        print(f"❌ Database connection error: {e}")

class Priests(db.Model):  # ✅ Class names should be PascalCase
    __tablename__ = "priests"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.String(50), nullable=False)
    age = db.Column(db.String(20), nullable=False)
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

        
# Marked down as we want to use data from database
# priests = [
#     {"name": "Pankaj Jha", "experience": "4 years", "age": "40 years", "availability": True, "Location": "Chennai"},
#     {"name": "Medhansh Acharya", "experience": "7 years", "age": "35 years", "availability": True, "Location": "Pune"},
#     {"name": "Govind Kumar Jha", "experience": "6 years", "age": "27 years", "availability": True, "Location": "New Delhi"},
#     {"name": "Shankar Pandit", "experience": "9 years", "age": "39 years", "availability": True, "Location": "Bangalore"}
# ]


@app.route("/")
def home():
    priests = Priests.query.all()  # ✅ Corrected query
    return render_template('home.html', priests=priests)

@app.route("/api/priests")
def list_priests():
    priests = Priests.query.all()  # ✅ Corrected model reference
    return jsonify([priest.to_dict() for priest in priests])  # ✅ Fixed iteration

if __name__ == "__main__":
    app.run(debug=True)
