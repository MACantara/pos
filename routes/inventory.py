from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Ingredient, Supplier, InventoryLog, User # Import necessary models

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_bp.route('/')
@login_required
def view_inventory():
    # Redirect cashier away
    if current_user.role == 'cashier':
        return redirect(url_for('pos.new_order'))

    # Eager load supplier and user for efficiency
    ingredients = Ingredient.query.options(db.joinedload(Ingredient.supplier)).order_by(Ingredient.name).all()
    low_stock = Ingredient.query.filter(Ingredient.quantity <= Ingredient.threshold).order_by(Ingredient.name).all()
    suppliers = Supplier.query.order_by(Supplier.name).all()
    inventory_logs = InventoryLog.query.options(
        db.joinedload(InventoryLog.ingredient), 
        db.joinedload(InventoryLog.user)
    ).order_by(InventoryLog.timestamp.desc()).limit(20).all() # Increased limit
    
    return render_template(
        'inventory.html',
        ingredients=ingredients,
        low_stock=low_stock,
        suppliers=suppliers,
        inventory_logs=inventory_logs
    )

# Note: API endpoints for managing inventory and suppliers 
# should be in routes/api.py
