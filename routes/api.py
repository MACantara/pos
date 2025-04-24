from flask import Blueprint, request, jsonify, abort, send_file
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from extensions import db
from models import User, Category, Product, Ingredient, Supplier, Order, OrderItem, Customer, InventoryLog, ProductIngredient
from datetime import datetime, date, timedelta
import os
import io # For file export later if needed

api_bp = Blueprint('api', __name__, url_prefix='/api')

# --- Helper Functions ---
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Employee API ---
@api_bp.route('/employees', methods=['POST'])
@login_required
def add_employee():
    if current_user.role != 'manager':
        abort(403)
    
    data = request.form
    name = data.get('name')
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    if not all([name, username, password, role]):
         return jsonify({'success': False, 'message': 'Missing required fields.'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username already exists.'}), 400

    new_employee = User(
        name=name,
        username=username,
        password=generate_password_hash(password),
        role=role
    )
    db.session.add(new_employee)
    db.session.commit()
    return jsonify({'success': True, 'id': new_employee.id})

@api_bp.route('/employees/<int:employee_id>', methods=['GET'])
@login_required
def get_employee(employee_id):
    # Used by edit modal to fetch details
    if current_user.role != 'manager':
         abort(403)
    employee = User.query.get_or_404(employee_id)
    return jsonify({
        'id': employee.id,
        'name': employee.name,
        'username': employee.username,
        'role': employee.role
    })

@api_bp.route('/employees/<int:employee_id>', methods=['PUT'])
@login_required
def update_employee(employee_id):
    if current_user.role != 'manager':
        abort(403)
    
    employee = User.query.get_or_404(employee_id)
    data = request.form
    name = data.get('name')
    username = data.get('username')
    role = data.get('role')

    if not all([name, username, role]):
         return jsonify({'success': False, 'message': 'Missing required fields.'}), 400

    # Check if username is being changed to one that already exists
    existing_user = User.query.filter(User.username == username, User.id != employee_id).first()
    if existing_user:
         return jsonify({'success': False, 'message': 'Username already exists.'}), 400

    employee.name = name
    employee.username = username
    employee.role = role
    db.session.commit()
    return jsonify({'success': True})


@api_bp.route('/employees/<int:employee_id>/reset-password', methods=['POST'])
@login_required
def reset_employee_password(employee_id):
    if current_user.role != 'manager':
        abort(403)
    
    employee = User.query.get_or_404(employee_id)
    password = request.form.get('password')

    if not password:
        return jsonify({'success': False, 'message': 'Password cannot be empty.'}), 400
    
    employee.password = generate_password_hash(password)
    db.session.commit()
    
    return jsonify({'success': True})

@api_bp.route('/employees/<int:employee_id>', methods=['DELETE'])
@login_required
def delete_employee(employee_id):
    if current_user.role != 'manager':
        abort(403)
    
    employee = User.query.get_or_404(employee_id)

    # Prevent deleting self
    if employee.id == current_user.id:
         return jsonify({'success': False, 'message': 'You cannot delete your own account.'}), 400

    # Prevent deleting the last manager account
    if employee.role == 'manager' and User.query.filter_by(role='manager').count() <= 1:
        return jsonify({'success': False, 'message': 'Cannot delete the last manager account.'}), 400
    
    # Consider implications: reassign orders? Mark as inactive instead?
    # Simple deletion for now:
    db.session.delete(employee)
    db.session.commit()
    
    return jsonify({'success': True})

# --- Customer API ---
@api_bp.route('/customers/<int:customer_id>', methods=['GET'])
@login_required
def get_customer(customer_id):
    # Allow managers or potentially cashiers if needed for POS lookup
    # if current_user.role not in ['manager', 'cashier']: abort(403)
    
    customer = Customer.query.get_or_404(customer_id)
    
    # Get order history (limit for performance)
    orders = Order.query.filter_by(customer_id=customer_id)\
                .order_by(Order.created_at.desc())\
                .limit(10).all() # Limit history shown in modal
    orders_data = [{
        'id': order.id,
        'order_number': order.order_number,
        'created_at': order.created_at.isoformat(),
        'total_amount': order.total_amount,
        'points_earned': int(order.total_amount / 100) # Example calculation
    } for order in orders]
    
    return jsonify({
        'id': customer.id,
        'name': customer.name,
        'phone': customer.phone,
        'email': customer.email,
        'birthday': customer.birthday.isoformat() if customer.birthday else None,
        'rewards_points': customer.rewards_points,
        'orders': orders_data
    })

@api_bp.route('/customers', methods=['POST'])
@login_required
def add_customer():
    # Allow managers or cashiers
    if current_user.role not in ['manager', 'cashier']: abort(403)

    data = request.form
    name = data.get('name')
    phone = data.get('phone')
    email = data.get('email', None) # Use None if empty
    birthday_str = data.get('birthday', None)
    rewards_points = data.get('rewards_points', 0)

    if not name:
         return jsonify({'success': False, 'message': 'Customer name is required.'}), 400

    # Validate uniqueness if phone/email provided
    if phone and Customer.query.filter_by(phone=phone).first():
        return jsonify({'success': False, 'message': 'Phone number already exists.'}), 400
    if email and Customer.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email address already exists.'}), 400
    
    birthday = None
    if birthday_str:
        try:
            birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
        except ValueError:
             return jsonify({'success': False, 'message': 'Invalid birthday format. Use YYYY-MM-DD.'}), 400

    customer = Customer(
        name=name,
        phone=phone,
        email=email,
        birthday=birthday,
        rewards_points=int(rewards_points)
    )
    
    db.session.add(customer)
    db.session.commit()
    
    return jsonify({'success': True, 'id': customer.id})

@api_bp.route('/customers/<int:customer_id>', methods=['PUT'])
@login_required
def update_customer(customer_id):
    # Allow managers or cashiers
    if current_user.role not in ['manager', 'cashier']: abort(403)

    customer = Customer.query.get_or_404(customer_id)
    data = request.form
    name = data.get('name')
    phone = data.get('phone')
    email = data.get('email', None)
    birthday_str = data.get('birthday', None)

    if not name:
         return jsonify({'success': False, 'message': 'Customer name is required.'}), 400

    # Check uniqueness if phone/email changed
    if phone and phone != customer.phone and Customer.query.filter(Customer.phone == phone, Customer.id != customer_id).first():
        return jsonify({'success': False, 'message': 'Phone number already exists.'}), 400
    if email and email != customer.email and Customer.query.filter(Customer.email == email, Customer.id != customer_id).first():
        return jsonify({'success': False, 'message': 'Email address already exists.'}), 400

    birthday = None
    if birthday_str:
        try:
            birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
        except ValueError:
             return jsonify({'success': False, 'message': 'Invalid birthday format. Use YYYY-MM-DD.'}), 400
    
    customer.name = name
    customer.phone = phone
    customer.email = email
    customer.birthday = birthday
    
    db.session.commit()
    
    return jsonify({'success': True})

@api_bp.route('/customers/add-points', methods=['POST'])
@login_required
def add_customer_points():
     # Allow managers or cashiers
    if current_user.role not in ['manager', 'cashier']: abort(403)

    customer_id = request.form.get('customer_id')
    points_str = request.form.get('points')
    # reason = request.form.get('reason') # Optional: Log reason for adding points

    if not customer_id or not points_str:
        return jsonify({'success': False, 'message': 'Customer ID and points are required.'}), 400
        
    try:
        points = int(points_str)
        if points <= 0: raise ValueError("Points must be positive.")
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid points value.'}), 400

    customer = Customer.query.get_or_404(customer_id)
    customer.rewards_points += points
    
    db.session.commit()
    
    return jsonify({'success': True, 'new_points': customer.rewards_points})

@api_bp.route('/customers/<int:customer_id>/birthday-promo', methods=['POST'])
@login_required
def send_birthday_promo(customer_id):
    # Allow managers or cashiers
    if current_user.role not in ['manager', 'cashier']: abort(403)

    customer = Customer.query.get_or_404(customer_id)
    
    # Check if today is actually the customer's birthday
    today = date.today()
    if not customer.birthday or customer.birthday.day != today.day or customer.birthday.month != today.month:
        return jsonify({'success': False, 'message': "It's not this customer's birthday today."}), 400
    
    # In a real app, this would trigger sending an SMS or email
    print(f"Simulating sending birthday promo to {customer.name} ({customer.phone or customer.email})")
    
    return jsonify({'success': True, 'message': 'Birthday promo simulated.'})


# --- Product & Category API ---
@api_bp.route('/categories', methods=['POST'])
@login_required
def add_category():
    if current_user.role != 'manager': abort(403)
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'success': False, 'message': 'Category name required.'}), 400
    if Category.query.filter_by(name=name).first():
        return jsonify({'success': False, 'message': 'Category name already exists.'}), 400
    
    new_category = Category(name=name)
    db.session.add(new_category)
    db.session.commit()
    return jsonify({'success': True, 'id': new_category.id, 'name': new_category.name})

