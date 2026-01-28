from app.blueprints.service_tickets import service_tickets_bp
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from sqlalchemy import select
from app.blueprints.service_tickets.schemas import service_ticket_schema, service_tickets_schema
from app.models import db, ServiceTickets, Mechanics, Parts
from app.extensions import limiter
from app.util.auth import mechanic_token_required
from app.blueprints.parts.schemas import parts_schema

# CREATE SERVICE TICKET
@service_tickets_bp.route('', methods=['POST'])
@limiter.limit("10 per day")
@mechanic_token_required
def create_service_ticket():
    try:
        service_ticket = service_ticket_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    db.session.add(service_ticket)
    db.session.commit()
    return service_ticket_schema.jsonify(service_ticket), 201


# READ ALL SERVICE TICKETS - PAGINATED
@service_tickets_bp.route('', methods=['GET'])
@limiter.limit("5 per day")
@mechanic_token_required
def read_service_tickets():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
    
        # Query with pagination using select()
        query = select(ServiceTickets)
        paginated_tickets = db.paginate(query, page=page, per_page=per_page, error_out=False)
        return service_tickets_schema.jsonify(paginated_tickets.items), 200
    except:
        # If pagination parameters are missing or invalid, return all tickets
        query = select(ServiceTickets)
        tickets = db.session.execute(query).scalars().all()
        return service_tickets_schema.jsonify(tickets), 200
    

# READ INDIVIDUAL SERVICE TICKET
@service_tickets_bp.route('/<int:ticket_id>', methods=['GET'])
def read_service_ticket(ticket_id):
    ticket = db.session.get(ServiceTickets, ticket_id)
    
    if not ticket:
        return jsonify({'error': 'Service ticket not found'}), 404
    
    return service_ticket_schema.jsonify(ticket), 200


# UPDATE SERVICE TICKET - Requires Token
@service_tickets_bp.route('/<int:ticket_id>', methods=['PUT'])
@limiter.limit("5 per day")
@mechanic_token_required
def update_service_ticket(ticket_id):
    ticket = db.session.get(ServiceTickets, ticket_id)
    
    if not ticket:
        return jsonify({'error': 'Service ticket not found'}), 404
    
    # Verify the mechanic is assigned to this ticket
    mechanic_id = int(request.logged_in_mechanic_id)
    
    # Check if the logged-in mechanic is in the list of mechanics for this ticket
    if not any(mechanic.id == mechanic_id for mechanic in ticket.mechanics):
        return jsonify({'error': 'Unauthorized to update this ticket'}), 403
    
    try:
        data = request.json
        
        # Handle mechanic assignment if mechanic_id is in the request
        if 'mechanic_id' in data:
            # Clear existing mechanics and add new ones
            ticket.mechanics.clear()
            for mid in data['mechanic_id']:
                mechanic = db.session.get(Mechanics, mid)
                if mechanic:
                    ticket.mechanics.append(mechanic)
            del data['mechanic_id']  # Remove from data so it doesn't try to set as attribute
        
        # Update other fields
        for key, value in data.items():
            if hasattr(ticket, key) and key != 'mechanics':  # Skip the relationship
                setattr(ticket, key, value)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    db.session.commit()
    return service_ticket_schema.jsonify(ticket), 200


# DELETE SERVICE TICKET - Requires Token
@service_tickets_bp.route('/<int:ticket_id>', methods=['DELETE'])
@limiter.limit("5 per day")
@mechanic_token_required
def delete_service_ticket(ticket_id):
    ticket = db.session.get(ServiceTickets, ticket_id)
    
    if not ticket:
        return jsonify({'error': 'Service ticket not found'}), 404
    
    # Verify the mechanic is assigned to this ticket
    mechanic_id = int(request.logged_in_mechanic_id)
    
    # Check if the logged-in mechanic is in the list of mechanics for this ticket
    if not any(mechanic.id == mechanic_id for mechanic in ticket.mechanics):
        return jsonify({'error': 'Unauthorized to delete this ticket'}), 403
    
    db.session.delete(ticket)
    db.session.commit()
    return jsonify({'message': f'Service ticket {ticket_id} deleted'}), 200

