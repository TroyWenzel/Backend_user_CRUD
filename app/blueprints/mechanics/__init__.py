from flask import Blueprint

# Create the blueprint
mechanics_bp = Blueprint('mechanics_bp', __name__)

# Import routes AFTER creating the blueprint to avoid circular import
# This must be at the bottom of the file
from app.blueprints.mechanics import routes