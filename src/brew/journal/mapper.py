from brew.journal.model.api.responses import JournalEntryAPIResponse
from brew.journal.model.entry import JournalEntry


class JournalMapper:
    @staticmethod
    def to_api_response(entry: JournalEntry) -> JournalEntryAPIResponse:
        return JournalEntryAPIResponse(
            id=entry.id,
            brew_started_at=entry.brew_started_at,
            brew_ended_at=entry.brew_ended_at,
            bag_id=entry.bag_id,
            profile_id=entry.profile_id,
            profile_snapshot_at_brew=entry.profile_snapshot_at_brew,
            water_ml=entry.water_ml,
            dose_grams=entry.dose_grams,
            rating=entry.rating,
            note_text=entry.note_text,
            created_at=entry.created_at,
        )
