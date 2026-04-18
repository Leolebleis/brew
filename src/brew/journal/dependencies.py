from brew.journal.service import JournalService


def get_journal_service() -> JournalService:
    msg = "Must be overridden — wired in app lifespan"
    raise NotImplementedError(msg)
