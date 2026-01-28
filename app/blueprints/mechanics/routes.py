from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select, func
from . import mechanics_bp  # CHANGED: Use relative import instead of absolute
from app.blueprints.mechanics.schemas import mechanic_schema, mechanics_schema, login_schema
from app.models import db, Mechanics, ServiceTickets, ticket_mechanic
from app.extensions import limiter
from app.blueprints.service_tickets.schemas import service_tickets_schema
from werkzeug.security import generate_password_hash, check_password_hash
from app.util.auth import encode_token, mechanic_token_required

# LOGIN ROUTE - FIXED TO RETURN USER DATA
@mechanics_bp.route('/login', methods=['POST'])
@limiter.limit("5 per 10 minute")
def login():
    try:
        data = request.json
        login_schema.load(data)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    # Find mechanic by email using select()
    query = select(Mechanics).where(Mechanics.email == data['email'])
    mechanic = db.session.execute(query).scalar_one_or_none()
    
    # Verify mechanic exists and password is correct
    if mechanic and check_password_hash(mechanic.password, str(data['password'])):
        token = encode_token(mechanic.id, role="mechanic")
        
        # Return both token AND user data (excluding password)
        return jsonify({
            "message": f"Welcome back, {mechanic.first_name}!",
            "token": token,
            "user": mechanic_schema.dump(mechanic)  # This excludes password due to load_only
        }), 200
    
    return jsonify({"error": "Invalid credentials"}), 401


# CREATE MECHANIC ROUTE
@mechanics_bp.route('', methods=['POST'])
#@limiter.limit("2 per day")
def create_mechanic():
    try:
        data = request.json
        new_mechanic = mechanic_schema.load(data)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    # Hash the password before saving
    if 'password' in data:
        new_mechanic.password = generate_password_hash(str(data['password']))
    
    try:
        db.session.add(new_mechanic)
        db.session.commit()
        db.session.refresh(new_mechanic)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to create mechanic. Email may already exist."}), 400
    
    return jsonify(mechanic_schema.dump(new_mechanic)), 201


# READ ALL MECHANICS
@mechanics_bp.route('', methods=['GET'])
def read_mechanics():
    query = select(Mechanics)
    mechanics = db.session.execute(query).scalars().all()
    return mechanics_schema.jsonify(mechanics), 200


# GET MY TICKETS - Requires Token
@mechanics_bp.route('/my-tickets', methods=['GET'])
@mechanic_token_required
def get_my_tickets():
    mechanic_id = request.logged_in_mechanic_id
    # Get the mechanic and their tickets through the relationship
    mechanic = db.session.get(Mechanics, mechanic_id)   
    if not mechanic:
        return jsonify({'error': 'Mechanic not found'}), 404 
    # Return tickets
    return service_tickets_schema.jsonify(mechanic.service_tickets), 200


# GET MY PROFILE - Requires Token
@mechanics_bp.route('/profile', methods=['GET'])
@mechanic_token_required
def get_profile():
    mechanic_id = request.logged_in_mechanic_id
    mechanic = db.session.get(Mechanics, mechanic_id)
    
    if not mechanic:
        return jsonify({'error': 'Mechanic not found'}), 404
    
    return mechanic_schema.jsonify(mechanic), 200


# UPDATE MECHANIC - Requires Token
@mechanics_bp.route('', methods=['PUT'])
@limiter.limit("5 per day")
@mechanic_token_required
def update_mechanic():
    mechanic_id = request.logged_in_mechanic_id
    mechanic = db.session.get(Mechanics, mechanic_id)
    
    if not mechanic:
        return jsonify({'error': 'Mechanic not found'}), 404

    try:
        data = request.json
        if 'password' in data:
            data['password'] = generate_password_hash(str(data['password']))
        
        for key, value in data.items():
            if hasattr(mechanic, key):
                setattr(mechanic, key, value)
    except ValidationError as e:
        return jsonify(e.messages), 400

    db.session.commit()
    return mechanic_schema.jsonify(mechanic), 200


# DELETE MECHANIC - Requires Token
@mechanics_bp.route('', methods=['DELETE'])
@mechanic_token_required
def delete_mechanic():
    mechanic_id = request.logged_in_mechanic_id
    mechanic = db.session.get(Mechanics, mechanic_id)
    
    if not mechanic:
        return jsonify({'error': 'Mechanic not found'}), 404

    db.session.delete(mechanic)
    db.session.commit()
    return jsonify({'message': 'Mechanic deleted'}), 200


# GET MECHANIC WITH MOST TICKETS
@mechanics_bp.route('/top-mechanics', methods=['GET'])
def get_top_mechanics():
    # Query to count tickets per mechanic
    results = db.session.query(
        Mechanics.id,
        Mechanics.first_name,
        Mechanics.last_name,
        Mechanics.email,
        func.count(ticket_mechanic.c.ticket_id).label('ticket_count')
    ).join(
        ticket_mechanic, Mechanics.id == ticket_mechanic.c.mechanic_id
    ).group_by(
        Mechanics.id
    ).order_by(
        func.count(ticket_mechanic.c.ticket_id).desc()
    ).limit(5).all()
    
    if not results:
        return jsonify({'error': 'No mechanics found with tickets'}), 404
    
    top_mechanics = [
        {
            'id': result.id,
            'first_name': result.first_name,
            'last_name': result.last_name,
            'email': result.email,
            'ticket_count': result.ticket_count
        }
        for result in results
    ]
    
    return jsonify(top_mechanics), 200