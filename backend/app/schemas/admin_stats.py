from datetime import date

from app.schemas.base import CamelModel


class StatsOverview(CamelModel):
    total_users: int
    active_users: int
    suspended_users: int
    withdrawn_users: int
    total_sessions: int
    avg_score: float | None


class TimeseriesPoint(CamelModel):
    date: date
    signups: int
    sessions: int


class StatsTimeseries(CamelModel):
    points: list[TimeseriesPoint]
