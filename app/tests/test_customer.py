import unittest
import json
from datetime import date
from werkzeug.security import generate_password_hash
from app import create_app
from app.models import db, Customers, ServiceTickets
from app.util.auth import encode_token


class BaseTestCase(unittest.TestCase):
    # Base test case with setup and teardown
    
    def setUp(self):
        # Set up test client and database
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create a sample customer for tests
        self.sample_customer = Customers(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            password=generate_password_hash("password123"),
            phone="555-1234"
        )
        db.session.add(self.sample_customer)
        db.session.commit()
        
        # Generate token for the sample customer
        self.customer_token = encode_token(self.sample_customer.id, role="customer")
    
    def tearDown(self):
        # Clean up after tests
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


class TestCustomerLogin(BaseTestCase):
    # Tests for POST /customers/login
    
    def test_login_success(self):
        # Test successful login with valid credentials
        response = self.client.post('/customers/login', 
            data=json.dumps({
                'email': 'john.doe@example.com',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('token', data)
        self.assertIn('Welcome back, John!', data['message'])
    
    def test_login_invalid_password(self):
        # Test login with incorrect password
        response = self.client.post('/customers/login',
            data=json.dumps({
                'email': 'john.doe@example.com',
                'password': 'wrongpassword'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Invalid credentials')
    
    def test_login_nonexistent_user(self):
        # Test login with non-existent email
        response = self.client.post('/customers/login',
            data=json.dumps({
                'email': 'nonexistent@example.com',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Invalid credentials')
    
    def test_login_missing_fields(self):
        # Test login with missing required fields
        response = self.client.post('/customers/login',
            data=json.dumps({'email': 'john.doe@example.com'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_login_invalid_data(self):
        # Test login with invalid data format
        response = self.client.post('/customers/login',
            data=json.dumps({
                'email': 'invalid-email',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)


class TestCreateCustomer(BaseTestCase):
    # Tests for POST /customers
    
    def test_create_customer_success(self):
        # Test successful customer creation
        response = self.client.post('/customers',
            data=json.dumps({
                'first_name': 'Jane',
                'last_name': 'Smith',
                'email': 'jane.smith@example.com',
                'password': 'securepass123',
                'phone': '555-5678'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['email'], 'jane.smith@example.com')
        self.assertEqual(data['first_name'], 'Jane')
    
    def test_create_customer_missing_fields(self):
        # Test customer creation with missing required fields
        response = self.client.post('/customers',
            data=json.dumps({
                'first_name': 'Jane',
                'email': 'jane@example.com'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_create_customer_invalid_email(self):
        # Test customer creation with invalid email format
        response = self.client.post('/customers',
            data=json.dumps({
                'first_name': 'Jane',
                'last_name': 'Smith',
                'email': 'invalid-email',
                'password': 'password123',
                'phone': '555-0000'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_create_customer_duplicate_email(self):
        # Test customer creation with duplicate email
        response = self.client.post('/customers',
            data=json.dumps({
                'first_name': 'Jane',
                'last_name': 'Smith',
                'email': 'john.doe@example.com',
                'password': 'password123',
                'phone': '555-0000'
            }),
            content_type='application/json'
        )
        
        # Should fail due to unique constraint
        self.assertIn(response.status_code, [400, 409, 500])


class TestGetMyTickets(BaseTestCase):
    # Tests for GET /customers/my-tickets
    
    def setUp(self):
        # Set up test data including service ticket
        super().setUp()
        
        # Create a service ticket for the sample customer with ALL required fields
        self.sample_ticket = ServiceTickets(
            customer_id=self.sample_customer.id,
            service_desc="Test ticket - oil change and tire rotation",
            VIN="1HGBH41JXMN109186",  # Valid VIN format (17 characters)
            service_date=date.today(),
            price=150.00
        )
        db.session.add(self.sample_ticket)
        db.session.commit()
    
    def test_get_my_tickets_success(self):
        # Test retrieving customer's tickets with valid token
        response = self.client.get('/customers/my-tickets',
            headers={'Authorization': f'Bearer {self.customer_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
    
    def test_get_my_tickets_no_tickets(self):
        # Test retrieving tickets when customer has none
        # Delete the ticket
        db.session.delete(self.sample_ticket)
        db.session.commit()
        
        response = self.client.get('/customers/my-tickets',
            headers={'Authorization': f'Bearer {self.customer_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue('message' in data or isinstance(data, list))
    
    def test_get_my_tickets_no_token(self):
        # Test accessing tickets without authentication token
        response = self.client.get('/customers/my-tickets')
        
        self.assertEqual(response.status_code, 401)
    
    def test_get_my_tickets_invalid_token(self):
        # Test accessing tickets with invalid token
        response = self.client.get('/customers/my-tickets',
            headers={'Authorization': 'Bearer invalid_token_here'}
        )
        
        self.assertEqual(response.status_code, 401)


class TestGetProfile(BaseTestCase):
    # Tests for GET /customers/profile
    
    def test_get_profile_success(self):
        # Test retrieving customer profile with valid token
        response = self.client.get('/customers/profile',
            headers={'Authorization': f'Bearer {self.customer_token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['email'], self.sample_customer.email)
        self.assertEqual(data['first_name'], self.sample_customer.first_name)
    
    def test_get_profile_no_token(self):
        # Test accessing profile without authentication token
        response = self.client.get('/customers/profile')
        
        self.assertEqual(response.status_code, 401)
    
    def test_get_profile_invalid_token(self):
        # Test accessing profile with invalid token
        response = self.client.get('/customers/profile',
            headers={'Authorization': 'Bearer invalid_token'}
        )
        
        self.assertEqual(response.status_code, 401)


class TestReadCustomers(BaseTestCase):
    # Tests for GET /customers (paginated list)
    
    def test_read_customers_default_pagination(self):
        # Test retrieving customers with default pagination
        response = self.client.get('/customers')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
    
    def test_read_customers_custom_pagination(self):
        # Test retrieving customers with custom pagination parameters
        response = self.client.get('/customers?page=1&per_page=5')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertLessEqual(len(data), 5)
    
    def test_read_customers_page_out_of_range(self):
        # Test retrieving customers with page number out of range
        response = self.client.get('/customers?page=9999&per_page=10')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)


class TestReadCustomer(BaseTestCase):
    # Tests for GET /customers/<customer_id>
    
    def test_read_customer_success(self):
        # Test retrieving a specific customer by ID
        response = self.client.get(f'/customers/{self.sample_customer.id}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['id'], self.sample_customer.id)
        self.assertEqual(data['email'], self.sample_customer.email)
    
    def test_read_customer_not_found(self):
        # Test retrieving a non-existent customer
        response = self.client.get('/customers/99999')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_read_customer_invalid_id(self):
        # Test retrieving customer with invalid ID format
        response = self.client.get('/customers/invalid')
        
        self.assertEqual(response.status_code, 404)


class TestDeleteCustomer(BaseTestCase):
    # Tests for DELETE /customers/<customer_id>
    
    def test_delete_customer_success(self):
        # Test successfully deleting a customer
        # Create a customer to delete
        customer = Customers(
            first_name="Delete",
            last_name="Me",
            email="delete.me@example.com",
            password=generate_password_hash("password123"),
            phone="555-0000"
        )
        db.session.add(customer)
        db.session.commit()
        customer_id = customer.id
        
        response = self.client.delete(f'/customers/{customer_id}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('Successfully deleted', data['message'])
    
    def test_delete_customer_not_found(self):
        # Test deleting a non-existent customer
        response = self.client.delete('/customers/99999')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_delete_customer_invalid_id(self):
        # Test deleting customer with invalid ID format
        response = self.client.delete('/customers/invalid')
        
        self.assertEqual(response.status_code, 404)


class TestUpdateCustomer(BaseTestCase):
    # Tests for PUT /customers
    
    def test_update_customer_success(self):
        # Test successfully updating customer profile
        response = self.client.put('/customers',
            headers={'Authorization': f'Bearer {self.customer_token}'},
            data=json.dumps({
                'first_name': 'UpdatedJohn',
                'phone': '555-9999'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['first_name'], 'UpdatedJohn')
        self.assertEqual(data['phone'], '555-9999')
    
    def test_update_customer_password(self):
        # Test updating customer password
        response = self.client.put('/customers',
            headers={'Authorization': f'Bearer {self.customer_token}'},
            data=json.dumps({'password': 'newpassword123'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify password was hashed
        updated_customer = db.session.get(Customers, self.sample_customer.id)
        self.assertNotEqual(updated_customer.password, 'newpassword123')
    
    def test_update_customer_no_token(self):
        # Test updating customer without authentication token
        response = self.client.put('/customers',
            data=json.dumps({'first_name': 'UpdatedName'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_update_customer_invalid_token(self):
        # Test updating customer with invalid token
        response = self.client.put('/customers',
            headers={'Authorization': 'Bearer invalid_token'},
            data=json.dumps({'first_name': 'UpdatedName'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_update_customer_invalid_field(self):
        # Test updating with non-existent field
        response = self.client.put('/customers',
            headers={'Authorization': f'Bearer {self.customer_token}'},
            data=json.dumps({'nonexistent_field': 'value'}),
            content_type='application/json'
        )
        
        # Should succeed but ignore invalid field
        self.assertEqual(response.status_code, 200)


class TestSearchCustomerByEmail(BaseTestCase):
    # Tests for GET /customers/search
    
    def test_search_customer_success(self):
        # Test searching for customer by email
        response = self.client.get(f'/customers/search?email={self.sample_customer.email}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['email'].lower(), self.sample_customer.email.lower())
    
    def test_search_customer_case_insensitive(self):
        # Test case-insensitive email search
        response = self.client.get(f'/customers/search?email={self.sample_customer.email.upper()}')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['email'].lower(), self.sample_customer.email.lower())
    
    def test_search_customer_not_found(self):
        # Test searching for non-existent customer email
        response = self.client.get('/customers/search?email=nonexistent@example.com')
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_search_customer_missing_parameter(self):
        # Test search without email parameter
        response = self.client.get('/customers/search')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('required', data['error'].lower())
    
    def test_search_customer_empty_parameter(self):
        # Test search with empty email parameter
        response = self.client.get('/customers/search?email=')
        
        self.assertEqual(response.status_code, 400)

# This allows you to run the test file directly as a script:
# python app/tests/test_customer.py
if __name__ == '__main__':
    unittest.main() # avoids the need to run python -m unittest app/tests/test_customer.py or python -m unittest discover app/tests