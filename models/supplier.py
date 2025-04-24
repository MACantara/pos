from extensions import db

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True) # Added unique=True
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    address = db.Column(db.Text) # Added address
    ingredients = db.relationship('Ingredient', backref='supplier', lazy=True)

    def __repr__(self):
        return f"Supplier('{self.name}')"
