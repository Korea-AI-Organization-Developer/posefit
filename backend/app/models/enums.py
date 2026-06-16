import enum


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class UserStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"  # 관리자에 의한 정지 (로그인·이용 차단)
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


# ─── 관리자(운영) 도메인 ──────────────────────────────────────────────────────
class AdminRole(str, enum.Enum):
    super_admin = "super_admin"  # 관리자 계정·감사 로그 관리 권한
    admin = "admin"


class AdminStatus(str, enum.Enum):
    active = "active"
    disabled = "disabled"


class LlmProvider(str, enum.Enum):
    google = "google"
    openai = "openai"
    anthropic = "anthropic"
