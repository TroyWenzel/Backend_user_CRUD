from flask import Flask
from flask_cors import CORS 
from app.models import db
from app.extensions import ma, limiter, cache
from flask_swagger_ui import get_swaggerui_blueprint

CONFIG_MAP = {
    'development': 'DevelopmentConfig',
    'testing': 'TestingConfig',
    'production': 'ProductionConfig'
}

def create_app(config_name):
    app = Flask(__name__)
    
    config_class_name = CONFIG_MAP.get(config_name, config_name)
    app.config.from_object(f'config.{config_class_name}')
    
    # Initialize extensions
    db.init_app(app)
    ma.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)

    # CORS Configuration
    CORS(app, resources={
        r"/*": {
            "origins": [
                "http://localhost:5173",      # Vite dev server
                "http://127.0.0.1:5173",      # Alternative localhost
                "http://localhost:5174",      # Backup Vite port
                "http://localhost:3000",      # React default port (if used)
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })

    from app.blueprints.customers import customers_bp
    from app.blueprints.mechanics import mechanics_bp
    from app.blueprints.service_tickets import service_tickets_bp
    from app.blueprints.parts import parts_bp
    
    # Create swagger blueprint
    swagger_blueprint = get_swaggerui_blueprint(
        "/api/docs", 
        "/static/mechanic_shop_swagger.yaml", 
        config={"app_name": "Mechanic Shop API"}
    )

    # Register blueprints
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(mechanics_bp, url_prefix='/mechanics')
    app.register_blueprint(service_tickets_bp, url_prefix='/tickets')
    app.register_blueprint(parts_bp, url_prefix='/parts')
    app.register_blueprint(swagger_blueprint, url_prefix='/api/docs')

    return app