import random
import uuid
from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash

# Assuming your Flask app instance is created in 'app.py'
# and extensions (like db) are initialized there or in 'extensions.py'
from app import app, db
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
        # --- Create Users ---
        print("Creating users...")
        users = [
            User(username='cashier1', password=generate_password_hash('password', method='pbkdf2:sha256'), name='Alice Smith', role='cashier'),
            User(username='kitchen1', password=generate_password_hash('password', method='pbkdf2:sha256'), name='Bob Johnson', role='kitchen'),
            User(username='manager1', password=generate_password_hash('password', method='pbkdf2:sha256'), name='Charlie Brown', role='manager')
        ]
        db.session.add_all(users)
        db.session.flush() # Flush to get user IDs if needed immediately

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
        for ingredient in ingredients:
            initial_logs.append(InventoryLog(
                ingredient_id=ingredient.id,
                quantity_change=ingredient.quantity,
                reason='initial_stock',
                user_id=users[2].id # Manager added initial stock
            ))
        db.session.add_all(initial_logs)

        # --- Create Products ---
        print("Creating products...")
        products = [
            Product(name='Chicken Sandwich', description='Grilled chicken breast with lettuce and tomato', price=250.00, category_id=categories[1].id, image='chicken_sandwich.jpg'),
            Product(name='Caesar Salad', description='Fresh lettuce with Caesar dressing', price=180.00, category_id=categories[0].id, image='caesar_salad.jpg'),
            Product(name='French Fries', description='Crispy golden fries', price=80.00, category_id=categories[0].id, image='fries.jpg'),
            Product(name='Cola Can', description='330ml Can of Cola', price=50.00, category_id=categories[3].id, image='cola.jpg'),
            Product(name='Ice Cream Scoop', description='Single scoop of vanilla ice cream', price=70.00, category_id=categories[2].id, image='ice_cream.jpg')
        ]
        db.session.add_all(products)
        db.session.flush() # Get product IDs

        # --- Create Product Ingredients ---
        print("Creating product ingredients...")
        product_ingredients = [
            # Chicken Sandwich
            ProductIngredient(product_id=products[0].id, ingredient_id=ingredients[1].id, quantity_needed=0.15), # 150g chicken
            ProductIngredient(product_id=products[0].id, ingredient_id=ingredients[0].id, quantity_needed=0.05), # 50g tomato
            ProductIngredient(product_id=products[0].id, ingredient_id=ingredients[2].id, quantity_needed=0.1),  # 0.1 head lettuce
            ProductIngredient(product_id=products[0].id, ingredient_id=ingredients[3].id, quantity_needed=1.0),  # 1 bun
            # Caesar Salad
            ProductIngredient(product_id=products[1].id, ingredient_id=ingredients[2].id, quantity_needed=0.2),  # 0.2 head lettuce
            # French Fries
            ProductIngredient(product_id=products[2].id, ingredient_id=ingredients[7].id, quantity_needed=0.2), # 200g potatoes
            # Cola Can
            ProductIngredient(product_id=products[3].id, ingredient_id=ingredients[5].id, quantity_needed=1.0),  # 1 can
            # Ice Cream Scoop
            ProductIngredient(product_id=products[4].id, ingredient_id=ingredients[6].id, quantity_needed=0.1)  # 100ml ice cream
        ]
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

        for i in range(5): # Create 5 sample orders
            order_user = random.choice(users)
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
                product = random.choice(products)
                quantity = random.randint(1, 3)
                item_price = product.price # Price at the time of order
                item_total = item_price * quantity
                order_subtotal += item_total

                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=item_price,
                    notes=random.choice([None, "Extra sauce", "No onions"]) if product.name == 'Chicken Sandwich' else None
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
                            ingredient_to_update.quantity -= quantity_used

                            # Create inventory log for usage
                            log = InventoryLog(
                                ingredient_id=ingredient_to_update.id,
                                quantity_change=-quantity_used,
                                reason='order_usage',
                                user_id=order_user.id,
                                order_id=order.id,
                                timestamp=created_time # Log time should match order time ideally
                            )
                            inventory_logs_for_orders.append(log)


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

if __name__ == '__main__':
    with app.app_context():
        # Optional: Clear data before seeding. Be careful with this in production!
        clear_data()
        
        # Check if data already exists (simple check on Users)
        if User.query.first() is None:
             seed_data()
        else:
             print("Database already contains data. Skipping seeding.")
             # You might want to add an argument parser here to force seeding
             # e.g., python seed_data.py --force
             # Or uncomment clear_data() above if you always want to reset.
