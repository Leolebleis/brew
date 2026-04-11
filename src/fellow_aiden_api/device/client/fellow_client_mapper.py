from typing import Any

from fellow_aiden_api.device.model.device import Device


class FellowDeviceMapper:
    @staticmethod
    def to_entity(data: dict[str, Any]) -> Device:
        return Device(
            brewer_id=data["id"],
            display_name=data["displayName"],
            firmware_version=data["firmwareVersion"],
        )