# Add PUT and DELETE for categories as needed

@api_bp.route('/products', methods=['POST'])
@login_required
def add_product():
    if current_user.role != 'manager': abort(403)
    
    data = request.form
    name = data.get('name')
    category_id = data.get('category_id')
    price_str = data.get('price')
    description = data.get('description', '')
    available_str = data.get('available', 'true')

    if not all([name, category_id, price_str]):
        return jsonify({'success': False, 'message': 'Name, category, and price are required.'}), 400

    try:
        price = float(price_str)
        if price < 0: raise ValueError()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid price.'}), 400

    available = available_str.lower() == 'true'
    
    filename = 'default.jpg'
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Ensure the upload folder exists
            upload_folder = os.path.join(os.getcwd(), 'static', 'uploads') # Adjust path as needed
            os.makedirs(upload_folder, exist_ok=True) 
            file.save(os.path.join(upload_folder, filename))
        elif file.filename != '':
             return jsonify({'success': False, 'message': 'Invalid image file type.'}), 400

    new_product = Product(
        name=name,
        category_id=category_id,
        price=price,
        description=description,
        available=available,
        image=filename
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'success': True, 'id': new_product.id})

@api_bp.route('/products/<int:product_id>', methods=['GET'])
@login_required
def get_product(product_id):
    # Used by edit modal
    if current_user.role != 'manager': abort(403)
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'category_id': product.category_id,
        'price': product.price,
        'description': product.description,
        'available': product.available,
        'image': product.image
    })

