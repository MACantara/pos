from flask import Blueprint, render_template, request, redirect, url_for, abort
from flask_login import login_required, current_user
from extensions import db
from models import Order, OrderItem, Product, User, Customer # Import Customer

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

@orders_bp.route('/')
@login_required
def list_orders():
    # Redirect cashier away
    if current_user.role == 'cashier':
        return redirect(url_for('pos.new_order'))

    # Get filters from query parameters
    page = request.args.get('page', 1, type=int)
    per_page = 15 # Number of orders per page
    status_filter = request.args.get('status', 'all')
    type_filter = request.args.get('type', 'all')
    
    # Base query - Join User and optionally Customer
    query = db.session.query(
        Order, 
        User.name.label('staff_name'), 
        Customer.name.label('customer_name') # Select customer name
    ).join(User, Order.user_id == User.id)\
     .outerjoin(Customer, Order.customer_id == Customer.id) # Left outer join for customer

    # Apply filters
    if status_filter != 'all':
        query = query.filter(Order.status == status_filter)
    if type_filter != 'all':
        query = query.filter(Order.order_type == type_filter)
    
    # Get paginated orders
    pagination = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    # orders_data now contains tuples: (Order object, staff_name, customer_name)
    orders_data = pagination.items 
    
    return render_template(
        'orders.html', 
        orders_data=orders_data, # Pass the tuple data
        pagination=pagination,
        status_filter=status_filter,
        type_filter=type_filter
    )

@orders_bp.route('/<int:order_id>/receipt')
@login_required
def view_receipt(order_id):
    order = Order.query.options(
        db.joinedload(Order.items).joinedload(OrderItem.product), # Eager load items and products
        db.joinedload(Order.staff), # Eager load staff
        db.joinedload(Order.customer) # Eager load customer
    ).get_or_404(order_id)

    # Optional: Check if user has permission to view this receipt
    # if current_user.role == 'cashier' and order.user_id != current_user.id:
    #     abort(403)

    return render_template('receipt.html', order=order)

# Note: API endpoints for orders (like getting details or updating status)
# should be in routes/api.py
