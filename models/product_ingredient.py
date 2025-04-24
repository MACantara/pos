from extensions import db

class ProductIngredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
    quantity_needed = db.Column(db.Float, nullable=False) # Quantity of ingredient needed per product unit

    def __repr__(self):
        return f"ProductIngredient(Product: {self.product_id}, Ingredient: {self.ingredient_id}, Qty: {self.quantity_needed})"
