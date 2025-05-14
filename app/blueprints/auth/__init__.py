from flask import Blueprint

auth_bp = Blueprint("auth", __name__, template_folder="templates")

# Import routes after blueprint creation to avoid circular imports
from . import routes
