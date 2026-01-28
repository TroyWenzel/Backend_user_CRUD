from app.extensions import ma
from app.models import Inventory, Parts
from marshmallow import fields, validate

class InventorySchema(ma.SQLAlchemyAutoSchema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=250))
    price = fields.Float(required=True)
    
    class Meta:
        model = Inventory
        load_instance = True

class PartsSchema(ma.SQLAlchemyAutoSchema):
    desc_id = fields.Int(required=True, allow_none=False)
    ticket_id = fields.Int(required=False, allow_none=True)
    
    class Meta:
        model = Parts
        load_instance = True
        include_fk = True

# Schema instances
inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)

part_schema = PartsSchema()
parts_schema = PartsSchema(many=True)