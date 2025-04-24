from extensions import db
from datetime import datetime

class InventoryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
    quantity_change = db.Column(db.Float, nullable=False) # Positive for addition, negative for reduction
    reason = db.Column(db.String(100), nullable=False)  # e.g., 'purchase', 'order_usage', 'waste', 'correction'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # User who made the change
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True) # Link to order if usage
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"InventoryLog(Ingredient: {self.ingredient_id}, Change: {self.quantity_change}, Reason: {self.reason})"
