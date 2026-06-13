from datetime import UTC, datetime

from brew.journal.model.entry import JournalEntry, TastingAxes


def test_entry_defaults_for_new_fields() -> None:
    entry = JournalEntry(
        id="e1",
        brew_started_at=datetime(2026, 6, 13, 7, 0, tzinfo=UTC),
        brew_ended_at=datetime(2026, 6, 13, 7, 7, tzinfo=UTC),
        bag_id="b1",
        profile_id="p1",
        profile_snapshot_at_brew={},
        water_ml=450,
        dose_grams=27,
        rating=None,
        note_text=None,
        created_at=datetime(2026, 6, 13, 7, 7, tzinfo=UTC),
    )
    assert entry.acidity is None
    assert entry.flavor_tags == []
    assert entry.bean_dimensions_snapshot is None


def test_tasting_axes_holds_five_signed_axes() -> None:
    axes = TastingAxes(acidity=2, bitterness=0, body=-1, sweetness=1, strength=0)
    assert (axes.acidity, axes.bitterness, axes.body, axes.sweetness, axes.strength) == (2, 0, -1, 1, 0)
