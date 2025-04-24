from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager
from models import User, Category, Product, Ingredient, Supplier, Order, OrderItem, Customer, InventoryLog, ProductIngredient
from datetime import datetime, date
import json
import os
import pandas as pd
import io

routes = Blueprint('routes', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@routes.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'cashier':
            return redirect(url_for('routes.new_order'))
        else:
            return redirect(url_for('routes.dashboard'))
    return redirect(url_for('routes.login'))

@routes.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            
            # Redirect cashiers directly to the POS screen
            if user.role == 'cashier':
                return redirect(url_for('routes.new_order'))
            else:
                return redirect(url_for('routes.dashboard'))
        else:
            flash('Login failed. Check username and password.', 'danger')
            
    return render_template('login.html')

@routes.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('routes.login'))

@routes.before_request
def restrict_cashier_access():
    if current_user.is_authenticated and current_user.role == 'cashier':
        allowed_routes = ['routes.new_order', 'routes.logout', 'static']
        
        if request.endpoint not in allowed_routes and not request.endpoint.startswith('static'):
            return redirect(url_for('routes.new_order'))

@routes.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'cashier':
        return redirect(url_for('routes.new_order'))
        
    # Get today's orders
    today = datetime.today().date()
    today_orders = Order.query.filter(db.func.date(Order.created_at) == today).all()
    
    # Calculate total sales
    total_sales = sum(order.total_amount for order in today_orders) if today_orders else 0
    
    # Get best selling items
    best_sellers = db.session.query(
        Product.name, db.func.sum(OrderItem.quantity).label('total')
    ).join(OrderItem).filter(
        db.func.date(Order.created_at) == today
    ).join(Order).group_by(Product.name).order_by(db.desc('total')).limit(5).all()
    
    # Get staff on duty
    staff_on_duty = User.query.filter(
        db.func.date(User.created_at) == today
    ).all()
    
    # Get low stock ingredients
    low_stock = Ingredient.query.filter(
        Ingredient.quantity <= Ingredient.threshold
    ).all()
    
    return render_template(
        'dashboard.html', 
        total_sales=total_sales, 
        today_orders=len(today_orders),
        best_sellers=best_sellers,
        staff_on_duty=staff_on_duty,
        low_stock=low_stock,
        orders=today_orders[:5]
    )

@routes.route('/orders')
@login_required
def orders():
    # Get order type filter
    order_type = request.args.get('type', 'all')
    
    # Base query
    query = Order.query
    
    # Apply filters
    if order_type != 'all':
        query = query.filter_by(order_type=order_type)
    
    # Get orders
    orders = query.order_by(Order.created_at.desc()).all()
    
    return render_template('orders.html', orders=orders, order_type=order_type)

@routes.route('/new-order', methods=['GET', 'POST'])
@login_required
def new_order():
    categories = Category.query.all()
    products = Product.query.all()
    
    if request.method == 'POST':
        data = request.json
        
        # Create new order
        order = Order(
            order_number=f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            order_type=data['orderType'],
            status='pending',
            user_id=current_user.id,
            total_amount=data['totalAmount'],
            payment_method=data['paymentMethod']
        )
        
        db.session.add(order)
        db.session.flush()
        
        # Add order items
        for item in data['items']:
            product = Product.query.get(item['productId'])
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item['quantity'],
                price=item['price'],
                notes=item.get('notes', '')
            )
            db.session.add(order_item)
            
            # Update inventory
            for ingredient in product.ingredients:
                ingredient_obj = ingredient.ingredient
                ingredient_obj.quantity -= ingredient.quantity_needed * item['quantity']
                
                # Log inventory change
                log = InventoryLog(
                    ingredient_id=ingredient_obj.id,
                    quantity_change=-(ingredient.quantity_needed * item['quantity']),
                    reason='order',
                    user_id=current_user.id
                )
                db.session.add(log)
        
        db.session.commit()
        
        return jsonify({'success': True, 'orderId': order.id})
    
    return render_template('new_order.html', categories=categories, products=products)

