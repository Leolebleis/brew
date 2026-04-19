from dataclasses import asdict

from brew.journal.model.api.responses import JournalEntryAPIResponse
from brew.journal.model.entry import JournalEntry


class JournalMapper:
    @staticmethod
    def to_api_response(entry: JournalEntry) -> JournalEntryAPIResponse:
        return JournalEntryAPIResponse.model_validate(asdict(entry))
