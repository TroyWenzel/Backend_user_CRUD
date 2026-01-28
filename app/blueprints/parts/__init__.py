from flask import Blueprint

parts_bp = Blueprint('parts_bp', __name__)

from app.blueprints.parts import routes