@api_bp.route('/products/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    if current_user.role != 'manager': abort(403)
    product = Product.query.get_or_404(product_id)
    
    data = request.form
    name = data.get('name')
    category_id = data.get('category_id')
    price_str = data.get('price')
    description = data.get('description', '')
    available_str = data.get('available', 'true')

    if not all([name, category_id, price_str]):
        return jsonify({'success': False, 'message': 'Name, category, and price are required.'}), 400

    try:
        price = float(price_str)
        if price < 0: raise ValueError()
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid price.'}), 400

    available = available_str.lower() == 'true'
    
    product.name = name
    product.category_id = category_id
    product.price = price
    product.description = description
    product.available = available

    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Ensure the upload folder exists
            upload_folder = os.path.join(os.getcwd(), 'static', 'uploads') # Adjust path as needed
            os.makedirs(upload_folder, exist_ok=True)
            # Optional: Delete old image file before saving new one
            # if product.image != 'default.jpg':
            #     try: os.remove(os.path.join(upload_folder, product.image))
            #     except OSError: pass # Ignore if file doesn't exist
            file.save(os.path.join(upload_folder, filename))
            product.image = filename
        elif file.filename != '':
             return jsonify({'success': False, 'message': 'Invalid image file type.'}), 400

    db.session.commit()
    return jsonify({'success': True})

@api_bp.route('/products/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    if current_user.role != 'manager': abort(403)
    product = Product.query.get_or_404(product_id)
    
    # Optional: Check if product is in any non-completed orders before deleting?
    
    # Delete image file (optional)
    # if product.image != 'default.jpg':
    #     try: 
    #         upload_folder = os.path.join(os.getcwd(), 'static', 'uploads')
    #         os.remove(os.path.join(upload_folder, product.image))
    #     except OSError: pass

    db.session.delete(product)
    db.session.commit()
    return jsonify({'success': True})

@api_bp.route('/products/<int:product_id>/toggle', methods=['POST'])
@login_required
def toggle_product_availability(product_id):
    if current_user.role != 'manager': abort(403)
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    available = data.get('available')

    if available is None:
         return jsonify({'success': False, 'message': 'Availability status required.'}), 400

    product.available = bool(available)
    db.session.commit()
    return jsonify({'success': True, 'available': product.available})

# --- Order API ---
@api_bp.route('/orders/<int:order_id>', methods=['GET'])
@login_required
def get_order_details(order_id):
    # Allow managers or cashiers
    if current_user.role not in ['manager', 'cashier']: abort(403)

    order = Order.query.options(
        db.joinedload(Order.items).joinedload(OrderItem.product),
        db.joinedload(Order.staff)
    ).get_or_404(order_id)

    items_data = [{
        'id': item.id,
        'name': item.product.name,
        'quantity': item.quantity,
        'price': item.price,
        'notes': item.notes
    } for item in order.items]

    return jsonify({
        'id': order.id,
        'order_number': order.order_number,
        'created_at': order.created_at.isoformat(),
        'order_type': order.order_type,
        'status': order.status,
        'staff_name': order.staff.name,
        'items': items_data,
        'subtotal': order.subtotal,
        'tax': order.tax,
        'total_amount': order.total_amount,
        'payment_method': order.payment_method,
        'customer_id': order.customer_id
    })

@api_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
     # Allow managers or cashiers
    if current_user.role not in ['manager', 'cashier']: abort(403)

    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    new_status = data.get('status')

    valid_statuses = ['pending', 'in-progress', 'completed', 'cancelled']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'message': 'Invalid status.'}), 400

    # Add logic here if status changes have side effects (e.g., inventory adjustments for cancelled)
    order.status = new_status
    if new_status == 'completed' and not order.completed_at:
        order.completed_at = datetime.utcnow()
    elif new_status != 'completed':
         order.completed_at = None # Reset if changed away from completed

    db.session.commit()
    return jsonify({'success': True, 'new_status': order.status})


