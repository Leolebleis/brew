from datetime import datetime

from pydantic import BaseModel


class WaterAPIResponse(BaseModel):
    remaining_ml: int
    last_refilled_at: datetime
