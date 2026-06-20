from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

from sqlalchemy import TypeDecorator, text
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column


class _UTCDateTime(TypeDecorator):
    """MySQL DATETIME(naive) → Python datetime(UTC-aware) 자동 변환.

    MySQL DATETIME은 timezone을 저장하지 않아 aiomysql이 naive datetime을 반환한다.
    Pydantic이 naive datetime을 직렬화하면 'Z' 없는 ISO 문자열이 되고,
    브라우저 new Date()가 로컬 시간(KST)으로 해석해 UTC→KST 변환이 누락된다.
    """

    impl = DATETIME
    cache_ok = True

    def __init__(self, fsp: int = 0, **kw):
        super().__init__(fsp=fsp, **kw)

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone(timedelta(hours=9)))
        return value


class TimestampMixin:
    """erd.sql의 created_at / updated_at (DATETIME(6)) 컬럼을 공통 제공."""

    created_at: Mapped[datetime] = mapped_column(
        _UTCDateTime(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6)"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        _UTCDateTime(fsp=6),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)"),
    )
