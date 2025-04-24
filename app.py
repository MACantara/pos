from flask import Flask, render_template, redirect, url_for, request
from extensions import db, login_manager
from werkzeug.security import generate_password_hash
from flask_login import current_user # Import current_user
import os # Import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'tokyo_tokyo_secret_key' # Change in production!
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tokyo_pos.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = 'static/uploads' # Define upload folder

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' # Set the login view endpoint using blueprint name
    login_manager.login_message_category = 'info' # Optional: flash message category

    # Import and register blueprints from the routes package
    from routes.auth import auth_bp
    from routes.pos import pos_bp
    from routes.dashboard import dashboard_bp
    from routes.orders import orders_bp
    from routes.menu import menu_bp
    from routes.inventory import inventory_bp
    from routes.reports import reports_bp
    from routes.employees import employees_bp
    from routes.customers import customers_bp
    from routes.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(pos_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(api_bp)
    
    # Register error handlers at app level
    @app.errorhandler(404)
    def page_not_found(e):
        # Customize 404 page if needed
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
         # Log the error e
        print(f"Server Error: {e}")
        return render_template('500.html'), 500

    @app.errorhandler(403)
    def forbidden(e):
        # Custom forbidden page
        return render_template('403.html'), 403

    # Middleware to restrict cashier access globally (alternative to per-blueprint)
    @app.before_request
    def restrict_cashier_access():
        # Allow access to static files and auth routes unconditionally
        # Also allow access to API endpoints needed by cashier (like customer lookup)
        if request.endpoint and (
            request.endpoint.startswith('static') or 
            request.endpoint.startswith('auth.') or
            request.endpoint == 'api.get_customer' # Example allowed API endpoint
            ):
            return

        if current_user.is_authenticated and current_user.role == 'cashier':
            # Define allowed endpoints for cashiers (main POS screen)
            allowed_endpoints = ['pos.new_order'] 
            
            # Check if the requested endpoint is allowed
            if request.endpoint not in allowed_endpoints:
                # Redirect cashier to their main page if trying to access restricted areas
                return redirect(url_for('pos.new_order'))

    return app

# Create app instance
app = create_app()

# Initialize database and create default users
with app.app_context():
    # Import models from the new structure
    from models import User, Category, Product # Import others as needed for seeding

    # Create tables
    db.create_all()
    
    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'), # Change this default password
            name='Admin User',
            role='manager'
        )
        db.session.add(admin)
        print("Admin user created")
    
    # Create cashier user if not exists
    if not User.query.filter_by(username='cashier').first():
        cashier = User(
            username='cashier',
            password=generate_password_hash('cashier123'), # Change this default password
            name='Cashier User',
            role='cashier'
        )
        db.session.add(cashier)
        print("Cashier user created")

    # Optional: Seed initial data (Categories, etc.)
    if not Category.query.first():
        print("Seeding initial categories...")
        categories_to_add = ['Ramen', 'Bento', 'Donburi', 'Sushi/Maki', 'Sides', 'Desserts', 'Drinks']
        for cat_name in categories_to_add:
            db.session.add(Category(name=cat_name))
        print("Categories seeded.")

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error during initial setup: {e}")


if __name__ == '__main__':
    # Ensure upload folder exists
    upload_folder = os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_folder, exist_ok=True)
    app.run(debug=True) # Turn off debug in production
