from flask import Blueprint, render_template, redirect, url_for, request # Import request
from flask_login import login_required, current_user
from extensions import db
from models import Order, OrderItem, Product, User, Ingredient # Import necessary models
from datetime import datetime, date, timedelta # Import date, timedelta
from sqlalchemy import func, desc, cast, Date as SQLDate # Import cast, SQLDate

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

def get_date_range(range_str):
    """Calculates start and end datetime based on range string."""
    today = date.today()
    start_date, end_date = None, None

    if range_str == 'today':
        start_date = datetime.combine(today, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
    elif range_str == 'yesterday':
        yesterday = today - timedelta(days=1)
        start_date = datetime.combine(yesterday, datetime.min.time())
        end_date = datetime.combine(yesterday, datetime.max.time())
    elif range_str == 'this_week':
        start_of_week = today - timedelta(days=today.weekday()) # Monday
        start_date = datetime.combine(start_of_week, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time()) # Until end of today
    elif range_str == 'last_week':
        end_of_last_week = today - timedelta(days=today.weekday() + 1)
        start_of_last_week = end_of_last_week - timedelta(days=6)
        start_date = datetime.combine(start_of_last_week, datetime.min.time())
        end_date = datetime.combine(end_of_last_week, datetime.max.time())
    elif range_str == 'this_month':
        start_of_month = today.replace(day=1)
        start_date = datetime.combine(start_of_month, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time()) # Until end of today
    elif range_str == 'last_month':
        end_of_last_month = today.replace(day=1) - timedelta(days=1)
        start_of_last_month = end_of_last_month.replace(day=1)
        start_date = datetime.combine(start_of_last_month, datetime.min.time())
        end_date = datetime.combine(end_of_last_month, datetime.max.time())
    elif range_str == 'this_year':
        start_of_year = today.replace(month=1, day=1)
        start_date = datetime.combine(start_of_year, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time()) # Until end of today
    else: # Default to today if range is invalid
        range_str = 'today'
        start_date = datetime.combine(today, datetime.min.time())
        end_date = datetime.combine(today, datetime.max.time())
        
    return start_date, end_date, range_str


@dashboard_bp.route('/')
@login_required
def view():
    # Redirect cashier away from dashboard
    if current_user.role == 'cashier':
        return redirect(url_for('pos.new_order'))
        
    # Get selected date range from query param, default to 'today'
    selected_range = request.args.get('range', 'today')
    start_date, end_date, selected_range = get_date_range(selected_range)

    # Base query for orders within the selected date range
    orders_in_range_query = Order.query.filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date
    )
    
    # Calculate total sales for the range
    total_sales = orders_in_range_query.with_entities(func.sum(Order.total_amount)).scalar() or 0
    
    # Calculate Orders Count for the range
    total_orders_count = orders_in_range_query.count()

    # Get best selling items in the range
    best_sellers = db.session.query(
        Product.name, func.sum(OrderItem.quantity).label('total')
    ).join(OrderItem, OrderItem.product_id == Product.id)\
     .join(Order, Order.id == OrderItem.order_id)\
     .filter(Order.created_at >= start_date, Order.created_at <= end_date)\
     .group_by(Product.name)\
     .order_by(desc('total'))\
     .limit(5).all()
    
    # Calculate Staff Performance in the range
    staff_performance = db.session.query(
        User.name,
        func.count(Order.id).label('order_count')
    ).join(Order, User.id == Order.user_id)\
    .filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date
    )\
    .group_by(User.name)\
    .order_by(func.count(Order.id).desc())\
    .all()

    # Get low stock ingredients (not date-dependent)
    low_stock = Ingredient.query.filter(
        Ingredient.quantity <= Ingredient.threshold
    ).order_by(Ingredient.name).all()
    
    # Get recent orders (still shows last 5 within the range)
    recent_orders = orders_in_range_query.order_by(Order.created_at.desc()).limit(5).all()

    # Get count of staff who took orders in the range
    staff_on_duty_count = db.session.query(func.count(Order.user_id.distinct()))\
        .filter(Order.created_at >= start_date, Order.created_at <= end_date)\
        .scalar() or 0
        
    # --- Sales Trend Data for Chart ---
    # Group by day using func.date()
    sales_trend_query = db.session.query(
        func.date(Order.created_at).label('date'), # Use func.date() for grouping
        func.sum(Order.total_amount).label('daily_sales')
    ).filter(
        Order.created_at >= start_date,
        Order.created_at <= end_date
    ).group_by(func.date(Order.created_at))\
     .order_by(func.date(Order.created_at))\
     .all()

    # Process results (assuming 'date' is now a date object or string 'YYYY-MM-DD')
    sales_trend_labels = []
    sales_trend_values = []
    for item in sales_trend_query:
        # Handle potential date object or string from func.date()
        if isinstance(item.date, date):
            sales_trend_labels.append(item.date.strftime('%Y-%m-%d'))
        else: # Assume it's a string 'YYYY-MM-DD'
            sales_trend_labels.append(item.date) 
        sales_trend_values.append(float(item.daily_sales) if item.daily_sales is not None else 0.0)
        
    # --- End Sales Trend Data ---

    return render_template(
        'dashboard.html', 
        total_sales=total_sales, 
        today_orders=total_orders_count, # Renamed from today_orders_count for consistency with template
        best_sellers=best_sellers,
        staff_on_duty_count=staff_on_duty_count, 
        low_stock=low_stock,
        orders=recent_orders, 
        staff_performance=staff_performance,
        selected_range=selected_range, # Pass the selected range string
        sales_trend_labels=sales_trend_labels, # Pass chart labels
        sales_trend_values=sales_trend_values # Pass chart values
    )
