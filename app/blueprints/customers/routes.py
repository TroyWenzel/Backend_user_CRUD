from app.blueprints.customers import customers_bp
from app.blueprints.customers.schemas import customer_schema, customers_schema, customer_login_schema
from flask import jsonify, request
from marshmallow import ValidationError
from app.models import db, Customers, ServiceTickets
from app.extensions import limiter, cache
from werkzeug.security import generate_password_hash, check_password_hash
from app.util.auth import encode_token, customer_token_required

# CUSTOMER LOGIN ROUTE
@customers_bp.route('/login', methods=['POST'])
@limiter.limit("5 per 10 minute")
def login():
    from sqlalchemy import select
    
    try:
        data = request.json
        customer_login_schema.load(data)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    # Find customer by email using select()
    query = select(Customers).where(Customers.email == data['email'])
    customer = db.session.execute(query).scalar_one_or_none()
    
    # Verify customer exists and password is correct
    if customer and check_password_hash(customer.password, str(data['password'])):
        token = encode_token(customer.id, role="customer")
        return jsonify({
            "message": f"Welcome back, {customer.first_name}!",
            "token": token
        }), 200
    
    return jsonify({"error": "Invalid credentials"}), 401


# CREATE CUSTOMER ROUTE
@customers_bp.route('', methods=['POST'])
@limiter.limit("30 per day")
def create_customer():
    try:
        data = request.json
        new_customer = customer_schema.load(data)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    # Hash the password before saving
    if 'password' in data:
        new_customer.password = generate_password_hash(str(data['password']))
    
    try:
        db.session.add(new_customer)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create customer. Email may already exist."}), 400
    
    return customer_schema.jsonify(new_customer), 201


# GET MY TICKETS - Customer Token Required
@customers_bp.route('/my-tickets', methods=['GET'])
@customer_token_required
def get_my_tickets():
    from sqlalchemy import select
    
    customer_id = request.logged_in_customer_id
    
    # Get all service tickets for this customer using select()
    query = select(ServiceTickets).where(ServiceTickets.customer_id == customer_id)
    tickets = db.session.execute(query).scalars().all()
    
    if not tickets:
        return jsonify({"message": "No service tickets found"}), 200
    
    # Import schema for service tickets
    from app.blueprints.service_tickets.schemas import service_tickets_schema
    return service_tickets_schema.jsonify(tickets), 200


# GET MY PROFILE - Customer Token Required
@customers_bp.route('/profile', methods=['GET'])
@customer_token_required
def get_profile():
    customer_id = request.logged_in_customer_id
    customer = db.session.get(Customers, customer_id)
    
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    
    return customer_schema.jsonify(customer), 200


# READ CUSTOMERS ROUTE - PAGINATED WITH CACHING
@customers_bp.route("", methods=["GET"])
@cache.cached(timeout=60, query_string=True)
def read_customers():
    from sqlalchemy import select
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Query all customers with pagination using select()
    query = select(Customers)
    
    # Use paginate but handle out of range pages gracefully
    try:
        paginated_customers = db.paginate(query, page=page, per_page=per_page, error_out=False)
        # Return the items from the pagination object
        return customers_schema.jsonify(paginated_customers.items), 200
    except Exception as e:
        # If pagination fails, return empty list
        return jsonify([]), 200


# Read Individual Customer
@customers_bp.route('/<int:customer_id>', methods=['GET'])
def read_customer(customer_id):
    customer = db.session.get(Customers, customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    return customer_schema.jsonify(customer), 200


# Delete a Customer
@customers_bp.route("/<int:customer_id>", methods=["DELETE"])
@limiter.limit("5 per day")
def delete_customer(customer_id):
    customer = db.session.get(Customers, customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": f"Successfully deleted customer {customer_id}"}), 200


# UPDATE A CUSTOMER - Token Required (own profile only)
@customers_bp.route("", methods=["PUT"])
@customer_token_required
def update_customer():
    customer_id = request.logged_in_customer_id
    customer = db.session.get(Customers, customer_id)
    
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    try:
        data = request.json
        
        # Hash password if it's being updated
        if 'password' in data:
            data['password'] = generate_password_hash(str(data['password']))
        
        # Update allowed fields
        for key, value in data.items():
            if hasattr(customer, key):
                setattr(customer, key, value)
                
    except ValidationError as e:
        return jsonify({"message": e.messages}), 400
    
    db.session.commit()
    return customer_schema.jsonify(customer), 200


# SEARCH CUSTOMER BY EMAIL (case-insensitive)
@customers_bp.route('/search', methods=['GET'])
def search_customer_by_email():
    from sqlalchemy import select
    
    email = request.args.get('email')
    
    if not email:
        return jsonify({'error': 'Email parameter is required'}), 400
    
    # Case-insensitive search using select()
    query = select(Customers).where(Customers.email.ilike(email))
    customer = db.session.execute(query).scalar_one_or_none()
    
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404
    
    return customer_schema.jsonify(customer), 200