# --- Inventory & Supplier API ---
# Add POST, PUT, DELETE for Ingredients and Suppliers as needed
# Add POST for InventoryLog (manual adjustments, receiving stock)

# --- Report API ---
@api_bp.route('/reports/generate', methods=['POST'])
@login_required
def generate_report_data():
    if current_user.role not in ['manager']: abort(403) # Only managers for reports

    filters = request.get_json()
    report_type = filters.get('report_type', 'sales')
    date_range = filters.get('date_range', 'today')
    start_date_str = filters.get('date_start')
    end_date_str = filters.get('date_end')

    # Determine date range
    end_date = datetime.utcnow().date()
    start_date = end_date

    if date_range == 'today':
        pass # Default is today
    elif date_range == 'yesterday':
        start_date = end_date - timedelta(days=1)
        end_date = start_date
    elif date_range == 'this_week':
        start_date = end_date - timedelta(days=end_date.weekday())
    elif date_range == 'last_week':
        end_date = end_date - timedelta(days=end_date.weekday() + 1)
        start_date = end_date - timedelta(days=6)
    elif date_range == 'this_month':
        start_date = end_date.replace(day=1)
    elif date_range == 'last_month':
        end_date = end_date.replace(day=1) - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif date_range == 'custom' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            if start_date > end_date: raise ValueError("Start date cannot be after end date.")
        except ValueError as e:
            return jsonify({'success': False, 'message': f'Invalid custom date range: {e}'}), 400
    
    # Convert dates to datetimes for filtering
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    # --- Fetch Data Based on Report Type ---
    # This is a simplified example. Real reports would be more complex.
    
    # Base query for orders in range
    orders_in_range = Order.query.filter(
        Order.created_at >= start_dt, 
        Order.created_at <= end_dt,
        Order.status == 'completed' # Usually only completed orders for sales reports
    )

    total_sales = orders_in_range.with_entities(db.func.sum(Order.total_amount)).scalar() or 0
    orders_count = orders_in_range.count()
    avg_order_value = total_sales / orders_count if orders_count > 0 else 0

    # Top Items
    top_items_query = db.session.query(
        Product.name, 
        db.func.sum(OrderItem.quantity).label('total_quantity'),
        db.func.sum(OrderItem.quantity * OrderItem.price).label('total_revenue')
    ).join(OrderItem, OrderItem.product_id == Product.id)\
     .join(Order, Order.id == OrderItem.order_id)\
     .filter(Order.created_at >= start_dt, Order.created_at <= end_dt, Order.status == 'completed')\
     .group_by(Product.name)\
     .order_by(db.desc('total_revenue'))\
     .limit(5)
    top_items = [{'name': i[0], 'quantity': int(i[1]), 'revenue': float(i[2])} for i in top_items_query.all()]

    # Payment Methods
    payment_methods_query = db.session.query(
        Order.payment_method,
        db.func.count(Order.id).label('count'),
        db.func.sum(Order.total_amount).label('total_amount')
    ).filter(Order.created_at >= start_dt, Order.created_at <= end_dt, Order.status == 'completed')\
     .group_by(Order.payment_method)\
     .order_by(db.desc('total_amount'))
    payment_methods = [{'method': p[0], 'count': p[1], 'amount': float(p[2])} for p in payment_methods_query.all()]

    # Staff Performance
    staff_perf_query = db.session.query(
        User.name,
        db.func.count(Order.id).label('order_count'),
        db.func.sum(Order.total_amount).label('total_sales')
    ).join(Order, Order.user_id == User.id)\
     .filter(Order.created_at >= start_dt, Order.created_at <= end_dt, Order.status == 'completed')\
     .group_by(User.name)\
     .order_by(db.desc('total_sales'))
    staff_performance = [{'name': s[0], 'orders': s[1], 'sales': float(s[2])} for s in staff_perf_query.all()]

    # Sales Trend (Example: Daily sales for the period)
    sales_trend_query = db.session.query(
        db.func.date(Order.created_at).label('sale_date'),
        db.func.sum(Order.total_amount).label('daily_total')
    ).filter(Order.created_at >= start_dt, Order.created_at <= end_dt, Order.status == 'completed')\
     .group_by('sale_date')\
     .order_by('sale_date')
    sales_trend = [{'date': d[0].isoformat(), 'sales': float(d[1])} for d in sales_trend_query.all()]


    # --- Assemble Response ---
    report_data = {
        'summary': {
            'total_sales': total_sales,
            'orders_count': orders_count,
            'avg_order_value': avg_order_value,
            # Add top category calculation if needed
        },
        'top_items': top_items,
        'payment_methods': payment_methods,
        'staff_performance': staff_performance,
        'sales_trend': sales_trend,
        # Add other data sections based on report_type
    }

    return jsonify({'success': True, 'data': report_data})