# ASSIGN MECHANIC TO TICKET
@service_tickets_bp.route('/<int:ticket_id>/mechanics/<int:mechanic_id>', methods=['POST'])
@mechanic_token_required
def assign_mechanic_to_ticket(ticket_id, mechanic_id):
    ticket = db.session.get(ServiceTickets, ticket_id)
    
    if not ticket:
        return jsonify({'error': 'Service ticket not found'}), 404
    
    mechanic = db.session.get(Mechanics, mechanic_id)
    
    if not mechanic:
        return jsonify({'error': 'Mechanic not found'}), 404
    
    # Check if mechanic is already assigned
    if mechanic in ticket.mechanics:
        return jsonify({'error': 'Mechanic already assigned to this ticket'}), 400
    
    # Add mechanic to the ticket
    ticket.mechanics.append(mechanic)
    db.session.commit()
    
    return jsonify({'message': f'Mechanic {mechanic.first_name} {mechanic.last_name} assigned to ticket {ticket_id}'}), 200


# REMOVE MECHANIC FROM TICKET
@service_tickets_bp.route('/<int:ticket_id>/mechanics/<int:mechanic_id>', methods=['DELETE'])
@mechanic_token_required
def remove_mechanic_from_ticket(ticket_id, mechanic_id):
    ticket = db.session.get(ServiceTickets, ticket_id)
    
    if not ticket:
        return jsonify({'error': 'Service ticket not found'}), 404
    
    mechanic = db.session.get(Mechanics, mechanic_id)
    
    if not mechanic:
        return jsonify({'error': 'Mechanic not found'}), 404
    
    # Check if mechanic is assigned
    if mechanic not in ticket.mechanics:
        return jsonify({'error': 'Mechanic not assigned to this ticket'}), 400
    
    # Remove mechanic from the ticket
    ticket.mechanics.remove(mechanic)
    db.session.commit()
    
    return jsonify({'message': f'Mechanic {mechanic.first_name} {mechanic.last_name} removed from ticket {ticket_id}'}), 200

# ADD PART TO SERVICE TICKET
@service_tickets_bp.route('/<int:ticket_id>/parts/<int:part_id>', methods=['POST'])
@mechanic_token_required
def add_part_to_ticket(ticket_id, part_id):
    ticket = db.session.get(ServiceTickets, ticket_id)
    
    if not ticket:
        return jsonify({'error': 'Service ticket not found'}), 404
    
    part = db.session.get(Parts, part_id)
    
    if not part:
        return jsonify({'error': 'Part not found'}), 404
    
    # Check if part is already assigned to a ticket
    if part.ticket_id is not None:
        return jsonify({'error': f'Part already assigned to ticket {part.ticket_id}'}), 400
    
    # Assign the part to the ticket
    part.ticket_id = ticket_id
    db.session.commit()
    
    return jsonify({'message': f'Part {part_id} successfully added to ticket {ticket_id}','part_id': part.id,'ticket_id': ticket.id}), 200


# REMOVE PART FROM SERVICE TICKET
@service_tickets_bp.route('/<int:ticket_id>/parts/<int:part_id>', methods=['DELETE'])
@mechanic_token_required
def remove_part_from_ticket(ticket_id, part_id):
    ticket = db.session.get(ServiceTickets, ticket_id)
    
    if not ticket:
        return jsonify({'error': 'Service ticket not found'}), 404
    
    part = db.session.get(Parts, part_id)
    
    if not part:
        return jsonify({'error': 'Part not found'}), 404
    
    # Check if part is assigned to this ticket
    if part.ticket_id != ticket_id:
        return jsonify({'error': 'Part not assigned to this ticket'}), 400
    
    # Remove the part from the ticket
    part.ticket_id = None
    db.session.commit()
    
    return jsonify({'message': f'Part {part_id} removed from ticket {ticket_id}'}), 200


# GET ALL PARTS FOR A TICKET
@service_tickets_bp.route('/<int:ticket_id>/parts', methods=['GET'])
def get_ticket_parts(ticket_id):
    ticket = db.session.get(ServiceTickets, ticket_id)
    
    if not ticket:
        return jsonify({'error': 'Service ticket not found'}), 404
    
    query = select(Parts).where(Parts.ticket_id == ticket_id)
    parts = db.session.execute(query).scalars().all()
    
    return parts_schema.jsonify(parts), 200