from extensions import db

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False) # Price per unit at the time of order
    notes = db.Column(db.Text, nullable=True) # Special instructions

    def __repr__(self):
        return f"OrderItem(Order: {self.order_id}, Product: {self.product_id}, Qty: {self.quantity})"
