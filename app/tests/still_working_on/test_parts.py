from datetime import date
from app import create_app
from app.models import db, Mechanics, Parts, Inventory, ServiceTickets, Customers
import unittest
from werkzeug.security import generate_password_hash
from app.util.auth import encode_token


class TestParts(unittest.TestCase):
    
    def setUp(self):
        # Set up test client and database
        self.app = create_app('TestingConfig')
        
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            
            # Create test mechanic for authentication
            self.mechanic = Mechanics(
                first_name="Test", 
                last_name="Mechanic", 
                email="mechanic@email.com", 
                password=generate_password_hash('password'),
                address="123 Test St",
                salary=50000.00
            )
            db.session.add(self.mechanic)
            
            # Create test customer (required for ServiceTickets)
            self.customer = Customers(
                first_name="John",
                last_name="Doe",
                email="customer@email.com",
                password=generate_password_hash('password'),
                phone="555-1234"
            )
            db.session.add(self.customer)
            db.session.commit()
            
            # Create test inventory item
            self.inventory = Inventory(
                name="Engine Oil",
                price=25.99
            )
            db.session.add(self.inventory)
            db.session.commit()
            
            # Create test part
            self.part = Parts(
                desc_id=self.inventory.id,
                ticket_id=None
            )
            db.session.add(self.part)
            
            # Create test service ticket
            self.ticket = ServiceTickets(
                customer_id=self.customer.id,
                service_desc="Oil change",
                VIN="1HGBH41JXMN109186",
                service_date=date.today(),
                price=150.00
            )
            db.session.add(self.ticket)
            db.session.commit()
            
        self.token = encode_token(1, role="mechanic")
        self.client = self.app.test_client()
    
    # ============== INVENTORY TESTS ==============
    
    # ===== CREATE INVENTORY TESTS =====
    # Test creating a new inventory item with authentication
    def test_create_inventory(self):
        headers = {"Authorization": "Bearer " + self.token}
        inventory_payload = {
            "name": "Brake Fluid",
            "price": 18.99
        }
        
        response = self.client.post('/parts/inventory', headers=headers, json=inventory_payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['name'], "Brake Fluid")
        self.assertEqual(response.json['price'], 18.99)
    
    # Negative test: Create inventory without authentication
    def test_create_inventory_unauthorized(self):
        inventory_payload = {
            "name": "Brake Fluid",
            "price": 18.99
        }
        
        response = self.client.post('/parts/inventory', json=inventory_payload)
        self.assertEqual(response.status_code, 401)
    
    # Negative test: Create inventory with missing required fields
    def test_create_inventory_missing_fields(self):
        headers = {"Authorization": "Bearer " + self.token}
        inventory_payload = {
            "name": "Brake Fluid"
        }
        
        response = self.client.post('/parts/inventory', headers=headers, json=inventory_payload)
        self.assertEqual(response.status_code, 400)
    
    # ===== READ ALL INVENTORY TESTS =====
    # Test getting all inventory items
    def test_read_inventory(self):
        response = self.client.get('/parts/inventory')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json) > 0)
        self.assertEqual(response.json[0]['name'], "Engine Oil")
    
    # Test getting inventory when database is empty
    def test_read_inventory_empty(self):
        with self.app.app_context():
            db.session.query(Inventory).delete()
            db.session.commit()
        
        response = self.client.get('/parts/inventory')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 0)
    
    # Test getting multiple inventory items
    def test_read_inventory_multiple_items(self):
        headers = {"Authorization": "Bearer " + self.token}
        
        # Create additional inventory items
        for i in range(3):
            inventory_payload = {
                "name": f"Item {i}",
                "price": 5.99 + i
            }
            self.client.post('/parts/inventory', headers=headers, json=inventory_payload)
        
        response = self.client.get('/parts/inventory')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json), 4)
    
    # ===== READ SINGLE INVENTORY ITEM TESTS =====
    # Test getting a specific inventory item
    def test_read_inventory_item(self):
        response = self.client.get('/parts/inventory/1')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['name'], "Engine Oil")
        self.assertEqual(response.json['price'], 25.99)
    
    # Negative test: Get non-existent inventory item
    def test_read_inventory_item_not_found(self):
        response = self.client.get('/parts/inventory/9999')
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Inventory item not found')
    
    # Negative test: Get inventory item with invalid ID format
    def test_read_inventory_item_invalid_id(self):
        response = self.client.get('/parts/inventory/invalid')
        self.assertEqual(response.status_code, 404)
    
    # ===== UPDATE INVENTORY ITEM TESTS =====
    # Test updating an inventory item
    def test_update_inventory(self):
        headers = {"Authorization": "Bearer " + self.token}
        update_payload = {
            "name": "Updated Engine Oil",
            "price": 30.99
        }
        
        response = self.client.put('/parts/inventory/1', headers=headers, json=update_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['name'], "Updated Engine Oil")
        self.assertEqual(response.json['price'], 30.99)
    
    # Negative test: Update inventory without authentication
    def test_update_inventory_unauthorized(self):
        update_payload = {
            "name": "Updated Engine Oil"
        }
        
        response = self.client.put('/parts/inventory/1', json=update_payload)
        self.assertEqual(response.status_code, 401)
    
    # Negative test: Update non-existent inventory item
    def test_update_inventory_not_found(self):
        headers = {"Authorization": "Bearer " + self.token}
        update_payload = {
            "name": "Updated Oil"
        }
        
        response = self.client.put('/parts/inventory/9999', headers=headers, json=update_payload)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Inventory item not found')
    
    # Negative test: Update inventory with invalid token
    def test_update_inventory_invalid_token(self):
        headers = {"Authorization": "Bearer invalidtoken123"}
        update_payload = {
            "name": "Updated Oil"
        }
        
        response = self.client.put('/parts/inventory/1', headers=headers, json=update_payload)
        self.assertEqual(response.status_code, 401)
    
    # ===== DELETE INVENTORY ITEM TESTS =====
    # Test deleting an inventory item
    def test_delete_inventory(self):
        headers = {"Authorization": "Bearer " + self.token}
        
        response = self.client.delete('/parts/inventory/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Inventory item 1 deleted')
        
        # Verify deletion
        with self.app.app_context():
            deleted_item = db.session.get(Inventory, 1)
            self.assertIsNone(deleted_item)
    
    # Negative test: Delete inventory without authentication
    def test_delete_inventory_unauthorized(self):
        response = self.client.delete('/parts/inventory/1')
        self.assertEqual(response.status_code, 401)
    
    # Negative test: Delete non-existent inventory item
    def test_delete_inventory_not_found(self):
        headers = {"Authorization": "Bearer " + self.token}
        
        response = self.client.delete('/parts/inventory/9999', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Inventory item not found')
    
    # Negative test: Delete inventory with invalid token
    def test_delete_inventory_invalid_token(self):
        headers = {"Authorization": "Bearer invalidtoken123"}
        
        response = self.client.delete('/parts/inventory/1', headers=headers)
        self.assertEqual(response.status_code, 401)
    
    # ============== PARTS TESTS ==============
    
    # ===== CREATE PART TESTS =====
    # Test creating a new part with authentication
    def test_create_part(self):
        headers = {"Authorization": "Bearer " + self.token}
        part_payload = {
            "desc_id": 1,
            "ticket_id": None
        }
        
        response = self.client.post('/parts', headers=headers, json=part_payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['desc_id'], 1)
        self.assertIsNone(response.json['ticket_id'])
    
    # Negative test: Create part without authentication
    def test_create_part_unauthorized(self):
        part_payload = {
            "desc_id": 1,
            "ticket_id": None
        }
        
        response = self.client.post('/parts', json=part_payload)
        self.assertEqual(response.status_code, 401)
    
    # Negative test: Create part with missing required fields
    def test_create_part_missing_fields(self):
        headers = {"Authorization": "Bearer " + self.token}
        part_payload = {
            "ticket_id": None
        }
        
        response = self.client.post('/parts', headers=headers, json=part_payload)
        self.assertEqual(response.status_code, 400)
    
    # Negative test: Create part with invalid token
    def test_create_part_invalid_token(self):
        headers = {"Authorization": "Bearer invalidtoken123"}
        part_payload = {
            "desc_id": 1,
            "ticket_id": None
        }
        
        response = self.client.post('/parts', headers=headers, json=part_payload)
        self.assertEqual(response.status_code, 401)
    
    # ===== READ ALL PARTS TESTS =====
    # Test getting all parts
    def test_read_parts(self):
        response = self.client.get('/parts')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json) > 0)
        self.assertEqual(response.json[0]['desc_id'], 1)
    
    # Test getting parts when database is empty
    def test_read_parts_empty(self):
        with self.app.app_context():
            db.session.query(Parts).delete()
            db.session.commit()
        
        response = self.client.get('/parts')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 0)
    
    # Test getting multiple parts
    def test_read_parts_multiple(self):
        headers = {"Authorization": "Bearer " + self.token}
        
        # Create additional parts
        for i in range(5):
            part_payload = {
                "desc_id": 1,
                "ticket_id": None
            }
            self.client.post('/parts', headers=headers, json=part_payload)
        
        response = self.client.get('/parts')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json), 6)
    
    # ===== READ SINGLE PART TESTS =====
    # Test getting a specific part
    def test_read_part(self):
        response = self.client.get('/parts/1')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['desc_id'], 1)
        self.assertIsNone(response.json['ticket_id'])
    
    # Negative test: Get non-existent part
    def test_read_part_not_found(self):
        response = self.client.get('/parts/9999')
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Part not found')
    
    # Negative test: Get part with invalid ID format
    def test_read_part_invalid_id(self):
        response = self.client.get('/parts/invalid')
        self.assertEqual(response.status_code, 404)
    
    # ===== UPDATE PART TESTS =====
    # Test updating a part
    def test_update_part(self):
        headers = {"Authorization": "Bearer " + self.token}
        update_payload = {
            "ticket_id": 1
        }
        
        response = self.client.put('/parts/1', headers=headers, json=update_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['ticket_id'], 1)
    
    # Negative test: Update part without authentication
    def test_update_part_unauthorized(self):
        update_payload = {
            "ticket_id": 1
        }
        
        response = self.client.put('/parts/1', json=update_payload)
        self.assertEqual(response.status_code, 401)
    
    # Negative test: Update non-existent part
    def test_update_part_not_found(self):
        headers = {"Authorization": "Bearer " + self.token}
        update_payload = {
            "ticket_id": 1
        }
        
        response = self.client.put('/parts/9999', headers=headers, json=update_payload)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Part not found')
    
    # Negative test: Update part with invalid token
    def test_update_part_invalid_token(self):
        headers = {"Authorization": "Bearer invalidtoken123"}
        update_payload = {
            "ticket_id": 1
        }
        
        response = self.client.put('/parts/1', headers=headers, json=update_payload)
        self.assertEqual(response.status_code, 401)
    
    # ===== DELETE PART TESTS =====
    # Test deleting a part
    def test_delete_part(self):
        headers = {"Authorization": "Bearer " + self.token}
        
        response = self.client.delete('/parts/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Part 1 deleted')
        
        # Verify deletion
        with self.app.app_context():
            deleted_part = db.session.get(Parts, 1)
            self.assertIsNone(deleted_part)
    
    # Negative test: Delete part without authentication
    def test_delete_part_unauthorized(self):
        response = self.client.delete('/parts/1')
        self.assertEqual(response.status_code, 401)
    
    # Negative test: Delete non-existent part
    def test_delete_part_not_found(self):
        headers = {"Authorization": "Bearer " + self.token}
        
        response = self.client.delete('/parts/9999', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['error'], 'Part not found')
    
    # Negative test: Delete part with invalid token
    def test_delete_part_invalid_token(self):
        headers = {"Authorization": "Bearer invalidtoken123"}
        
        response = self.client.delete('/parts/1', headers=headers)
        self.assertEqual(response.status_code, 401)
    
    # ===== GET AVAILABLE PARTS TESTS =====
    # Test getting parts not assigned to any ticket
    def test_get_available_parts(self):
        response = self.client.get('/parts/available')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json) > 0)
        self.assertEqual(response.json[0]['desc_id'], 1)
        self.assertIsNone(response.json[0]['ticket_id'])
    
    # Test getting available parts when all are assigned
    def test_get_available_parts_none_available(self):
        # Assign all parts to tickets
        with self.app.app_context():
            part = db.session.get(Parts, 1)
            part.ticket_id = 1
            db.session.commit()
        
        response = self.client.get('/parts/available')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 0)
    
    # Test getting available parts when some are assigned
    def test_get_available_parts_mixed(self):
        headers = {"Authorization": "Bearer " + self.token}
        
        # Create additional parts
        for i in range(2):
            part_payload = {
                "desc_id": 1,
                "ticket_id": None
            }
            self.client.post('/parts', headers=headers, json=part_payload)
        
        # Assign one part to a ticket
        with self.app.app_context():
            part = db.session.get(Parts, 2)
            part.ticket_id = 1
            db.session.commit()
        
        response = self.client.get('/parts/available')
        self.assertEqual(response.status_code, 200)
        # Should have 2 available parts (part 1 and part 3)
        self.assertEqual(len(response.json), 2)
        
        # Verify none have ticket_id
        for part in response.json:
            self.assertIsNone(part['ticket_id'])
    
    # Test getting available parts when no parts exist
    def test_get_available_parts_empty_database(self):
        with self.app.app_context():
            db.session.query(Parts).delete()
            db.session.commit()
        
        response = self.client.get('/parts/available')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 0)


if __name__ == '__main__':
    unittest.main()