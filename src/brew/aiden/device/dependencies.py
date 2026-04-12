from brew.aiden.device.service import DeviceService


def get_device_service() -> DeviceService:
    msg = "Must be overridden — wired in app lifespan"
    raise NotImplementedError(msg)
