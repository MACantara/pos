from extensions import db
from datetime import datetime

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    order_type = db.Column(db.String(20), nullable=False)  # dine-in, take-out, delivery
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, in-progress, completed, cancelled
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Staff who took the order
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan") # Added cascade
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    subtotal = db.Column(db.Float, nullable=False) # Added subtotal
    tax = db.Column(db.Float, nullable=False) # Added tax
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True) # Made nullable

    def __repr__(self):
        return f"Order('{self.order_number}', '{self.status}', '{self.total_amount}')"
