from brew.bags.service import BagService


def get_bag_service() -> BagService:
    msg = "Must be overridden — wired in app lifespan"
    raise NotImplementedError(msg)
