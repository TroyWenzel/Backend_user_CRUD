from app import create_app
from app.models import db
from flask_cors import CORS  # Add this import

main = create_app('DevelopmentConfig')

# Add CORS to your app
CORS(main, origins="*")  # Or be more specific: origins=['http://localhost:5175']

with main.app_context():
    #print(main.url_map) 
    #db.drop_all()
    db.create_all()

if __name__ == '__main__':
    print("Starting server with CORS enabled...")
    main.run(debug=True, host='127.0.0.1', port=5000)