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
        
        
priests = [
    {"name": "Pankaj Jha", "experience": "4 years", "age": "40 years", "availability": True, "Location": "Chennai"},
    {"name": "Medhansh Acharya", "experience": "7 years", "age": "35 years", "availability": True, "Location": "Pune"},
    {"name": "Govind Kumar Jha", "experience": "6 years", "age": "27 years", "availability": True, "Location": "New Delhi"},
    {"name": "Shankar Pandit", "experience": "9 years", "age": "39 years", "availability": True, "Location": "Bangalore"}
]

@app.route("/")
def home():
    return render_template('home.html', priests=priests)

@app.route("/api/priests")
def list_priests():
    return jsonify(priests)

if __name__ == "__main__":
    app.run(debug=True)
