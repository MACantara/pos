from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from extensions import db, login_manager
from models import User # Import User from the models package

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'cashier':
            return redirect(url_for('pos.new_order')) # Reference blueprint name
        else:
            return redirect(url_for('dashboard.view')) # Reference blueprint name
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect based on role if already logged in
        if current_user.role == 'cashier':
            return redirect(url_for('pos.new_order'))
        else:
            return redirect(url_for('dashboard.view'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            
            # Redirect cashiers directly to the POS screen
            if user.role == 'cashier':
                return redirect(url_for('pos.new_order'))
            else:
                # Redirect other roles to dashboard
                return redirect(url_for('dashboard.view'))
        else:
            flash('Invalid username or password', 'error')
            
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('auth.login'))

# Middleware to restrict cashier access - applied within app.py or individually
# @auth_bp.before_request
# def restrict_cashier_access():
#     # This logic might be better placed in app.py or applied per-blueprint/route
#     if current_user.is_authenticated and current_user.role == 'cashier':
#         allowed_endpoints = ['pos.new_order', 'auth.logout', 'static']
#         if request.endpoint not in allowed_endpoints and not request.endpoint.startswith('static'):
#             return redirect(url_for('pos.new_order'))
