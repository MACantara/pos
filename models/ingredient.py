from extensions import db

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True) # Added unique=True
    quantity = db.Column(db.Float, nullable=False, default=0) # Added default
    unit = db.Column(db.String(50), nullable=False) # e.g., kg, liter, pcs
    threshold = db.Column(db.Float, nullable=False, default=0) # Low stock threshold
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True) # Made nullable
    products = db.relationship('ProductIngredient', backref='ingredient', lazy=True, cascade="all, delete-orphan") # Added cascade
    inventory_logs = db.relationship('InventoryLog', backref='ingredient', lazy=True) # Added relationship

    def __repr__(self):
        return f"Ingredient('{self.name}', '{self.quantity} {self.unit}')"
