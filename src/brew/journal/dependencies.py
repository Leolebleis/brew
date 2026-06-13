from brew.journal.palate import PalateQuery
from brew.journal.service import JournalService


def get_journal_service() -> JournalService:
    msg = "Must be overridden — wired in app lifespan"
    raise NotImplementedError(msg)


def get_palate_query() -> PalateQuery:
    msg = "Must be overridden — wired in app lifespan"
    raise NotImplementedError(msg)
