from extensions import db
from datetime import date

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # Made name required
    phone = db.Column(db.String(20), unique=True, nullable=True) # Made nullable but unique if provided
    email = db.Column(db.String(100), unique=True, nullable=True) # Made nullable but unique if provided
    rewards_points = db.Column(db.Integer, default=0)
    birthday = db.Column(db.Date, nullable=True)
    orders = db.relationship('Order', backref='customer', lazy=True)
    created_at = db.Column(db.Date, default=date.today) # Added created_at

    def __repr__(self):
        return f"Customer('{self.name}', '{self.phone}')"
