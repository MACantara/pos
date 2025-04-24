from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # cashier, kitchen, manager
    orders = db.relationship('Order', backref='staff', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.role}')"

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)
    
    def __repr__(self):
        return f"Category('{self.name}')"

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(100), default='default.jpg')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    available = db.Column(db.Boolean, default=True)
    ingredients = db.relationship('ProductIngredient', backref='product', lazy=True)
    orders = db.relationship('OrderItem', backref='product', lazy=True)
    
    def __repr__(self):
        return f"Product('{self.name}', '{self.price}')"

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    threshold = db.Column(db.Float, nullable=False)
    products = db.relationship('ProductIngredient', backref='ingredient', lazy=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    
    def __repr__(self):
        return f"Ingredient('{self.name}', '{self.quantity} {self.unit}')"

class ProductIngredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
    quantity_needed = db.Column(db.Float, nullable=False)
    
    def __repr__(self):
        return f"ProductIngredient('{self.product_id}', '{self.ingredient_id}', '{self.quantity_needed}')"

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    ingredients = db.relationship('Ingredient', backref='supplier', lazy=True)
    
    def __repr__(self):
        return f"Supplier('{self.name}')"

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    order_type = db.Column(db.String(20), nullable=False)  # dine-in, take-out, delivery
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, in-progress, completed
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    items = db.relationship('OrderItem', backref='order', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    
    def __repr__(self):
        return f"Order('{self.order_number}', '{self.status}', '{self.total_amount}')"

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f"OrderItem('{self.product_id}', '{self.quantity}', '{self.price}')"

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(100))
    rewards_points = db.Column(db.Integer, default=0)
    birthday = db.Column(db.Date)
    orders = db.relationship('Order', backref='customer', lazy=True)
    
    def __repr__(self):
        return f"Customer('{self.name}', '{self.phone}')"

class InventoryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredient.id'), nullable=False)
    quantity_change = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(100), nullable=False)  # purchase, usage, waste
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"InventoryLog('{self.ingredient_id}', '{self.quantity_change}', '{self.reason}')"
