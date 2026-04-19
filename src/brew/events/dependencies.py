from brew.events.broadcaster import EventBroadcaster


def get_event_broadcaster() -> EventBroadcaster:
    msg = "Must be overridden — wired in app lifespan"
    raise NotImplementedError(msg)
