from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Order, OrderItem, Product, User, Ingredient # Import necessary models
from datetime import datetime
from sqlalchemy import func, desc

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def view():
    # Redirect cashier away from dashboard
    if current_user.role == 'cashier':
        return redirect(url_for('pos.new_order'))
        
    # Get today's date
    today = datetime.utcnow().date()
    start_of_today = datetime.combine(today, datetime.min.time())
    end_of_today = datetime.combine(today, datetime.max.time())

    # Get today's orders
    today_orders_query = Order.query.filter(
        Order.created_at >= start_of_today,
        Order.created_at <= end_of_today
    )
    today_orders = today_orders_query.all()
    
    # Calculate total sales for today
    total_sales = today_orders_query.with_entities(func.sum(Order.total_amount)).scalar() or 0
    
    # Get best selling items today
    best_sellers = db.session.query(
        Product.name, func.sum(OrderItem.quantity).label('total_quantity')
    ).join(OrderItem, OrderItem.product_id == Product.id)\
     .join(Order, Order.id == OrderItem.order_id)\
     .filter(Order.created_at >= start_of_today, Order.created_at <= end_of_today)\
     .group_by(Product.name)\
     .order_by(desc('total_quantity'))\
     .limit(5).all()
    
    # Get staff who created orders today (simplified - assumes staff logged in today are on duty)
    # A better approach would involve a dedicated shift/attendance model
    staff_ids_today = db.session.query(Order.user_id)\
        .filter(Order.created_at >= start_of_today, Order.created_at <= end_of_today)\
        .distinct().all()
    staff_on_duty = User.query.filter(User.id.in_([s[0] for s in staff_ids_today])).all() if staff_ids_today else []

    # Get low stock ingredients
    low_stock = Ingredient.query.filter(
        Ingredient.quantity <= Ingredient.threshold
    ).order_by(Ingredient.name).all()
    
    # Get recent orders (last 5 today)
    recent_orders = today_orders_query.order_by(Order.created_at.desc()).limit(5).all()

    # Calculate Today's Orders Count
    today_orders_count = db.session.query(func.count(Order.id)).filter(
        Order.created_at >= start_of_today,
        Order.created_at <= end_of_today
    ).scalar() or 0 # Get the count of orders created today

    return render_template(
        'dashboard.html', 
        total_sales=total_sales, 
        today_orders_count=len(today_orders), # Renamed for clarity
        best_sellers=best_sellers,
        staff_on_duty=staff_on_duty,
        low_stock=low_stock,
        orders=recent_orders, # Pass recent orders
        today_orders=today_orders_count # Pass the calculated count
    )
