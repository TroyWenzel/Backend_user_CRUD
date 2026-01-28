from app.extensions import ma
from app.models import Customers
from marshmallow import fields, validate, ValidationError, validates_schema

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    # Override fields to add proper validation
    email = fields.Email(required=True, validate=validate.Email(error="Invalid email format"))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=250))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=250))
    phone = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    password = fields.Str(required=True, load_only=True)  # load_only means it won't be in output
    address = fields.Str(required=False, allow_none=True)
    
    class Meta:
        model = Customers
        load_instance = True
        # Don't exclude password here - load_only handles it
        
    @validates_schema
    def validate_duplicate_email(self, data, **kwargs):
        # Check for duplicate email when creating new customer
        email = data.get('email')
        if email:
            from app.models import db
            from sqlalchemy import select
            
            # Only check for duplicates if not updating
            # Check if context exists and has 'updating' flag
            is_updating = False
            if hasattr(self, 'context') and self.context:
                is_updating = self.context.get('updating', False)
            
            if not is_updating:
                query = select(Customers).where(Customers.email.ilike(email))
                existing = db.session.execute(query).scalar_one_or_none()
                
                if existing:
                    raise ValidationError({'email': ['Email already exists']})

        
class CustomerLoginSchema(ma.Schema):
    # Schema for customer login - only email and password
    email = fields.Email(required=True, validate=validate.Email(error="Invalid email format"))
    password = fields.Str(required=True, validate=validate.Length(min=1))

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

customer_login_schema = CustomerLoginSchema()