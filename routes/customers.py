from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from extensions import db
from models import Customer # Import necessary models
from datetime import date

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')

@customers_bp.route('/')
@login_required
def view_customers():
    # Only managers can access this page
    if current_user.role != 'manager':
         abort(403) # Forbidden
        
    customers = Customer.query.order_by(Customer.name).all()
    
    # Get customers with birthdays today
    today = date.today()
    # Function to check birthday easily in template
    def is_birthday(customer):
        return customer.birthday and customer.birthday.day == today.day and customer.birthday.month == today.month

    return render_template(
        'customers.html',
        customers=customers,
        is_birthday=is_birthday # Pass function to template
    )

# Note: API endpoints for managing customers 
# should be in routes/api.py
