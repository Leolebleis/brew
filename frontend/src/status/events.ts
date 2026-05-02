// Backend domain event names — must match src/brew/events/domain.py
export const StatusEvent = {
  BrewCompleted: "BrewCompleted",
  BagActivated: "BagActivated",
  BagFinished: "BagFinished",
  WaterRefilled: "WaterRefilled",
  JournalEntryCreated: "JournalEntryCreated",
} as const;

export type StatusEventName = (typeof StatusEvent)[keyof typeof StatusEvent];
