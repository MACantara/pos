from flask import Blueprint, render_template, abort # Import abort
from flask_login import login_required, current_user

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/')
@login_required
def view_reports():
    # Check if the user has the 'manager' role
    if current_user.role != 'manager':
        abort(403) # Trigger the 403 error handler defined in app.py

    # If the user is a manager, proceed to render the reports page
    return render_template('reports.html')

# Other report-related routes might go here
