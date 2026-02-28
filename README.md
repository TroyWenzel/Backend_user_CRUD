Mechanic Shop Management System - Full Stack Application
📋 Overview
A comprehensive full-stack application for managing a mechanic workshop, combining a React + Vite frontend with a Flask REST API backend. This system allows workshop managers to efficiently manage customers, mechanics, service tickets, and assignments.

🏗️ Architecture
The application consists of two main components:

Frontend (React + Vite)
Modern React application with Material-UI (MUI) components

Built with Vite for fast development and optimized production builds

Emotion for styled components

React Router for navigation

Backend (Flask)
RESTful API built with Flask

SQLAlchemy ORM for database management

Marshmallow for serialization/deserialization

SQLite for development, PostgreSQL for production

Swagger/OpenAPI documentation

🚀 Features
Customer Management
Create, read, update, and delete customer records

Store customer contact information (name, email, phone, address)

View customer service history

Mechanic Management
Manage mechanic profiles with contact details and salary information

Track mechanic assignments to service tickets

Update mechanic information

Service Tickets
Create service tickets linked to customers

Track vehicle VIN, service description, date, and price

Assign multiple mechanics to a single ticket

View all tickets with associated customer and mechanic details

Many-to-Many Relationships
Service tickets can have multiple mechanics

Mechanics can work on multiple tickets

Junction table ticket_mechanic manages the relationships

🛠️ Technology Stack
Frontend
Technology	Purpose
React 19	UI library
Vite 7	Build tool and dev server
Material-UI (MUI) 7	Component library
Emotion 11	Styling
React Router 7	Navigation
ESLint 9	Code linting
Backend
Technology	Purpose
Flask 3.1	Web framework
SQLAlchemy 2.0	ORM for database
Marshmallow 4.1	Object serialization
Flask-CORS	Cross-origin resource sharing
Gunicorn	Production WSGI server
PyYAML	Swagger file processing
📁 Project Structure
text
/
├── frontend/                 # React + Vite frontend
│   ├── src/                  # Source files
│   ├── index.html            # Entry HTML
│   ├── vite.config.js        # Vite configuration
│   └── eslint.config.js      # ESLint configuration
│
├── backend/                  # Flask backend
│   ├── app/                  # Application package
│   │   ├── models.py         # Database models
│   │   ├── routes/           # API route handlers
│   │   └── static/           # Swagger documentation files
│   ├── flask_app.py          # Production entry point
│   ├── main.py                # Development entry point
│   ├── config.py             # Configuration classes
│   ├── requirements.txt      # Python dependencies
│   └── merge_swagger.py      # Swagger documentation merger
💾 Database Schema
Customers
id (INT, PK)

first_name (VARCHAR)

last_name (VARCHAR)

email (VARCHAR, unique)

phone (VARCHAR)

address (VARCHAR)

Mechanics
id (INT, PK)

first_name (VARCHAR)

last_name (VARCHAR)

email (VARCHAR, unique)

address (VARCHAR)

salary (FLOAT)

Service Tickets
id (INT, PK)

customer_id (INT, FK)

service_desc (VARCHAR)

VIN (VARCHAR)

service_date (DATE)

price (FLOAT)

Ticket_Mechanic (Junction Table)
ticket_id (INT, FK)

mechanic_id (INT, FK)

🔌 API Endpoints
Customers
Method	Endpoint	Description
GET	/customers	Get all customers
GET	/customers/{id}	Get specific customer
POST	/customers	Create new customer
PUT	/customers/{id}	Update customer
DELETE	/customers/{id}	Delete customer
Mechanics
Method	Endpoint	Description
GET	/mechanics	Get all mechanics
GET	/mechanics/{id}	Get specific mechanic
POST	/mechanics	Create new mechanic
PUT	/mechanics/{id}	Update mechanic
DELETE	/mechanics/{id}	Delete mechanic
Service Tickets
Method	Endpoint	Description
GET	/tickets	Get all tickets
GET	/tickets/{id}	Get specific ticket
POST	/tickets	Create new ticket
PUT	/tickets/{id}/assign-mechanic/{mechanic_id}	Assign mechanic to ticket
PUT	/tickets/{id}/remove-mechanic/{mechanic_id}	Remove mechanic from ticket
🚦 Getting Started
Prerequisites
Node.js (v18+)

Python (v3.9+)

npm or yarn

pip (Python package manager)

Installation
1. Clone the repository
bash
git clone <repository-url>
cd mechanic-shop-management
2. Backend Setup
bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python main.py
The backend will start at http://127.0.0.1:5000

3. Frontend Setup
bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
The frontend will start at http://localhost:5173 (or next available port)

Environment Configuration
Backend Configuration
The application uses different configuration classes:

DevelopmentConfig: SQLite database, debug mode enabled

TestingConfig: In-memory SQLite for tests

ProductionConfig: PostgreSQL (via DATABASE_URL), debug disabled

Set environment variables as needed:

bash
export SECRET_KEY="your-secret-key"
export DATABASE_URL="postgresql://user:pass@host/db"  # Production only
📚 API Documentation
Swagger/OpenAPI documentation is automatically generated by merging multiple YAML files. Access the interactive documentation at:

Development: http://127.0.0.1:5000/api/docs

Production: https://your-domain.com/api/docs

🧪 Testing
Backend Tests
bash
cd backend
pytest
Frontend Linting
bash
cd frontend
npm run lint
📦 Building for Production
Frontend Build
bash
cd frontend
npm run build
The built files will be in the dist directory.

Backend Production Server
bash
cd backend
gunicorn flask_app:app
🌐 Deployment
Backend (Render/Heroku)
Set environment variables in your hosting platform

Ensure DATABASE_URL is configured for PostgreSQL

The application will automatically use ProductionConfig

Frontend (Netlify/Vercel)
Build the frontend: npm run build

Deploy the dist folder to your hosting service

Configure environment variables for API URL if needed

🔒 CORS Configuration
CORS is enabled for all origins in development. For production, restrict to your frontend domain:

python
CORS(app, origins=["https://your-frontend-domain.com"])
📝 License
This project is for educational purposes as part of a homework assignment.

🤝 Contributing
This is a homework project, but feel free to fork and experiment!
