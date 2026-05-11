from pydantic import BaseModel, ConfigDict
from pydantic import field_serializer
from datetime import date

class Sale(BaseModel):
    sale_date: date
    product_id: str
    quantity: int
    total_value: float

    @field_serializer('sale_date')
    def serialize_date(self, value):
        return value.isoformat()

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )