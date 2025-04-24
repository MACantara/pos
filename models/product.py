from extensions import db

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(100), default='default.jpg')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    available = db.Column(db.Boolean, default=True)
    ingredients = db.relationship('ProductIngredient', backref='product', lazy=True, cascade="all, delete-orphan") # Added cascade
    order_items = db.relationship('OrderItem', backref='product', lazy=True) # Renamed relationship

    def __repr__(self):
        return f"Product('{self.name}', '{self.price}')"
