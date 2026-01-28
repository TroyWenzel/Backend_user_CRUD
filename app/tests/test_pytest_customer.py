import pytest
from flask import json
from datetime import date
from werkzeug.security import generate_password_hash
from app.models import db, Customers, ServiceTickets
from app.util.auth import encode_token


@pytest.fixture
def sample_customer(app):
    # Create a sample customer for testing
    with app.app_context():
        customer = Customers(
            first_name="John",
            last_name="Doe",
            email="john.doe@email.com",
            password=generate_password_hash("password123"),
            phone="555-1234"
        )
        db.session.add(customer)
        db.session.commit()
        
        # Refresh to get the ID
        db.session.refresh(customer)
        customer_id = customer.id
        
        yield customer
        
        # Cleanup
        customer = db.session.get(Customers, customer_id)
        if customer:
            db.session.delete(customer)
            db.session.commit()


@pytest.fixture
def customer_token(sample_customer):
    # Generate a valid customer token
    return encode_token(sample_customer.id, role="customer")


@pytest.fixture
def sample_service_ticket(app, sample_customer):
    # Create a sample service ticket for testing
    with app.app_context():
        ticket = ServiceTickets(
            customer_id=sample_customer.id,
            service_desc="Test ticket - oil change",
            VIN="1HGBH41JXMN109186",
            service_date=date.today(),
            price=100.00
        )
        db.session.add(ticket)
        db.session.commit()
        
        # Refresh to get the ID
        db.session.refresh(ticket)
        ticket_id = ticket.id
        
        yield ticket
        
        # Cleanup
        ticket = db.session.get(ServiceTickets, ticket_id)
        if ticket:
            db.session.delete(ticket)
            db.session.commit()


