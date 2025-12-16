import enum

class UserRole(str, enum.Enum):
    EDITOR = "EDITOR"
    TRUSTED_EDITOR = "TRUSTED_EDITOR"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"

class EditAction(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

class EditStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    APPLIED = "APPLIED"

class LineageEventType(str, enum.Enum):
    LEGAL_TRANSFER = "LEGAL_TRANSFER"
    SPIRITUAL_SUCCESSION = "SPIRITUAL_SUCCESSION"
    MERGE = "MERGE"
    SPLIT = "SPLIT"
