from flask import Flask, render_template
from extensions import db, login_manager
from werkzeug.security import generate_password_hash

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'tokyo_tokyo_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tokyo_pos.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Import and register blueprints
    from routes import routes
    app.register_blueprint(routes)
    
    # Register error handlers at app level
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500
    
    return app

# Create app instance
app = create_app()

# Initialize database and create admin user
with app.app_context():
    # Import models here to avoid circular imports
    from models import User
    
    # Create tables
    db.create_all()
    
    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            name='Admin User',
            role='manager'
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created")
    
    # Create cashier user if not exists
    if not User.query.filter_by(username='cashier').first():
        cashier = User(
            username='cashier',
            password=generate_password_hash('cashier123'),
            name='Cashier User',
            role='cashier'
        )
        db.session.add(cashier)
        db.session.commit()
        print("Cashier user created")

if __name__ == '__main__':
    app.run(debug=True)