class TestCustomerLogin:
    # Tests for POST /customers/login
    
    def test_login_success(self, client, sample_customer):
        # Test successful login with valid credentials
        response = client.post('/customers/login', json={
            'email': 'john.doe@email.com',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'token' in data
        assert 'Welcome back, John!' in data['message']
    
    def test_login_invalid_password(self, client, sample_customer):
        # Test login with incorrect password
        response = client.post('/customers/login', json={
            'email': 'john.doe@email.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'Invalid credentials'
    
    def test_login_nonexistent_user(self, client):
        # Test login with non-existent email
        response = client.post('/customers/login', json={
            'email': 'nonexistent@email.com',
            'password': 'password123'
        })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'Invalid credentials'
    
    def test_login_missing_fields(self, client):
        # Test login with missing required fields
        response = client.post('/customers/login', json={
            'email': 'john.doe@email.com'
        })
        
        assert response.status_code == 400
    
    def test_login_invalid_data(self, client):
        # Test login with invalid data format
        response = client.post('/customers/login', json={
            'email': 'invalid-email',
            'password': 'password123'
        })
        
        assert response.status_code == 400


class TestCreateCustomer:
    # Tests for POST /customers
    
    def test_create_customer_success(self, client, app):
        # Test successful customer creation
        response = client.post('/customers', json={
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@email.com',
            'password': 'securepass123',
            'phone': '555-5678'
        })
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['email'] == 'jane.smith@email.com'
        assert data['first_name'] == 'Jane'
        
        # Cleanup
        with app.app_context():
            customer = db.session.query(Customers).filter_by(
                email='jane.smith@email.com'
            ).first()
            if customer:
                db.session.delete(customer)
                db.session.commit()
    
    def test_create_customer_missing_fields(self, client):
        # Test customer creation with missing required fields
        response = client.post('/customers', json={
            'first_name': 'Jane',
            'email': 'jane@email.com'
        })
        
        assert response.status_code == 400
    
    def test_create_customer_invalid_email(self, client):
        # Test customer creation with invalid email format
        response = client.post('/customers', json={
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'invalid-email',
            'password': 'password123',
            'phone': '555-0000'
        })
        
        assert response.status_code == 400
    
    def test_create_customer_duplicate_email(self, client, sample_customer):
        # Test customer creation with duplicate email
        response = client.post('/customers', json={
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'john.doe@email.com',
            'password': 'password123',
            'phone': '555-0000'
        })
        
        # Should fail due to unique constraint
        assert response.status_code in [400, 409, 500]


class TestGetMyTickets:
    # Tests for GET /customers/my-tickets
    
    def test_get_my_tickets_success(self, client, customer_token, sample_service_ticket):
        # Test retrieving customer's tickets with valid token
        response = client.get('/customers/my-tickets', headers={
            'Authorization': f'Bearer {customer_token}'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_get_my_tickets_no_tickets(self, client, customer_token):
        # Test retrieving tickets when customer has none
        response = client.get('/customers/my-tickets', headers={
            'Authorization': f'Bearer {customer_token}'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data or isinstance(data, list)
    
    def test_get_my_tickets_no_token(self, client):
        # Test accessing tickets without authentication token
        response = client.get('/customers/my-tickets')
        
        assert response.status_code == 401
    
    def test_get_my_tickets_invalid_token(self, client):
        # Test accessing tickets with invalid token
        response = client.get('/customers/my-tickets', headers={'Authorization': 'Bearer invalid_token_here'})
        
        assert response.status_code == 401


class TestGetProfile:
    # Tests for GET /customers/profile
    
    def test_get_profile_success(self, client, customer_token, sample_customer):
        # Test retrieving customer profile with valid token
        response = client.get('/customers/profile', headers={'Authorization': f'Bearer {customer_token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['email'] == sample_customer.email
        assert data['first_name'] == sample_customer.first_name
    
    def test_get_profile_no_token(self, client):
        # Test accessing profile without authentication token
        response = client.get('/customers/profile')
        
        assert response.status_code == 401
    
    def test_get_profile_invalid_token(self, client):
        # Test accessing profile with invalid token
        response = client.get('/customers/profile', headers={'Authorization': 'Bearer invalid_token'})
        
        assert response.status_code == 401


class TestReadCustomers:
    # Tests for GET /customers (paginated list)
    
    def test_read_customers_default_pagination(self, client, sample_customer):
        # Test retrieving customers with default pagination
        response = client.get('/customers')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_read_customers_custom_pagination(self, client, sample_customer):
        # Test retrieving customers with custom pagination parameters
        response = client.get('/customers?page=1&per_page=5')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) <= 5
    
    def test_read_customers_page_out_of_range(self, client):
        # Test retrieving customers with page number out of range
        response = client.get('/customers?page=9999&per_page=10')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)


class TestReadCustomer:
    # Tests for GET /customers/<customer_id>
    
    def test_read_customer_success(self, client, sample_customer):
        # Test retrieving a specific customer by ID
        response = client.get(f'/customers/{sample_customer.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == sample_customer.id
        assert data['email'] == sample_customer.email
    
    def test_read_customer_not_found(self, client):
        # Test retrieving a non-existent customer
        response = client.get('/customers/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_read_customer_invalid_id(self, client):
        # Test retrieving customer with invalid ID format
        response = client.get('/customers/invalid')
        
        assert response.status_code == 404


class TestDeleteCustomer:
    # Tests for DELETE /customers/<customer_id>
    
    def test_delete_customer_success(self, client, app):
        # Test successfully deleting a customer
        # Create a customer to delete
        with app.app_context():
            customer = Customers(
                first_name="Delete",
                last_name="Me",
                email="delete.me@email.com",
                password=generate_password_hash("password123"),
                phone="555-0000"
            )
            db.session.add(customer)
            db.session.commit()
            db.session.refresh(customer)
            customer_id = customer.id
        
        response = client.delete(f'/customers/{customer_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'Successfully deleted' in data['message']
    
    def test_delete_customer_not_found(self, client):
        # Test deleting a non-existent customer
        response = client.delete('/customers/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_delete_customer_invalid_id(self, client):
        # Test deleting customer with invalid ID format
        response = client.delete('/customers/invalid')
        
        assert response.status_code == 404


class TestUpdateCustomer:
    # Tests for PUT /customers
    
    def test_update_customer_success(self, client, customer_token, sample_customer):
        # Test successfully updating customer profile
        response = client.put('/customers', 
            headers={'Authorization': f'Bearer {customer_token}'},
            json={
                'first_name': 'UpdatedJohn',
                'phone': '555-9999'
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['first_name'] == 'UpdatedJohn'
        assert data['phone'] == '555-9999'
    
    def test_update_customer_password(self, client, customer_token, sample_customer, app):
        # Test updating customer password
        response = client.put('/customers',
            headers={'Authorization': f'Bearer {customer_token}'},
            json={'password': 'newpassword123'}
        )
        
        assert response.status_code == 200
        
        # Verify password was hashed
        with app.app_context():
            updated_customer = db.session.get(Customers, sample_customer.id)
            assert updated_customer.password != 'newpassword123'
    
    def test_update_customer_no_token(self, client):
        # Test updating customer without authentication token
        response = client.put('/customers', json={'first_name': 'UpdatedName'})
        
        assert response.status_code == 401
    
    def test_update_customer_invalid_token(self, client):
        # Test updating customer with invalid token
        response = client.put('/customers',
            headers={'Authorization': 'Bearer invalid_token'},
            json={'first_name': 'UpdatedName'}
        )
        
        assert response.status_code == 401
    
    def test_update_customer_invalid_field(self, client, customer_token):
        # Test updating with non-existent field
        response = client.put('/customers',
            headers={'Authorization': f'Bearer {customer_token}'},
            json={'nonexistent_field': 'value'}
        )
        
        # Should succeed but ignore invalid field
        assert response.status_code == 200


class TestSearchCustomerByEmail:
    # Tests for GET /customers/search
    
    def test_search_customer_success(self, client, sample_customer):
        # Test searching for customer by email
        response = client.get(f'/customers/search?email={sample_customer.email}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['email'].lower() == sample_customer.email.lower()
    
    def test_search_customer_case_insensitive(self, client, sample_customer):
        # Test case-insensitive email search
        response = client.get(f'/customers/search?email={sample_customer.email.upper()}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['email'].lower() == sample_customer.email.lower()
    
    def test_search_customer_not_found(self, client):
        # Test searching for non-existent customer email
        response = client.get('/customers/search?email=nonexistent@email.com')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_search_customer_missing_parameter(self, client):
        # Test search without email parameter
        response = client.get('/customers/search')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'required' in data['error'].lower()
    
    def test_search_customer_empty_parameter(self, client):
        # Test search with empty email parameter
        response = client.get('/customers/search?email=')
        
        assert response.status_code == 400
        
# Make sure to use "pytest app/tests/test_pytest_customer.py -v" when running this