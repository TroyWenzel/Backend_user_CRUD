from app.extensions import ma
from app.models import ServiceTickets
from marshmallow import fields, validate


class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    customer_id = fields.Int(required=True)
    service_desc = fields.Str(required=True, validate=validate.Length(min=1, max=1000))
    VIN = fields.Str(required=True, validate=validate.Length(min=17, max=17))
    service_date = fields.Date(required=True)
    price = fields.Float(required=True)
    
    class Meta:
        model = ServiceTickets
        load_instance = True
        include_fk = True
        exclude = ('mechanics',)  # Exclude the relationship to avoid serialization issues


service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)