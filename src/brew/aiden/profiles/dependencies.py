from brew.aiden.profiles.service import ProfileService


def get_profile_service() -> ProfileService:
    msg = "Must be overridden — wired in app lifespan"
    raise NotImplementedError(msg)
