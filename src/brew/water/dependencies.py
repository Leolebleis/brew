from brew.water.service import WaterService


def get_water_service() -> WaterService:
    msg = "Must be overridden — wired in app lifespan"
    raise NotImplementedError(msg)
