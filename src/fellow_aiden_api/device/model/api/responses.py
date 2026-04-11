from pydantic import BaseModel


class DeviceAPIResponse(BaseModel):
    brewer_id: str
    display_name: str
    firmware_version: str
