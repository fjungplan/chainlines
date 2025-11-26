import enum

class EventType(enum.Enum):
    LEGAL_TRANSFER = "LEGAL_TRANSFER"
    SPIRITUAL_SUCCESSION = "SPIRITUAL_SUCCESSION"
    MERGE = "MERGE"
    SPLIT = "SPLIT"

    @property
    def description(self):
        return {
            EventType.LEGAL_TRANSFER: "Legal transfer of team rights or license.",
            EventType.SPIRITUAL_SUCCESSION: "Spiritual or informal succession.",
            EventType.MERGE: "Merger of two or more teams.",
            EventType.SPLIT: "Split of a team into multiple entities.",
        }[self]
