from pydantic import BaseModel


class DeviceSettingsAPIRequest(BaseModel):
    setting: str
    value: str | int | float | bool
