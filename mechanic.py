from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Date, Column, ForeignKey, Table, Integer, Float
from datetime import date
from flask_marshmallow import Marshmallow #Importing Marshmallow class
from marshmallow import ValidationError

app = Flask(__name__) #Instantiating our Flask app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db' #Connecting a sqlite db to our flask app

# Create a base class for our models
class Base(DeclarativeBase):
    pass
    # you could add your own configuration

# Instantiate your SQLAlchemy database
db = SQLAlchemy(model_class = Base)
ma = Marshmallow()

# Initialize my extension onto my Flask app
db.init_app(app) #adding the db to the app
ma.init_app(app)

ticket_mechanic = Table(
    'ticket_mechanic',
    Base.metadata,
    Column('ticket_id', Integer, ForeignKey('service_tickets.id'), primary_key=True),
    Column('mechanic_id', Integer, ForeignKey('mechanics.id'), primary_key=True)
)
# Customers table
class Customers(Base):
    __tablename__ = 'customers'
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(250), nullable=False)
    last_name: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(350), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=True)

# Relationship: one customer can have many service tickets
    service_tickets: Mapped[list["ServiceTickets"]] = relationship(back_populates="customer")

# Service Tickets table
class ServiceTickets(Base):
    __tablename__ = 'service_tickets'
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id'), nullable=False)
    service_desc: Mapped[str] = mapped_column(String(1000), nullable=False)
    VIN: Mapped[str] = mapped_column(String(17), nullable=False)
    service_date: Mapped[date] = mapped_column(Date, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Relationships
    customer: Mapped["Customers"] = relationship(back_populates="service_tickets")
    mechanics: Mapped[list["Mechanics"]] = relationship(secondary=ticket_mechanic, back_populates="service_tickets")

# Mechanics table
class Mechanics(Base):
    __tablename__ = 'mechanics'
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(250), nullable=False)
    last_name: Mapped[str] = mapped_column(String(250), nullable=False)
    email: Mapped[str] = mapped_column(String(350), nullable=False, unique=True)
    address: Mapped[str] = mapped_column(String(500), nullable=True)
    salary: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Relationship: one mechanic can work on many service tickets
    service_tickets: Mapped[list["ServiceTickets"]] = relationship(secondary=ticket_mechanic, back_populates="mechanics")

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customers 

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

# CREATE CUSTOMER ROUTE
@app.route('/customers', methods=['POST'])
def create_customer():
    try:
        data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400 
    
    new_customer = Customers(**data)
    db.session.add(new_customer)
    db.session.commit()
    return customer_schema.jsonify(new_customer), 201 

# READ CUSTOMERS ROUTE
@app.route("/customers", methods=["GET"]) 
def read_customers():
    customers = db.session.query(Customers).all()
    return customers_schema.jsonify(customers), 200 

# Read Individual Customer
@app.route('/customers/<int:customer_id>', methods=['GET'])
def read_customer(customer_id):
    customer = db.session.get(Customers, customer_id)
    return customer_schema.jsonify(customer), 200

# Delete a Customer
@app.route("/customers/<int:customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    customer = db.session.get(Customers, customer_id)
    if not customer:
        return jsonify({"error":"User not found"}), 404
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": f"Successfully deleted user {customer_id}"}), 200


with app.app_context():
    db.create_all()
    # creates all tables defined by our models in the context of the app's configuration and db

app.run(debug=True)
# Finally, we run our Flask app


# Install Marshmallow
# pip install flask-marshmallow marshmallow-sqlalchemy