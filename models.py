from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ---------------- USER ----------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    orders = db.relationship("Order", backref="user", lazy=True)

# ---------------- PLANT ----------------
class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100))
    image = db.Column(db.String(200))
    description = db.Column(db.Text)

# ---------------- CART ----------------
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    plant_id = db.Column(db.Integer)

# ---------------- ORDER ----------------
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    plant_name = db.Column(db.String(150))
    price = db.Column(db.Float)
    payment_method = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
