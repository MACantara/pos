from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import login_required, current_user
from extensions import db
from models import User # Import necessary models

employees_bp = Blueprint('employees', __name__, url_prefix='/employees')

@employees_bp.route('/')
@login_required
def view_employees():
    # Only managers can access this page
    if current_user.role != 'manager':
        abort(403) # Forbidden
        
    employees = User.query.order_by(User.name).all()
    
    # Sample data - replace with real data if shift/activity models exist
    current_shifts = [] 
    recent_activity = [] 
    
    return render_template(
        'employees.html',
        employees=employees,
        current_shifts=current_shifts,
        recent_activity=recent_activity
    )

# Note: API endpoints for managing employees 
# should be in routes/api.py
