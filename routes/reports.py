from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
def view_reports():
     # Redirect cashier away
    if current_user.role == 'cashier':
        return redirect(url_for('pos.new_order'))
        
    # The actual report data generation will likely happen via API calls from JS
    return render_template('reports.html')

# Note: API endpoints for generating and exporting reports 
# should be in routes/api.py
