from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from extensions import db
from models import Order, OrderItem, Product, User, Ingredient # Import necessary models
from datetime import datetime, date # Import date
from sqlalchemy import func, desc

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def view():
    # Redirect cashier away from dashboard
    if current_user.role == 'cashier':
        return redirect(url_for('pos.new_order'))
        
    # Get today's date range
    today = date.today() # Use date.today() for consistency
    start_of_today = datetime.combine(today, datetime.min.time())
    end_of_today = datetime.combine(today, datetime.max.time())

    # Base query for today's orders
    today_orders_query = Order.query.filter(
        Order.created_at >= start_of_today,
        Order.created_at <= end_of_today
    )
    
    # Calculate total sales for today
    total_sales = today_orders_query.with_entities(func.sum(Order.total_amount)).scalar() or 0
    
    # Calculate Today's Orders Count
    today_orders_count = today_orders_query.count() # More efficient count

    # Get best selling items today
    best_sellers = db.session.query(
        Product.name, func.sum(OrderItem.quantity).label('total') # Alias to 'total' as used in template
    ).join(OrderItem, OrderItem.product_id == Product.id)\
     .join(Order, Order.id == OrderItem.order_id)\
     .filter(Order.created_at >= start_of_today, Order.created_at <= end_of_today)\
     .group_by(Product.name)\
     .order_by(desc('total'))\
     .limit(5).all()
    
    # Calculate Staff Performance (Orders taken today by each staff member)
    staff_performance = db.session.query(
        User.name,
        func.count(Order.id).label('order_count')
    ).join(Order, User.id == Order.user_id)\
    .filter(
        Order.created_at >= start_of_today,
        Order.created_at <= end_of_today
    )\
    .group_by(User.name)\
    .order_by(func.count(Order.id).desc())\
    .all()

    # Get low stock ingredients
    low_stock = Ingredient.query.filter(
        Ingredient.quantity <= Ingredient.threshold
    ).order_by(Ingredient.name).all()
    
    # Get recent orders (last 5 today)
    recent_orders = today_orders_query.order_by(Order.created_at.desc()).limit(5).all()

    # Get count of staff who took orders today for the "Staff on Duty" card
    # Note: This is a simplified view of "on duty". A proper system might track logins/shifts.
    staff_on_duty_count = db.session.query(func.count(Order.user_id.distinct()))\
        .filter(Order.created_at >= start_of_today, Order.created_at <= end_of_today)\
        .scalar() or 0

    return render_template(
        'dashboard.html', 
        total_sales=total_sales, 
        today_orders=today_orders_count, # Pass count as today_orders
        best_sellers=best_sellers,
        staff_on_duty_count=staff_on_duty_count, # Pass count for the card
        low_stock=low_stock,
        orders=recent_orders, # Pass recent orders list
        staff_performance=staff_performance # Pass the performance data
        # Removed staff_on_duty list as it's replaced by staff_performance
    )
