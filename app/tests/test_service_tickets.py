from datetime import date
from app import create_app
from app.models import db, Mechanics, ServiceTickets, Parts, Customers, Inventory
import unittest
from werkzeug.security import generate_password_hash
from app.util.auth import encode_token


class TestServiceTickets(unittest.TestCase):
    
    def setUp(self):
        # Set up test client and database
        self.app = create_app('TestingConfig')
        
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            
            # Create test customer
            self.customer = Customers(
                first_name="John",
                last_name="Doe",
                email="customer@email.com",
                password=generate_password_hash('password'),
                phone="555-1234"
            )
            db.session.add(self.customer)
            
            # Create test mechanics
            self.mechanic1 = Mechanics(
                first_name="Test", 
                last_name="Mechanic", 
                email="mechanic1@email.com", 
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
            db.session.add(self.mechanic1)
            db.session.add(self.mechanic2)
            db.session.commit()
            
            # Create test service ticket
            self.ticket = ServiceTickets(
                customer_id=self.customer.id,
                service_desc="Oil change and tire rotation",
                VIN="1HGBH41JXMN109186",
                service_date=date.today(),
                price=150.00
            )
            db.session.add(self.ticket)
            db.session.commit()
            
            # Assign mechanic1 to the ticket
            self.ticket.mechanics.append(self.mechanic1)
            
            # Create inventory item for parts
            self.inventory = Inventory(
                name="Oil Filter",
                price=15.99
            )
            db.session.add(self.inventory)
            db.session.commit()
            
            # Create test part
            self.part = Parts(
                desc_id=self.inventory.id,
                ticket_id=None
            )
            db.session.add(self.part)
            db.session.commit()
            
        self.token_mechanic1 = encode_token(1, role="mechanic")
        self.token_mechanic2 = encode_token(2, role="mechanic")
        self.client = self.app.test_client()
    
    # ===== CREATE SERVICE TICKET TESTS =====
    # Test creating a new service ticket with authentication
    def test_create_service_ticket(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        ticket_payload = {
            "customer_id": 1,
            "service_desc": "Brake inspection and replacement",
            "VIN": "1HGBH41JXMN109187",
            "service_date": str(date.today()),
            "price": 250.00
        }
        
        response = self.client.post('/tickets', headers=headers, json=ticket_payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['service_desc'], "Brake inspection and replacement")
        self.assertEqual(response.json['VIN'], "1HGBH41JXMN109187")
    
    # Negative test: Create ticket without authentication
    def test_create_service_ticket_unauthorized(self):
        ticket_payload = {
            "customer_id": 1,
            "service_desc": "Brake inspection",
            "VIN": "1HGBH41JXMN109187",
            "service_date": str(date.today()),
            "price": 250.00
        }
        
        response = self.client.post('/tickets', json=ticket_payload)
        self.assertEqual(response.status_code, 401)
    
    # Negative test: Create ticket with missing required fields
    def test_create_service_ticket_missing_fields(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        ticket_payload = {
            "customer_id": 1,
            "service_desc": "Brake inspection"
        }
        
        response = self.client.post('/tickets', headers=headers, json=ticket_payload)
        self.assertEqual(response.status_code, 400)
    
    # ===== READ ALL SERVICE TICKETS TESTS =====
    # Test getting all service tickets with authentication
    def test_read_service_tickets(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        response = self.client.get('/tickets', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json) > 0)
    
    # Test getting paginated service tickets
    def test_read_service_tickets_paginated(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        # Create additional tickets for pagination
        with self.app.app_context():
            for i in range(10):
                ticket = ServiceTickets(
                    customer_id=1,
                    service_desc=f"Service {i}",
                    VIN=f"1HGBH41JXMN10918{i % 10}",
                    service_date=date.today(),
                    price=100.00
                )
                db.session.add(ticket)
            db.session.commit()
        
        response = self.client.get('/tickets?page=1&per_page=5', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(response.json), 5)
    
    # Negative test: Get tickets without authentication
    def test_read_service_tickets_unauthorized(self):
        response = self.client.get('/tickets')
        self.assertEqual(response.status_code, 401)
    
    # ===== READ INDIVIDUAL SERVICE TICKET TESTS =====
    # Test getting a specific service ticket
    def test_read_service_ticket(self):
        response = self.client.get('/tickets/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['service_desc'], "Oil change and tire rotation")
        self.assertEqual(response.json['VIN'], "1HGBH41JXMN109186")
    
    # Negative test: Get non-existent ticket
    def test_read_service_ticket_not_found(self):
        response = self.client.get('/tickets/9999')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Service ticket not found')
    
    # Negative test: Get ticket with invalid ID format
    def test_read_service_ticket_invalid_id(self):
        response = self.client.get('/tickets/invalid')
        self.assertEqual(response.status_code, 404)
    
    # ===== UPDATE SERVICE TICKET TESTS =====
    # Test updating a service ticket by assigned mechanic
    def test_update_service_ticket(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        update_payload = {
            "service_desc": "Updated service description",
            "price": 175.00
        }
        
        response = self.client.put('/tickets/1', headers=headers, json=update_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['service_desc'], "Updated service description")
        self.assertEqual(response.json['price'], 175.00)
    
    # Negative test: Update ticket by mechanic not assigned to it
    def test_update_service_ticket_unauthorized_mechanic(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic2}
        update_payload = {
            "service_desc": "Updated description"
        }
        
        response = self.client.put('/tickets/1', headers=headers, json=update_payload)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json['error'], 'Unauthorized to update this ticket')
    
    # Negative test: Update non-existent ticket
    def test_update_service_ticket_not_found(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        update_payload = {
            "service_desc": "Updated description"
        }
        
        response = self.client.put('/tickets/9999', headers=headers, json=update_payload)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Service ticket not found')
    
    # Negative test: Update ticket without authentication
    def test_update_service_ticket_no_auth(self):
        update_payload = {
            "service_desc": "Updated description"
        }
        
        response = self.client.put('/tickets/1', json=update_payload)
        self.assertEqual(response.status_code, 401)
    
    # ===== DELETE SERVICE TICKET TESTS =====
    # Test deleting a service ticket by assigned mechanic
    def test_delete_service_ticket(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        response = self.client.delete('/tickets/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Service ticket 1 deleted')
        
        # Verify ticket is deleted
        with self.app.app_context():
            deleted_ticket = db.session.get(ServiceTickets, 1)
            self.assertIsNone(deleted_ticket)
    
    # Negative test: Delete ticket by mechanic not assigned to it
    def test_delete_service_ticket_unauthorized_mechanic(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic2}
        
        response = self.client.delete('/tickets/1', headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json['error'], 'Unauthorized to delete this ticket')
    
    # Negative test: Delete non-existent ticket
    def test_delete_service_ticket_not_found(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        response = self.client.delete('/tickets/9999', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Service ticket not found')
    
    # Negative test: Delete ticket without authentication
    def test_delete_service_ticket_no_auth(self):
        response = self.client.delete('/tickets/1')
        self.assertEqual(response.status_code, 401)
    
    # ===== ASSIGN MECHANIC TO TICKET TESTS =====
    # Test assigning a mechanic to a ticket
    def test_assign_mechanic_to_ticket(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        response = self.client.post('/tickets/1/mechanics/2', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Mechanic Second Mechanic assigned to ticket 1', response.json['message'])
    
    # Negative test: Assign mechanic already assigned to ticket
    def test_assign_mechanic_already_assigned(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        response = self.client.post('/tickets/1/mechanics/1', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'Mechanic already assigned to this ticket')
    
    # Negative test: Assign mechanic to non-existent ticket
    def test_assign_mechanic_ticket_not_found(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        response = self.client.post('/tickets/9999/mechanics/1', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Service ticket not found')
    
    # Negative test: Assign non-existent mechanic to ticket
    def test_assign_mechanic_not_found(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        response = self.client.post('/tickets/1/mechanics/9999', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Mechanic not found')
    
    # Negative test: Assign mechanic without authentication
    def test_assign_mechanic_no_auth(self):
        response = self.client.post('/tickets/1/mechanics/2')
        self.assertEqual(response.status_code, 401)
    
    # ===== REMOVE MECHANIC FROM TICKET TESTS =====
    # Test removing a mechanic from a ticket
    def test_remove_mechanic_from_ticket(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        response = self.client.delete('/tickets/1/mechanics/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Mechanic Test Mechanic removed from ticket 1', response.json['message'])
    
    # Negative test: Remove mechanic not assigned to ticket
    def test_remove_mechanic_not_assigned(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        response = self.client.delete('/tickets/1/mechanics/2', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'Mechanic not assigned to this ticket')
    
    # Negative test: Remove mechanic from non-existent ticket
    def test_remove_mechanic_ticket_not_found(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        response = self.client.delete('/tickets/9999/mechanics/1', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Service ticket not found')
    
    # Negative test: Remove non-existent mechanic from ticket
    def test_remove_mechanic_not_found(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        response = self.client.delete('/tickets/1/mechanics/9999', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Mechanic not found')
    
    # Negative test: Remove mechanic without authentication
    def test_remove_mechanic_no_auth(self):
        response = self.client.delete('/tickets/1/mechanics/1')
        self.assertEqual(response.status_code, 401)
    
    # ===== ADD PART TO TICKET TESTS =====
    # Test adding a part to a service ticket
    def test_add_part_to_ticket(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        response = self.client.post('/tickets/1/parts/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Part 1 successfully added to ticket 1', response.json['message'])
        self.assertEqual(response.json['part_id'], 1)
        self.assertEqual(response.json['ticket_id'], 1)
    
    # Negative test: Add part already assigned to another ticket
    def test_add_part_already_assigned(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        # First assign the part to ticket 1
        self.client.post('/tickets/1/parts/1', headers=headers)
        
        # Create a second ticket
        with self.app.app_context():
            ticket2 = ServiceTickets(
                customer_id=1,
                service_desc="Engine repair",
                VIN="1HGBH41JXMN109189",
                service_date=date.today(),
                price=500.00
            )
            db.session.add(ticket2)
            db.session.commit()
            
            # Assign mechanic1 to ticket2
            ticket2.mechanics.append(self.mechanic1)
            db.session.commit()
        
        # Try to assign the same part to ticket 2
        response = self.client.post('/tickets/2/parts/1', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Part already assigned to ticket', response.json['error'])
    
    # Negative test: Add part to non-existent ticket
    def test_add_part_ticket_not_found(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        response = self.client.post('/tickets/9999/parts/1', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Service ticket not found')
    
    # Negative test: Add non-existent part to ticket
    def test_add_part_not_found(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        response = self.client.post('/tickets/1/parts/9999', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Part not found')
    
    # Negative test: Add part without authentication
    def test_add_part_no_auth(self):
        response = self.client.post('/tickets/1/parts/1')
        self.assertEqual(response.status_code, 401)
    
    # ===== REMOVE PART FROM TICKET TESTS =====
    # Test removing a part from a service ticket
    def test_remove_part_from_ticket(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        # First assign the part to the ticket
        self.client.post('/tickets/1/parts/1', headers=headers)
        
        # Then remove it
        response = self.client.delete('/tickets/1/parts/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Part 1 removed from ticket 1')
        
        # Verify part is no longer assigned
        with self.app.app_context():
            part = db.session.get(Parts, 1)
            self.assertIsNone(part.ticket_id)
    
    # Negative test: Remove part not assigned to ticket
    def test_remove_part_not_assigned(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        response = self.client.delete('/tickets/1/parts/1', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['error'], 'Part not assigned to this ticket')
    
    # Negative test: Remove part from non-existent ticket
    def test_remove_part_ticket_not_found(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        response = self.client.delete('/tickets/9999/parts/1', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Service ticket not found')
    
    # Negative test: Remove non-existent part from ticket
    def test_remove_part_not_found(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        response = self.client.delete('/tickets/1/parts/9999', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Part not found')
    
    # Negative test: Remove part without authentication
    def test_remove_part_no_auth(self):
        response = self.client.delete('/tickets/1/parts/1')
        self.assertEqual(response.status_code, 401)
    
    # ===== GET ALL PARTS FOR A TICKET TESTS =====
    # Test getting all parts for a ticket
    def test_get_ticket_parts(self):
        headers = {"Authorization": "Bearer " + self.token_mechanic1}
        
        # First assign a part to the ticket
        self.client.post('/tickets/1/parts/1', headers=headers)
        
        # Then get all parts for the ticket
        response = self.client.get('/tickets/1/parts')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json) > 0)
    
    # Test getting parts for a ticket with no parts
    def test_get_ticket_parts_empty(self):
        response = self.client.get('/tickets/1/parts')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 0)
    
    # Negative test: Get parts for non-existent ticket 
    def test_get_ticket_parts_not_found(self):
        response = self.client.get('/tickets/9999/parts')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Service ticket not found')


if __name__ == '__main__':
    unittest.main()