@routes.route('/api/employees/<int:employee_id>/reset-password', methods=['POST'])
@login_required
def reset_employee_password(employee_id):
    if current_user.role != 'manager':
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    employee = User.query.get_or_404(employee_id)
    password = request.form.get('password')
    
    employee.password = generate_password_hash(password)
    db.session.commit()
    
    return jsonify({'success': True})

@routes.route('/api/employees/<int:employee_id>', methods=['DELETE'])
@login_required
def delete_employee(employee_id):
    if current_user.role != 'manager':
        return jsonify({'success': False, 'message': 'Permission denied'})
    
    # Prevent deleting the last manager account
    if User.query.filter_by(role='manager').count() <= 1:
        employee = User.query.get_or_404(employee_id)
        if employee.role == 'manager':
            return jsonify({'success': False, 'message': 'Cannot delete the last manager account'})
    
    employee = User.query.get_or_404(employee_id)
    db.session.delete(employee)
    db.session.commit()
    
    return jsonify({'success': True})

@routes.route('/api/customers/<int:customer_id>', methods=['GET'])
@login_required
def get_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    # Get order history
    orders = Order.query.filter_by(customer_id=customer_id).order_by(Order.created_at.desc()).all()
    orders_data = []
    
    for order in orders:
        orders_data.append({
            'id': order.id,
            'order_number': order.order_number,
            'created_at': order.created_at.isoformat(),
            'total_amount': order.total_amount
        })
    
    return jsonify({
        'id': customer.id,
        'name': customer.name,
        'phone': customer.phone,
        'email': customer.email,
        'birthday': customer.birthday.isoformat() if customer.birthday else None,
        'rewards_points': customer.rewards_points,
        'orders': orders_data
    })

@routes.route('/api/customers', methods=['POST'])
@login_required
def add_customer():
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email', '')
    birthday = request.form.get('birthday', '')
    rewards_points = request.form.get('rewards_points', 0)
    
    # Check if phone number already exists
    if Customer.query.filter_by(phone=phone).first():
        return jsonify({'success': False, 'message': 'Phone number already registered'})
    
    customer = Customer(
        name=name,
        phone=phone,
        email=email,
        birthday=datetime.strptime(birthday, '%Y-%m-%d').date() if birthday else None,
        rewards_points=int(rewards_points)
    )
    
    db.session.add(customer)
    db.session.commit()
    
    return jsonify({'success': True, 'id': customer.id})

@routes.route('/api/customers/<int:customer_id>', methods=['PUT'])
@login_required
def update_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    name = request.form.get('name')
    phone = request.form.get('phone')
    email = request.form.get('email', '')
    birthday = request.form.get('birthday', '')
    
    # Check if phone number already exists with another customer
    existing = Customer.query.filter_by(phone=phone).first()
    if existing and existing.id != customer_id:
        return jsonify({'success': False, 'message': 'Phone number already registered'})
    
    customer.name = name
    customer.phone = phone
    customer.email = email
    customer.birthday = datetime.strptime(birthday, '%Y-%m-%d').date() if birthday else None
    
    db.session.commit()
    
    return jsonify({'success': True})

@routes.route('/api/customers/add-points', methods=['POST'])
@login_required
def add_customer_points():
    customer_id = request.form.get('customer_id')
    points = int(request.form.get('points'))
    reason = request.form.get('reason')
    
    customer = Customer.query.get_or_404(customer_id)
    customer.rewards_points += points
    
    db.session.commit()
    
    return jsonify({'success': True})

