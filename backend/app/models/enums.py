import enum


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class UserStatus(str, enum.Enum):
    active = "active"
    withdrawn = "withdrawn"


class Gender(str, enum.Enum):
    M = "M"  # Male
    F = "F"  # Female
    U = "U"  # Unknown / 선택 안 함


class ExerciseType(str, enum.Enum):
    static = "static"
    dynamic = "dynamic"


class SessionStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    aborted = "aborted"


class FeedbackSeverity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class FeedbackSource(str, enum.Enum):
    rule = "rule"
    llm = "llm"
