from app.models import db
from app import create_app
from flask_cors import CORS
import merge_swagger

# Merge swagger files before creating the app
merge_swagger.merge_swagger_files()

# Create the Flask app
app = create_app('ProductionConfig')

CORS(app, origins="*")

# Create database tables
with app.app_context():
    db.create_all()
    print("Database tables created successfully")

# Add this to actually run the app
if __name__ == '__main__':
    print(f"Starting Flask server on http://127.0.0.1:5000")
    print(f"CORS enabled for all origins")
    app.run(host='127.0.0.1', port=5000, debug=True)