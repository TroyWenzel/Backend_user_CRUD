from datetime import date
from app import create_app
from app.models import Mechanics, ServiceTickets, db
import unittest
from werkzeug.security import check_password_hash, generate_password_hash
from app.util.auth import encode_token


class TestMechanics(unittest.TestCase):
    
    # Runs before each test_method
    def setUp(self):
        self.app = create_app('TestingConfig')
        self.mechanic = Mechanics(
            first_name="Test", 
            last_name="Mechanic", 
            email="mechanic@email.com", 
            password=generate_password_hash('password'),
            address="123 Test St",
            salary=50000.00
        )
        
        self.mechanic2 = Mechanics(
            first_name="Second",
            last_name="Mechanic",
            email="mechanic2@email.com",
            password=generate_password_hash('password'),
            address="456 Test Ave",
            salary=55000.00
        )
        
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            db.session.add(self.mechanic)
            db.session.add(self.mechanic2)
            db.session.commit()
            
        self.token = encode_token(1, role="mechanic")
        self.client = self.app.test_client()
    
    # ===== LOGIN TESTS =====
    # Test successful login with valid credentials
    def test_login(self):
        login_creds = {
            "email": "mechanic@email.com",
            "password": "password"
        }
        response = self.client.post("/mechanics/login", json=login_creds)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], "Welcome back, Test!")
        self.assertIn("token", response.json)
    
    # Negative test: Login with incorrect password
    def test_login_invalid_credentials(self):
        login_creds = {
            "email": "mechanic@email.com",
            "password": "wrongpassword"
        }
        response = self.client.post("/mechanics/login", json=login_creds)
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)
        self.assertEqual(response.json['error'], "Invalid credentials")
    
    # Negative test: Login with email that doesn't exist
    def test_login_nonexistent_user(self):
        login_creds = {
            "email": "nonexistent@email.com",
            "password": "password"
        }
        response = self.client.post("/mechanics/login", json=login_creds)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json['error'], "Invalid credentials")
    
    # Negative test: Login with missing required fields
    def test_login_missing_fields(self):
        login_creds = {
            "email": "mechanic@email.com"
        }
        response = self.client.post("/mechanics/login", json=login_creds)
        self.assertEqual(response.status_code, 400)
    
    # ===== CREATE MECHANIC TESTS =====
    # Test creating a new mechanic
    def test_create_mechanic(self):
        mechanic_payload = {
            "first_name": "New",
            "last_name": "Mechanic",
            "email": "newmechanic@email.com",
            "password": "password123",
            "address": "789 New St",
            "salary": 60000.00
        }
        
        response = self.client.post('/mechanics', json=mechanic_payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['first_name'], "New")
        self.assertEqual(response.json['last_name'], "Mechanic")
        self.assertEqual(response.json['email'], "newmechanic@email.com")
    
    # Negative test: Create mechanic without required email
    def test_create_mechanic_missing_email(self):
        mechanic_payload = {
            "first_name": "New",
            "last_name": "Mechanic",
            "password": "password123",
            "salary": 60000.00
        }
        
        response = self.client.post('/mechanics', json=mechanic_payload)
        self.assertIn(response.status_code, [400, 500])
    
    # Negative test: Create mechanic with duplicate email
    def test_create_mechanic_duplicate_email(self):
        mechanic_payload = {
            "first_name": "Duplicate",
            "last_name": "Mechanic",
            "email": "mechanic@email.com",
            "password": "password123",
            "address": "123 Dup St",
            "salary": 60000.00
        }
        
        response = self.client.post('/mechanics', json=mechanic_payload)
        self.assertIn(response.status_code, [400, 500])
    
    # ===== READ ALL MECHANICS TESTS =====
    # Test getting all mechanics
    def test_read_mechanics(self):
        response = self.client.get('/mechanics')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 2)
        self.assertEqual(response.json[0]['email'], "mechanic@email.com")
    
    # Negative test: Get mechanics when database is empty
    def test_read_mechanics_empty(self):
        with self.app.app_context():
            db.session.query(Mechanics).delete()
            db.session.commit()
        
        response = self.client.get('/mechanics')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 0)
    
    # ===== GET MY TICKETS TESTS =====
    # Test getting authenticated mechanic's tickets
    def test_get_my_tickets(self):
        headers = {"Authorization": "Bearer " + self.token}
        
        response = self.client.get('/mechanics/my-tickets', headers=headers)
        self.assertEqual(response.status_code, 200)
        # Initially should be empty list or message
        self.assertTrue(isinstance(response.json, list) or 'message' in response.json)
    
    # Negative test: Get tickets without authentication
    def test_get_my_tickets_unauthorized(self):
        response = self.client.get('/mechanics/my-tickets')
        self.assertEqual(response.status_code, 401)
    
    # Negative test: Get tickets with invalid token
    def test_get_my_tickets_invalid_token(self):
        headers = {"Authorization": "Bearer invalidtoken123"}
        
        response = self.client.get('/mechanics/my-tickets', headers=headers)
        self.assertEqual(response.status_code, 401)
    
    # ===== GET PROFILE TESTS =====
    # Test getting authenticated mechanic's profile
    def test_get_profile(self):
        headers = {"Authorization": "Bearer " + self.token}
        
        response = self.client.get('/mechanics/profile', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['email'], "mechanic@email.com")
        self.assertEqual(response.json['first_name'], "Test")
        self.assertEqual(response.json['last_name'], "Mechanic")
    
    # Negative test: Get profile without authentication
    def test_get_profile_unauthorized(self):
        response = self.client.get('/mechanics/profile')
        self.assertEqual(response.status_code, 401)
    
    # Negative test: Get profile with invalid token
    def test_get_profile_invalid_token(self):
        headers = {"Authorization": "Bearer invalidtoken123"}
        
        response = self.client.get('/mechanics/profile', headers=headers)
        self.assertEqual(response.status_code, 401)
    
    # ===== UPDATE MECHANIC TESTS =====
    # Test updating authenticated mechanic's information
    def test_update_mechanic(self):
        headers = {"Authorization": "Bearer " + self.token}
        
        update_payload = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@email.com"
        }
        
        response = self.client.put('/mechanics', headers=headers, json=update_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['first_name'], "Updated")
        self.assertEqual(response.json['last_name'], "Name")
        self.assertEqual(response.json['email'], "updated@email.com")
    
    # Test updating mechanic's password (should be hashed)
    def test_update_mechanic_password(self):
        headers = {"Authorization": "Bearer " + self.token}
        
        update_payload = {
            "password": "newpassword123"
        }
        
        response = self.client.put('/mechanics', headers=headers, json=update_payload)
        self.assertEqual(response.status_code, 200)
        
        # Verify password was hashed
        with self.app.app_context():
            updated_mechanic = db.session.get(Mechanics, 1)
            self.assertTrue(check_password_hash(updated_mechanic.password, 'newpassword123'))
    
    # Negative test: Update mechanic without authentication
    def test_update_mechanic_unauthorized(self):
        update_payload = {
            "first_name": "Updated"
        }
        
        response = self.client.put('/mechanics', json=update_payload)
        self.assertEqual(response.status_code, 401)
    
    # Negative test: Update mechanic with invalid token
    def test_update_mechanic_invalid_token(self):
        headers = {"Authorization": "Bearer invalidtoken123"}
        update_payload = {
            "first_name": "Updated"
        }
        
        response = self.client.put('/mechanics', headers=headers, json=update_payload)
        self.assertEqual(response.status_code, 401)
    
    # ===== DELETE MECHANIC TESTS =====
    # Test deleting authenticated mechanic
    def test_delete_mechanic(self):
        headers = {"Authorization": "Bearer " + self.token}
        
        response = self.client.delete('/mechanics', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Mechanic deleted')
        
        # Verify mechanic is actually deleted
        with self.app.app_context():
            deleted_mechanic = db.session.get(Mechanics, 1)
            self.assertIsNone(deleted_mechanic)
    
    # Negative test: Delete mechanic without authentication
    def test_delete_mechanic_unauthorized(self):
        response = self.client.delete('/mechanics')
        self.assertEqual(response.status_code, 401)
    
    # Negative test: Delete mechanic with invalid token
    def test_delete_mechanic_invalid_token(self):
        headers = {"Authorization": "Bearer invalidtoken123"}
        
        response = self.client.delete('/mechanics', headers=headers)
        self.assertEqual(response.status_code, 401)
    
    # ===== GET TOP MECHANICS TESTS =====
    # Test getting top mechanics who have tickets assigned
    def test_get_top_mechanics_with_tickets(self):
        with self.app.app_context():
            # Create test tickets
            ticket1 = ServiceTickets(
                customer_id=1,
                service_desc="Oil change",
                VIN="1HGBH41JXMN109186",
                service_date=date.today(),
                price=50.00
            )
            ticket2 = ServiceTickets(
                customer_id=1,
                service_desc="Brake repair",
                VIN="1HGBH41JXMN109187",
                service_date=date.today(),
                price=150.00
            )
            ticket3 = ServiceTickets(
                customer_id=1,
                service_desc="Transmission",
                VIN="1HGBH41JXMN109188",
                service_date=date.today(),
                price=500.00
            )
            
            db.session.add_all([ticket1, ticket2, ticket3])
            db.session.commit()
            
            # Assign tickets to mechanics
            mechanic1 = db.session.get(Mechanics, 1)
            mechanic2 = db.session.get(Mechanics, 2)
            
            mechanic1.service_tickets.append(ticket1)
            mechanic1.service_tickets.append(ticket2)
            mechanic2.service_tickets.append(ticket3)
            
            db.session.commit()
        
        response = self.client.get('/mechanics/top-mechanics')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json) > 0)
        self.assertEqual(response.json[0]['ticket_count'], 2)
        self.assertIn('first_name', response.json[0])
        self.assertIn('last_name', response.json[0])
        self.assertIn('email', response.json[0])
    
    # Negative test: Get top mechanics when no tickets exist
    def test_get_top_mechanics_no_tickets(self):
        response = self.client.get('/mechanics/top-mechanics')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'No mechanics found with tickets')
    
    # Test that top mechanics returns max 5 results
    def test_get_top_mechanics_limit(self):
        with self.app.app_context():
            # Create 6 mechanics with varying ticket counts
            for i in range(3, 9):
                mechanic = Mechanics(
                    first_name=f"Mechanic{i}",
                    last_name=f"Last{i}",
                    email=f"mechanic{i}@email.com",
                    password=generate_password_hash('password'),
                    address=f"{i*100} Test St",
                    salary=50000.00
                )
                db.session.add(mechanic)
            db.session.commit()
            
            # Create tickets and assign them
            for i in range(1, 15):
                ticket = ServiceTickets(
                    customer_id=1,
                    service_desc=f"Service {i}",
                    VIN=f"1HGBH41JXMN10918{i % 10}",
                    service_date=date.today(),
                    price=100.00
                )
                db.session.add(ticket)
                db.session.commit()
                
                # Assign tickets to different mechanics
                mechanic = db.session.get(Mechanics, (i % 7) + 1)
                mechanic.service_tickets.append(ticket)
            
            db.session.commit()
        
        response = self.client.get('/mechanics/top-mechanics')
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.json), 5)


if __name__ == '__main__':
    unittest.main()