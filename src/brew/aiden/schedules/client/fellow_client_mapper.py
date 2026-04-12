from typing import Any

from brew.aiden.schedules.model.schedule import Schedule, ScheduleCreate, ScheduleUpdate


class FellowScheduleMapper:
    @staticmethod
    def to_entity(data: dict[str, Any]) -> Schedule:
        return Schedule(
            id=data["id"],
            days=data["days"],
            second_from_start_of_day=data["secondFromStartOfTheDay"],
            enabled=data["enabled"],
            amount_of_water=data["amountOfWater"],
            profile_id=data["profileId"],
        )

    @staticmethod
    def from_create(create: ScheduleCreate) -> dict[str, Any]:
        return {
            "days": create.days,
            "secondFromStartOfTheDay": create.second_from_start_of_day,
            "enabled": create.enabled,
            "amountOfWater": create.amount_of_water,
            "profileId": create.profile_id,
        }

    @staticmethod
    def from_update(update: ScheduleUpdate) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if update.days is not None:
            data["days"] = update.days
        if update.second_from_start_of_day is not None:
            data["secondFromStartOfTheDay"] = update.second_from_start_of_day
        if update.enabled is not None:
            data["enabled"] = update.enabled
        if update.amount_of_water is not None:
            data["amountOfWater"] = update.amount_of_water
        if update.profile_id is not None:
            data["profileId"] = update.profile_id
        return data
