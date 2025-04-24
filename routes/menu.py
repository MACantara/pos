from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Category, Product # Import necessary models

menu_bp = Blueprint('menu', __name__, url_prefix='/menu')

@menu_bp.route('/')
@login_required
def view_menu():
    # Redirect cashier away
    if current_user.role == 'cashier':
        return redirect(url_for('pos.new_order'))

    categories = Category.query.order_by(Category.name).all()
    # Eager load category for efficiency in the template
    products = Product.query.options(db.joinedload(Product.category)).order_by(Product.name).all()
    
    return render_template('menu.html', categories=categories, products=products)

# Note: API endpoints for managing products and categories 
# should be in routes/api.py
