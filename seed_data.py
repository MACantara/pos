import random
import uuid
from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash

# Import db directly from extensions instead of from app
from extensions import db
# Import models directly
from models import User, Supplier, Category, Product, Ingredient, ProductIngredient, Customer, Order, OrderItem, InventoryLog

def clear_data():
    """Clears data from tables in an order that respects foreign keys."""
    print("Clearing existing data...")
    # Delete in reverse order of dependencies or disable FK checks temporarily
    # This order might need adjustment based on exact FK constraints and cascade settings
    db.session.query(InventoryLog).delete()
    db.session.query(OrderItem).delete()
    db.session.query(Order).delete()
    db.session.query(ProductIngredient).delete()
    db.session.query(Product).delete()
    db.session.query(Ingredient).delete()
    db.session.query(Supplier).delete()
    db.session.query(Category).delete()
    db.session.query(Customer).delete()
    db.session.query(User).delete()
    db.session.commit()
    print("Data cleared.")

def seed_data():
    """Seeds the database with sample data."""
    print("Seeding data...")
    try:
        # --- Create Default Users (if they don't exist) ---
        print("Checking/Creating default users...")
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password=generate_password_hash('admin123', method='pbkdf2:sha256'), # Use consistent hashing
                name='Admin User',
                role='manager'
            )
            db.session.add(admin)
            print("Default admin user created.")
        else:
            print("Default admin user already exists.")

        if not User.query.filter_by(username='cashier').first():
            cashier = User(
                username='cashier',
                password=generate_password_hash('cashier123', method='pbkdf2:sha256'), # Use consistent hashing
                name='Cashier User',
                role='cashier'
            )
            db.session.add(cashier)
            print("Default cashier user created.")
        else:
            print("Default cashier user already exists.")
        
        db.session.flush() # Ensure default users get IDs if needed below

        # --- Create Additional Sample Users (Optional) ---
        print("Creating additional sample users...")
        # Get existing default users to potentially reuse their IDs or avoid conflicts
        admin_user = User.query.filter_by(username='admin').first()
        cashier_user = User.query.filter_by(username='cashier').first()
        
        # Example: Add more users only if they don't exist
        sample_users_data = [
            {'username': 'cashier1', 'password': 'password', 'name': 'Alice Smith', 'role': 'cashier'},
            {'username': 'kitchen1', 'password': 'password', 'name': 'Bob Johnson', 'role': 'kitchen'},
            {'username': 'manager1', 'password': 'password', 'name': 'Charlie Brown', 'role': 'manager'}
        ]
        
        users = [admin_user, cashier_user] # Start with default users
        for user_data in sample_users_data:
            if not User.query.filter_by(username=user_data['username']).first():
                new_user = User(
                    username=user_data['username'],
                    password=generate_password_hash(user_data['password'], method='pbkdf2:sha256'),
                    name=user_data['name'],
                    role=user_data['role']
                )
                db.session.add(new_user)
                users.append(new_user) # Add to list for potential use later in script
                print(f"Sample user {user_data['username']} created.")
            else:
                print(f"Sample user {user_data['username']} already exists.")
                # Optionally fetch and add existing sample user to the 'users' list if needed
                existing_sample_user = User.query.filter_by(username=user_data['username']).first()
                if existing_sample_user not in users:
                     users.append(existing_sample_user)

        db.session.flush() # Flush to get IDs of any newly added sample users

        # --- Create Suppliers ---
        print("Creating suppliers...")
        suppliers = [
            Supplier(name='Fresh Produce Co.', contact_person='Dave Lee', phone='123-456-7890', email='dave@freshproduce.com', address='1 Farm Road'),
            Supplier(name='Meat Masters', contact_person='Eve Davis', phone='987-654-3210', email='eve@meatmasters.com', address='2 Butcher Lane'),
            Supplier(name='Beverage World', contact_person='Frank Green', phone='555-123-4567', email='frank@bevworld.com', address='3 Drink Street')
        ]
        db.session.add_all(suppliers)
        db.session.flush() # Get supplier IDs

        # --- Create Categories ---
        print("Creating categories...")
        categories = [
            Category(name='Appetizers'),
            Category(name='Main Courses'),
            Category(name='Desserts'),
            Category(name='Beverages')
        ]
        db.session.add_all(categories)
        db.session.flush() # Get category IDs

        # --- Create Ingredients ---
        print("Creating ingredients...")
        ingredients = [
            Ingredient(name='Tomato', quantity=50.0, unit='kg', threshold=5.0, supplier_id=suppliers[0].id),
            Ingredient(name='Chicken Breast', quantity=30.0, unit='kg', threshold=3.0, supplier_id=suppliers[1].id),
            Ingredient(name='Lettuce', quantity=20.0, unit='heads', threshold=5.0, supplier_id=suppliers[0].id),
            Ingredient(name='Bread Buns', quantity=100.0, unit='pcs', threshold=20.0, supplier_id=suppliers[0].id),
            Ingredient(name='Cheese Slices', quantity=5.0, unit='kg', threshold=1.0, supplier_id=suppliers[1].id),
            Ingredient(name='Cola', quantity=200.0, unit='cans', threshold=24.0, supplier_id=suppliers[2].id),
            Ingredient(name='Ice Cream', quantity=10.0, unit='liters', threshold=2.0, supplier_id=suppliers[2].id),
            Ingredient(name='Potatoes', quantity=40.0, unit='kg', threshold=10.0, supplier_id=suppliers[0].id)
        ]
        db.session.add_all(ingredients)
        db.session.flush() # Get ingredient IDs

        # --- Create Initial Inventory Logs ---
        print("Creating initial inventory logs...")
        initial_logs = []
        admin_user_for_log = User.query.filter_by(role='manager').first() # Find a manager
        if not admin_user_for_log: # Fallback if no manager found
             admin_user_for_log = User.query.first() 
        for ingredient in ingredients:
            initial_logs.append(InventoryLog(
                ingredient_id=ingredient.id,
                quantity_change=ingredient.quantity,
                reason='initial_stock',
                user_id=admin_user_for_log.id # Use fetched admin/manager user ID
            ))
        db.session.add_all(initial_logs)

        # --- Create Products ---
        print("Creating products...")
        # Ensure categories are flushed and available
        appetizer_cat = Category.query.filter_by(name='Appetizers').first()
        main_course_cat = Category.query.filter_by(name='Main Courses').first()
        dessert_cat = Category.query.filter_by(name='Desserts').first()
        beverage_cat = Category.query.filter_by(name='Beverages').first()

        products = [
            Product(name='Takoyaki Balls', description='Japanese octopus balls', price=150.00, category_id=appetizer_cat.id, image='balls.jpg'),
            Product(name='Beef Bowl', description='Sliced beef over rice', price=350.00, category_id=main_course_cat.id, image='beef.jpg'),
            Product(name='Cheesy Baked Rice', description='Baked rice with cheese topping', price=280.00, category_id=main_course_cat.id, image='cheesy.jpg'),
            Product(name='Gyudon', description='Beef and onion rice bowl', price=320.00, category_id=main_course_cat.id, image='gyudon.jpg'),
            Product(name='Chicken Katsu', description='Fried chicken cutlet', price=300.00, category_id=main_course_cat.id, image='katsu.jpg'),
            Product(name='Maki Roll', description='Assorted sushi rolls', price=250.00, category_id=appetizer_cat.id, image='maki.jpg'),
            Product(name='Beef Misono', description='Teppanyaki style beef', price=450.00, category_id=main_course_cat.id, image='misono.jpg'),
            Product(name='Oyakodon', description='Chicken and egg rice bowl', price=290.00, category_id=main_course_cat.id, image='oyakodon.jpg'),
            Product(name='Grilled Salmon', description='Grilled salmon fillet', price=480.00, category_id=main_course_cat.id, image='salmon.jpg'),
            Product(name='Tonkatsu', description='Fried pork cutlet', price=330.00, category_id=main_course_cat.id, image='tonkatsu.jpg'),
            Product(name='Wagyu Cubes', description='Grilled wagyu beef cubes', price=650.00, category_id=main_course_cat.id, image='wagyu.jpg'),
            # Keep Cola and Ice Cream if desired, or remove them
            Product(name='Cola Can', description='330ml Can of Cola', price=50.00, category_id=beverage_cat.id, image='cola.jpg'),
            Product(name='Ice Cream Scoop', description='Single scoop of vanilla ice cream', price=70.00, category_id=dessert_cat.id, image='ice_cream.jpg')
        ]
        db.session.add_all(products)
        db.session.flush() # Get product IDs

        # --- Create Product Ingredients ---
        # !!! IMPORTANT: These are PLACEHOLDERS. Update with actual recipe ingredients and quantities. !!!
        print("Creating product ingredients (placeholders)...")
        product_ingredients = [
            # Chicken Katsu (Example - uses existing chicken, assumes need for potatoes/oil not listed)
            ProductIngredient(product_id=Product.query.filter_by(name='Chicken Katsu').first().id, ingredient_id=Ingredient.query.filter_by(name='Chicken Breast').first().id, quantity_needed=0.18), # 180g chicken
            # Gyudon (Example - assumes beef, onion, rice - needs more ingredients)
            ProductIngredient(product_id=Product.query.filter_by(name='Gyudon').first().id, ingredient_id=Ingredient.query.filter_by(name='Tomato').first().id, quantity_needed=0.05), # Placeholder, replace Tomato with Beef/Onion etc.
            # Oyakodon (Example - uses existing chicken, needs egg, onion, rice etc.)
            ProductIngredient(product_id=Product.query.filter_by(name='Oyakodon').first().id, ingredient_id=Ingredient.query.filter_by(name='Chicken Breast').first().id, quantity_needed=0.15), # 150g chicken
            # Wagyu Cubes (Example - needs Wagyu ingredient)
            ProductIngredient(product_id=Product.query.filter_by(name='Wagyu Cubes').first().id, ingredient_id=Ingredient.query.filter_by(name='Chicken Breast').first().id, quantity_needed=0.15), # Placeholder, replace Chicken with Wagyu
            # Cola Can
            ProductIngredient(product_id=Product.query.filter_by(name='Cola Can').first().id, ingredient_id=Ingredient.query.filter_by(name='Cola').first().id, quantity_needed=1.0),
            # Ice Cream Scoop
            ProductIngredient(product_id=Product.query.filter_by(name='Ice Cream Scoop').first().id, ingredient_id=Ingredient.query.filter_by(name='Ice Cream').first().id, quantity_needed=0.1)
        ]
        # Add more ProductIngredient entries for the other new products as needed.
        db.session.add_all(product_ingredients)

        # --- Create Customers ---
        print("Creating customers...")
        customers = [
            Customer(name='John Doe', phone='111-222-3333', email='john.doe@email.com', birthday=date(1990, 5, 15)),
            Customer(name='Jane Smith', phone='444-555-6666', rewards_points=50),
            Customer(name='Walk-in Customer', phone=None) # For orders without specific customer
        ]
        db.session.add_all(customers)
        db.session.flush() # Get customer IDs

        # --- Create Orders ---
        print("Creating orders...")
        orders_to_create = []
        order_items_to_create = []
        inventory_logs_for_orders = []
        tax_rate = 0.12 # Example tax rate

        # Fetch all products again after potentially adding new ones
        all_products = Product.query.all()
        if not all_products:
             print("Warning: No products found to create orders with.")
             return # Exit if no products

        all_available_users = User.query.all() # Fetch all users for order assignment
        if not all_available_users:
            print("Error: No users found to assign orders to.")
            return 

        for i in range(15): # Create 15 sample orders
            order_user = random.choice(all_available_users) # Assign order to any user
            order_customer = random.choice(customers)
            order_type = random.choice(['dine-in', 'take-out', 'delivery'])
            order_status = random.choice(['pending', 'in-progress', 'completed', 'cancelled'])
            created_time = datetime.utcnow() - timedelta(days=random.randint(0, 30), hours=random.randint(0,23))
            completed_time = created_time + timedelta(minutes=random.randint(15, 60)) if order_status == 'completed' else None

            order = Order(
                order_number=str(uuid.uuid4())[:8].upper(), # Unique order number
                order_type=order_type,
                status=order_status,
                user_id=order_user.id,
                customer_id=order_customer.id if order_customer.name != 'Walk-in Customer' else None,
                created_at=created_time,
                completed_at=completed_time,
                payment_method=random.choice(['cash', 'card', 'online']) if order_status == 'completed' else None,
                # Totals will be calculated after adding items
                subtotal=0,
                tax=0,
                total_amount=0
            )
            orders_to_create.append(order)
            db.session.add(order)
            db.session.flush() # Get order ID for items

            # --- Create Order Items for this Order ---
            order_subtotal = 0
            num_items = random.randint(1, 4)
            for _ in range(num_items):
                product = random.choice(all_products) # Use the updated product list
                quantity = random.randint(1, 3)
                item_price = product.price # Price at the time of order
                item_total = item_price * quantity
                order_subtotal += item_total

                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=item_price,
                    notes=random.choice([None, "Less spicy", "Extra rice"]) if product.category_id == main_course_cat.id else None # Example notes
                )
                order_items_to_create.append(order_item)

                # --- Update Inventory (if order is not cancelled) ---
                if order_status != 'cancelled':
                    # Find ingredients for this product
                    ings = ProductIngredient.query.filter_by(product_id=product.id).all()
                    for prod_ing in ings:
                        ingredient_to_update = Ingredient.query.get(prod_ing.ingredient_id)
                        if ingredient_to_update:
                            quantity_used = prod_ing.quantity_needed * quantity
                            # Check if enough quantity exists before reducing
                            if ingredient_to_update.quantity >= quantity_used:
                                ingredient_to_update.quantity -= quantity_used
                            else:
                                print(f"Warning: Not enough {ingredient_to_update.name} ({ingredient_to_update.quantity}{ingredient_to_update.unit}) for order {order.order_number}. Required: {quantity_used}{ingredient_to_update.unit}. Inventory not reduced.")
                                quantity_used = 0 # Don't log reduction if not enough stock

                            # Create inventory log for usage only if quantity was used
                            if quantity_used > 0:
                                log = InventoryLog(
                                    ingredient_id=ingredient_to_update.id,
                                    quantity_change=-quantity_used,
                                    reason='order_usage',
                                    user_id=order_user.id,
                                    order_id=order.id,
                                    timestamp=created_time # Log time should match order time ideally
                                )
                                inventory_logs_for_orders.append(log)
                        else:
                             print(f"Warning: Ingredient ID {prod_ing.ingredient_id} not found for product {product.name} in order {order.order_number}.")


            # Calculate totals for the order
            order.subtotal = round(order_subtotal, 2)
            order.tax = round(order_subtotal * tax_rate, 2)
            order.total_amount = round(order.subtotal + order.tax, 2)

        db.session.add_all(order_items_to_create)
        db.session.add_all(inventory_logs_for_orders)

        # --- Commit all changes ---
        db.session.commit()
        print("Data seeding completed successfully.")

    except Exception as e:
        db.session.rollback()
        print(f"An error occurred during seeding: {e}")
        import traceback
        traceback.print_exc()