@api_bp.route('/reports/export/<format>', methods=['POST'])
@login_required
def export_report(format):
    if current_user.role != 'manager': abort(403)
    
    # Get filters from form data (similar to generate_report_data)
    filters = request.form 
    # ... parse filters ...

    # --- Generate Report Data (again, or reuse logic) ---
    # ... fetch data based on filters ...
    report_data = { # Example structure
        'summary': {'total_sales': 1234.56}, 
        'details': [{'item': 'A', 'qty': 10}] 
    } 

    # --- Generate File Content ---
    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    mimetype = None
    file_content = None

    if format == 'csv':
        filename += ".csv"
        mimetype = 'text/csv'
        # Use io.StringIO and csv module to generate CSV content
        output = io.StringIO()
        # writer = csv.writer(output)
        # writer.writerow(['Header1', 'Header2'])
        # writer.writerow(['Data1', 'Data2'])
        # file_content = output.getvalue().encode('utf-8')
        file_content = b"Header1,Header2\nData1,Data2" # Placeholder

    elif format == 'excel':
        filename += ".xlsx"
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        # Use pandas or openpyxl to generate Excel content in memory (io.BytesIO)
        output = io.BytesIO()
        # import pandas as pd
        # df = pd.DataFrame(report_data['details'])
        # df.to_excel(output, index=False)
        # file_content = output.getvalue()
        file_content = b"Excel Content Placeholder" # Placeholder

    elif format == 'pdf':
        filename += ".pdf"
        mimetype = 'application/pdf'
        # Use libraries like ReportLab or WeasyPrint to generate PDF content in memory (io.BytesIO)
        output = io.BytesIO()
        # from reportlab.pdfgen import canvas
        # c = canvas.Canvas(output)
        # c.drawString(100, 750, "Report Title")
        # c.save()
        # file_content = output.getvalue()
        file_content = b"%PDF-1.4\n..." # Placeholder
    else:
        return jsonify({'success': False, 'message': 'Invalid export format'}), 400

    if file_content:
        return send_file(
            io.BytesIO(file_content),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename # Use download_name instead of attachment_filename
        )
    else:
         return jsonify({'success': False, 'message': 'Failed to generate report content'}), 500
