from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Category, Product, Order, OrderItem, Ingredient, ProductIngredient, InventoryLog # Import necessary models
from datetime import datetime
import uuid

pos_bp = Blueprint('pos', __name__, url_prefix='/pos') # Added url_prefix

@pos_bp.route('/new-order', methods=['GET', 'POST'])
@login_required
def new_order():
    if request.method == 'POST':
        order_data = request.get_json()
        
        # Generate unique order number
        order_number = f"ORD-{datetime.now().strftime('%y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Create new order
        new_order = Order(
            order_number=order_number,
            order_type=order_data['orderType'],
            status='pending', # Start as pending
            user_id=current_user.id,
            subtotal=order_data['subtotal'],
            tax=order_data['tax'],
            total_amount=order_data['totalAmount'],
            payment_method=order_data['paymentMethod'],
            customer_id=order_data.get('customerId') # Optional customer ID
        )
        
        db.session.add(new_order)
        db.session.flush()  # Get the order ID before commit

        # Add order items and deduct ingredients
        try:
            for item_data in order_data['items']:
                product = Product.query.get(item_data['productId'])
                if not product:
                    raise ValueError(f"Product ID {item_data['productId']} not found.")

                order_item = OrderItem(
                    order_id=new_order.id,
                    product_id=item_data['productId'],
                    quantity=item_data['quantity'],
                    price=item_data['price'], # Price at time of order
                    notes=item_data.get('notes', '')
                )
                db.session.add(order_item)

                # Deduct ingredients
                for prod_ing in product.ingredients:
                    ingredient = prod_ing.ingredient
                    quantity_to_deduct = prod_ing.quantity_needed * item_data['quantity']
                    
                    if ingredient.quantity < quantity_to_deduct:
                        # Not enough stock - rollback and inform user
                        db.session.rollback()
                        return jsonify({'success': False, 'message': f'Insufficient stock for {ingredient.name} to make {product.name}.'}), 400

                    ingredient.quantity -= quantity_to_deduct
                    
                    # Log inventory change
                    log_entry = InventoryLog(
                        ingredient_id=ingredient.id,
                        quantity_change=-quantity_to_deduct,
                        reason='order_usage',
                        user_id=current_user.id,
                        order_id=new_order.id
                    )
                    db.session.add(log_entry)

            db.session.commit()
            # Optionally update order status to 'in-progress' or 'completed' based on workflow
            # new_order.status = 'in-progress'
            # db.session.commit()
            return jsonify({'success': True, 'order_number': order_number})
        
        except ValueError as ve:
             db.session.rollback()
             return jsonify({'success': False, 'message': str(ve)}), 400
        except Exception as e:
            db.session.rollback()
            # Log the detailed error e
            print(f"Error placing order: {e}") 
            return jsonify({'success': False, 'message': 'An internal error occurred while processing the order.'}), 500

    # GET request - show POS screen
    categories = Category.query.order_by(Category.name).all()
    products = Product.query.filter_by(available=True).order_by(Product.name).all() # Only show available products
    return render_template('new_order.html', categories=categories, products=products)