@routes.route('/api/customers/<int:customer_id>/birthday-promo', methods=['POST'])
@login_required
def send_birthday_promo(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    # Check if today is actually the customer's birthday
    today = date.today()
    if not customer.birthday or customer.birthday.day != today.day or customer.birthday.month != today.month:
        return jsonify({'success': False, 'message': 'Today is not this customer\'s birthday'})
    
    # In a real app, this would send an SMS or email with the birthday promotion
    # For now, we'll just return success
    return jsonify({'success': True})

# Export report endpoints
@routes.route('/api/reports/export/<format>', methods=['POST'])
@login_required
def export_report(format):
    report_type = request.form.get('report_type')
    date_range = request.form.get('date_range')
    start_date = request.form.get('date_start')
    end_date = request.form.get('date_end')
    
    # In a real app, generate report based on parameters
    # For demo, we'll just return a sample file
    
    if format == 'excel':
        # Create a sample Excel file
        df = pd.DataFrame({
            'Date': ['2023-06-01', '2023-06-02', '2023-06-03'],
            'Orders': [45, 52, 48],
            'Sales': [12500.00, 14200.00, 13800.00]
        })
        
        output = io.BytesIO()
        with pd.ExcelWriter(output) as writer:
            df.to_excel(writer, sheet_name='Sales Report', index=False)
        
        output.seek(0)
        
        filename = f"tokyo_tokyo_{report_type}_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, attachment_filename=filename)
    
    elif format == 'pdf':
        # In a real app, generate a PDF file
        # For demo, we'll return a text message
        return "PDF report generation would be implemented here"
    
    elif format == 'csv':
        # Create a sample CSV file
        df = pd.DataFrame({
            'Date': ['2023-06-01', '2023-06-02', '2023-06-03'],
            'Orders': [45, 52, 48],
            'Sales': [12500.00, 14200.00, 13800.00]
        })
        
        output = io.StringIO()
        df.to_csv(output, index=False)
        
        response = app.response_class(
            response=output.getvalue(),
            mimetype='text/csv',
            headers={"Content-disposition": f"attachment; filename=tokyo_tokyo_{report_type}_report_{datetime.now().strftime('%Y%m%d')}.csv"}
        )
        return response
    
    return jsonify({'success': False, 'message': 'Invalid export format'})

# Add missing route handlers that are referenced in base.html

@routes.route('/menu')
@login_required
def menu():
    categories = Category.query.all()
    products = Product.query.all()
    return render_template('menu.html', categories=categories, products=products)

@routes.route('/inventory')
@login_required
def inventory():
    ingredients = Ingredient.query.all()
    low_stock = Ingredient.query.filter(Ingredient.quantity <= Ingredient.threshold).all()
    suppliers = Supplier.query.all()
    inventory_logs = InventoryLog.query.order_by(InventoryLog.timestamp.desc()).limit(10).all()
    
    return render_template(
        'inventory.html',
        ingredients=ingredients,
        low_stock=low_stock,
        suppliers=suppliers,
        inventory_logs=inventory_logs
    )

@routes.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@routes.route('/employees')
@login_required
def employees():
    if current_user.role != 'manager':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('routes.dashboard'))
        
    employees = User.query.all()
    
    # Sample data for current shifts and activity
    current_shifts = []
    recent_activity = []
    
    return render_template(
        'employees.html',
        employees=employees,
        current_shifts=current_shifts,
        recent_activity=recent_activity
    )

@routes.route('/customers')
@login_required
def customers():
    if current_user.role != 'manager':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('routes.dashboard'))
        
    customers = Customer.query.all()
    
    # Get customers with birthdays today
    today = date.today()
    birthday_customers = [c for c in customers if c.birthday and c.birthday.day == today.day and c.birthday.month == today.month]
    
    return render_template(
        'customers.html',
        customers=customers,
        birthday_customers=birthday_customers,
        is_birthday=lambda c: c.birthday and c.birthday.day == today.day and c.birthday.month == today.month
    )

# Replace the app error handlers with Blueprint error handlers
# Error handlers need to be moved to app.py since they need app context
# We'll add these custom Blueprint handlers instead

@routes.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@routes.app_errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500
